from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, urljoin
from pathlib import Path
import queue
import time
import random
import re
from markdownify import markdownify as md

from .browser_utils import initialize_driver, cleanup_driver
from .constants import PAGE_LOAD_TIMEOUT_SECONDS, MEMORY_MANAGEMENT_URL_LIMIT
from .types import LogMessage, StatusMessage, ProgressMessage, FileSavedMessage, StatusType


def sanitize_filename(url, filename_cache=None):
    if filename_cache is None:
        filename_cache = {}

    if url in filename_cache:
        return filename_cache[url]

    parsed_url = urlparse(url)
    path_segment = parsed_url.path
    if not path_segment or path_segment.endswith("/"):
        path_segment += "index"
    if path_segment.startswith("/"):
        path_segment = path_segment[1:]

    filename = path_segment.replace("/", "-")
    if not filename:
        filename = "index"

    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename_cache[url] = sanitized
    return sanitized


def _normalize_url(url):
    url_no_fragment = url.split("#")[0]
    if url_no_fragment.endswith("/"):
        url_no_fragment = url_no_fragment[:-1]
    return url_no_fragment


def _url_matches_any_pattern(url, patterns):
    """FIXED: Case-insensitive URL pattern matching for better user experience."""
    parsed_url_path = urlparse(url).path.lower()
    url_lower = url.lower()

    for pattern in patterns:
        pattern_lower = pattern.lower()
        if pattern_lower.startswith(("http://", "https://")):
            if url_lower.startswith(pattern_lower):
                return True
        elif pattern_lower in parsed_url_path:
            return True
    return False


def _process_page(driver, config, current_url, filename_cache=None):
    """Fetches, processes, and saves a single web page."""
    try:
        driver.get(current_url)
        pause_duration = random.uniform(config.min_pause, config.max_pause)
        time.sleep(pause_duration)

        final_url = driver.current_url
        if config.ignore_queries:
            final_url = final_url.split("?")[0]

        if "404" in driver.title or "Not Found" in driver.title:
            return None, f"  -> Skipping (404 Not Found): {final_url}"

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "lxml")

        for tag in soup(["script", "style"]):
            tag.decompose()
        cleaned_html = str(soup)

        filename = sanitize_filename(final_url, filename_cache) + ".md"
        md_content = md(cleaned_html)

        output_path = Path(config.output_dir) / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return (soup, final_url, output_path, filename), None
    except Exception as e:
        return None, f"  -> Error processing {current_url}: {str(e)}"


def _filter_and_queue_links(soup, base_url, config, processed_urls, urls_to_visit, depth, url_cache=None, max_processed_urls=None, log_queue=None):
    """Finds, filters, and queues new links from a parsed page."""
    if url_cache is None:
        url_cache = {}

    start_domain = urlparse(config.start_url).netloc
    links = soup.find_all("a", href=True)

    for link in links:
        if not isinstance(link, Tag):
            continue

        href_attr = link.get("href")
        if not isinstance(href_attr, str) or not href_attr or href_attr.startswith(("mailto:", "javascript:", "#")):
            continue

        abs_link = urljoin(base_url, href_attr)

        if abs_link in url_cache:
            normalized_abs_link, parsed_link_domain = url_cache[abs_link]
        else:
            normalized_abs_link = _normalize_url(abs_link)
            parsed_link_domain = urlparse(abs_link).netloc
            url_cache[abs_link] = (normalized_abs_link, parsed_link_domain)

        if config.stay_on_subdomain and parsed_link_domain != start_domain:
            continue

        if config.exclude_paths and _url_matches_any_pattern(abs_link, config.exclude_paths):
            continue

        if config.include_paths and not _url_matches_any_pattern(abs_link, config.include_paths):
            continue

        if normalized_abs_link not in processed_urls:
            # Issue 12: Capped Set / Pruning for memory management
            if max_processed_urls and len(processed_urls) >= max_processed_urls and max_processed_urls > MEMORY_MANAGEMENT_URL_LIMIT:
                # Prune 50% of the oldest entries when the limit is hit
                urls_to_prune = len(processed_urls) // 2
                processed_urls = set(list(processed_urls)[urls_to_prune:])
                if log_queue:
                    log_queue.put(LogMessage(message=f"  -> Memory management: trimmed processed URLs to {len(processed_urls)}"))

            processed_urls.add(normalized_abs_link)
            urls_to_visit.put((abs_link, depth + 1))


def crawl_website(config, log_queue, cancel_event, shutdown_event):
    """Crawls a website based on provided configuration."""
    driver = initialize_driver(config, log_queue, shutdown_event)
    if not driver:
        error_msg = StatusMessage(status=StatusType.ERROR, message="ERROR: Could not find a compatible web browser or its driver.\nPlease ensure a supported browser (Edge, Chrome, or Firefox) is installed.")
        log_queue.put(error_msg)
        return

    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
    log_queue.put(LogMessage(message="Starting web crawl..."))

    url_cache = {}
    filename_cache = {}

    urls_to_visit = queue.Queue()
    normalized_start_url = _normalize_url(config.start_url)
    urls_to_visit.put((config.start_url, 0))
    processed_urls = {normalized_start_url}
    pages_saved = 0

    max_processed_urls = max(config.max_pages * 10, MEMORY_MANAGEMENT_URL_LIMIT)

    try:
        while not urls_to_visit.empty() and pages_saved < config.max_pages:
            if cancel_event.is_set() or shutdown_event.is_set():
                break

            current_url, depth = urls_to_visit.get()

            if cancel_event.is_set() or shutdown_event.is_set():
                break

            if not shutdown_event.is_set():
                progress_msg = ProgressMessage(value=pages_saved, max_value=config.max_pages)
                log_queue.put(progress_msg)
                log_queue.put(LogMessage(message=f"GET (Depth {depth}): {current_url}"))

            try:
                page_data, error_msg = _process_page(driver, config, current_url, filename_cache)

                if cancel_event.is_set() or shutdown_event.is_set():
                    break

                if error_msg:
                    if not shutdown_event.is_set():
                        log_queue.put(LogMessage(message=error_msg))
                    continue

                if page_data:
                    soup, final_url, output_path, filename = page_data
                    normalized_final_url = _normalize_url(final_url)
                    processed_urls.add(normalized_final_url)

                    pages_saved += 1
                    if not shutdown_event.is_set():
                        file_saved_msg = FileSavedMessage(
                            url=final_url,
                            path=str(output_path),
                            filename=filename,
                            pages_saved=pages_saved,
                            max_pages=config.max_pages,
                            queue_size=urls_to_visit.qsize(),
                        )
                        log_queue.put(file_saved_msg)

                    if depth < config.crawl_depth:
                        _filter_and_queue_links(soup, final_url, config, processed_urls, urls_to_visit, depth, url_cache, max_processed_urls, log_queue)

            except TimeoutException:
                if not shutdown_event.is_set():
                    log_queue.put(LogMessage(message=f"  -> TIMEOUT after {PAGE_LOAD_TIMEOUT_SECONDS}s on: {current_url}"))
            except WebDriverException as e:
                if not shutdown_event.is_set():
                    log_queue.put(LogMessage(message=f"  -> SELENIUM ERROR on {current_url}: {e.msg}"))
            except Exception as e:
                if not shutdown_event.is_set():
                    log_queue.put(LogMessage(message=f"  -> PROCESSING ERROR on {current_url}: {e}"))

    finally:
        if driver:
            cleanup_driver(driver, timeout=10, log_queue=log_queue)

    if not cancel_event.is_set() and not shutdown_event.is_set() and pages_saved >= config.max_pages:
        progress_msg = ProgressMessage(value=pages_saved, max_value=config.max_pages)
        log_queue.put(progress_msg)

    status_key = StatusType.CANCELLED if cancel_event.is_set() else StatusType.SOURCE_COMPLETE
    message = "Process cancelled by user." if cancel_event.is_set() else f"\nWeb scrape finished. Saved {pages_saved} pages."
    if not shutdown_event.is_set():
        log_queue.put(StatusMessage(status=status_key, message=message))

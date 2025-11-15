import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from pathlib import Path
import queue
import time
import random
import re
import threading
import logging
from markdownify import markdownify as md

from .constants import MEMORY_MANAGEMENT_URL_LIMIT, PROCESSED_URLS_MEMORY_FACTOR
from .types import LogMessage, StatusMessage, ProgressMessage, FileSavedMessage, StatusType
from .config import CrawlerConfig


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
    """Case-insensitive URL pattern matching."""
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


def _process_page(session, config, current_url, filename_cache=None):
    """Fetches, processes, and saves a single web page using requests."""
    try:
        headers = {"User-Agent": config.user_agent}
        response = session.get(current_url, headers=headers, timeout=10)

        if response.status_code == 404:
            return None, f"  -> Skipping (404 Not Found): {current_url}"

        if response.status_code != 200:
            return None, f"  -> Skipping (Status {response.status_code}): {current_url}"

        # Pause for politeness
        pause_duration = random.uniform(config.min_pause, config.max_pause)
        time.sleep(pause_duration)

        # Check content type
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type:
            return None, f"  -> Skipping non-HTML content ({content_type}): {current_url}"

        final_url = response.url
        if config.ignore_queries:
            final_url = final_url.split("?")[0]

        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        # Clean up HTML
        for tag in soup(["script", "style", "nav", "footer", "iframe"]):
            tag.decompose()

        cleaned_html = str(soup)

        filename = sanitize_filename(final_url, filename_cache) + ".md"
        md_content = md(cleaned_html)

        output_path = Path(config.output_dir) / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return (soup, final_url, output_path, filename), None

    except requests.RequestException as e:
        return None, f"  -> Network Error on {current_url}: {str(e)}"
    except Exception as e:
        return None, f"  -> Error processing {current_url}: {str(e)}"


def _filter_and_queue_links(soup, base_url, config, processed_urls, urls_to_visit, depth, url_cache=None, max_processed_urls=None, message_queue=None):
    """Finds, filters, and queues new links from a parsed page."""
    if url_cache is None:
        url_cache = {}

    start_domain = urlparse(config.start_url).netloc
    links = soup.find_all("a", href=True)

    for link in links:
        href_attr = link.get("href")
        if not href_attr or href_attr.startswith(("mailto:", "javascript:", "#", "tel:")):
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
            # Memory management
            if max_processed_urls and len(processed_urls) >= max_processed_urls and max_processed_urls > MEMORY_MANAGEMENT_URL_LIMIT:
                urls_to_prune = len(processed_urls) // 2
                processed_urls = set(list(processed_urls)[urls_to_prune:])
                if message_queue:
                    logging.debug(f"Memory management: trimmed processed URLs to {len(processed_urls)}")

            processed_urls.add(normalized_abs_link)
            urls_to_visit.put((abs_link, depth + 1))


def crawl_website(config: CrawlerConfig, message_queue: queue.Queue, cancel_event: threading.Event):
    """Crawls a website using requests and BeautifulSoup."""
    logging.info("Starting web crawl (Lightweight Mode)...")

    url_cache = {}
    filename_cache = {}
    urls_to_visit = queue.Queue()

    normalized_start_url = _normalize_url(config.start_url)
    urls_to_visit.put((config.start_url, 0))
    processed_urls = {normalized_start_url}
    pages_saved = 0

    max_processed_urls = max(config.max_pages * PROCESSED_URLS_MEMORY_FACTOR, MEMORY_MANAGEMENT_URL_LIMIT)

    # Create a session for connection pooling
    with requests.Session() as session:
        try:
            while not urls_to_visit.empty() and pages_saved < config.max_pages:
                if cancel_event.is_set():
                    break

                current_url, depth = urls_to_visit.get()

                progress_msg = ProgressMessage(value=pages_saved, max_value=config.max_pages)
                message_queue.put(progress_msg)
                logging.info(f"GET (Depth {depth}): {current_url}")

                page_data, error_msg = _process_page(session, config, current_url, filename_cache)

                if cancel_event.is_set():
                    break

                if error_msg:
                    logging.warning(error_msg)
                    continue

                if page_data:
                    soup, final_url, output_path, filename = page_data
                    normalized_final_url = _normalize_url(final_url)
                    processed_urls.add(normalized_final_url)

                    pages_saved += 1
                    file_saved_msg = FileSavedMessage(
                        url=final_url,
                        path=str(output_path),
                        filename=filename,
                        pages_saved=pages_saved,
                        max_pages=config.max_pages,
                        queue_size=urls_to_visit.qsize(),
                    )
                    message_queue.put(file_saved_msg)

                    if depth < config.crawl_depth:
                        _filter_and_queue_links(soup, final_url, config, processed_urls, urls_to_visit, depth, url_cache, max_processed_urls, message_queue)

        except Exception as e:
            logging.critical(f"CRITICAL CRAWLER ERROR: {e}", exc_info=True)

    if not cancel_event.is_set() and pages_saved >= config.max_pages:
        progress_msg = ProgressMessage(value=pages_saved, max_value=config.max_pages)
        message_queue.put(progress_msg)

    status_key = StatusType.CANCELLED if cancel_event.is_set() else StatusType.SOURCE_COMPLETE
    message = "Process cancelled by user." if cancel_event.is_set() else f"\nWeb scrape finished. Saved {pages_saved} pages."
    message_queue.put(StatusMessage(status=status_key, message=message))

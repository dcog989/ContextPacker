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
import fnmatch
from markdownify import markdownify as md


from .types import StatusMessage, ProgressMessage, FileSavedMessage, StatusType
from .config import CrawlerConfig
from .constants import NUM_CRAWL_WORKERS


def sanitize_filename(url, filename_cache=None):
    if filename_cache is None:
        filename_cache = {}

    if url in filename_cache:
        return filename_cache[url]

    parsed_url = urlparse(url)
    path_segment = parsed_url.path
    fragment = parsed_url.fragment

    if not path_segment or path_segment.endswith("/"):
        path_segment += "index"
    if path_segment.startswith("/"):
        path_segment = path_segment[1:]

    filename = path_segment.replace("/", "-")
    if not filename:
        filename = "index"

    # Append fragment to differentiate URLs with anchors from their base
    if fragment:
        filename += f"-{fragment}"

    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Truncate absurdly long filenames (e.g. doxygen anchor names)
    if len(sanitized) > 195:
        sanitized = sanitized[:195].rstrip("-")

    filename_cache[url] = sanitized
    return sanitized


def _normalize_url(url):
    url_no_fragment = url.split("#")[0]
    if url_no_fragment.endswith("/"):
        url_no_fragment = url_no_fragment[:-1]
    return url_no_fragment


def _has_glob_chars(s: str) -> bool:
    return "*" in s or "?" in s or "[" in s


def _url_matches_any_pattern(url, patterns):
    """Case-insensitive URL pattern matching with glob support."""
    parsed_url_path = urlparse(url).path.lower()
    url_lower = url.lower()

    for pattern in patterns:
        pattern_lower = pattern.lower()
        if pattern_lower.startswith(("http://", "https://")):
            if _has_glob_chars(pattern_lower):
                if fnmatch.filter([url_lower], pattern_lower):
                    return True
            elif url_lower.startswith(pattern_lower):
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

        # Check content type before politeness pause to avoid delaying on non-text responses
        content_type = response.headers.get("Content-Type", "").lower()
        is_html = "text/html" in content_type
        is_text = "text/" in content_type or "application/json" in content_type or "application/xml" in content_type

        if not is_text:
            return None, f"  -> Skipping non-text content ({content_type}): {current_url}"

        # Detect common CDN/block pages that return 200 with a challenge page
        if is_html and response.text:
            text_lower = response.text.lower()
            soup_check = BeautifulSoup(response.text, "html.parser")
            title_tag = soup_check.find("title")
            title_text = title_tag.get_text(strip=True).lower() if title_tag else ""

            is_challenge = (
                "just a moment..." in title_text
                or "attention required" in title_text
                or "cf-browser-verification" in text_lower
                or "_cf_chl_opt" in text_lower
            )
            if is_challenge:
                return None, f"  -> Blocked by CDN/security ({current_url})"

            # Very short HTML pages are often error/redirect pages with no real content
            if (
                len(response.text) < 500
                and not response.text.strip().startswith("<!")
                and not response.text.strip().startswith("<html")
            ):
                return None, f"  -> Skipping suspiciously short response ({len(response.text)} bytes): {current_url}"

        # Pause for politeness
        pause_duration = random.uniform(config.min_pause, config.max_pause)
        time.sleep(pause_duration)

        final_url = response.url
        if config.ignore_queries:
            final_url = final_url.split("?")[0]

        sanitized_base_filename = sanitize_filename(final_url, filename_cache)

        soup = None
        output_content = ""
        extension = ".txt"  # A safe default

        if is_html:
            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract links from the page BEFORE cleanup so nav/footer links aren't lost
            all_links_on_page = []
            for a in soup.find_all("a", href=True):
                all_links_on_page.append(a)

            # Clean up HTML before converting to Markdown (strip nav/footer for clean output)
            for tag in soup(["script", "style", "nav", "footer", "iframe"]):
                tag.decompose()
            cleaned_html = str(soup)

            # Re-attach extracted links to root so _filter_and_queue_links can find them
            for a_tag in all_links_on_page:
                soup.append(a_tag)

            output_content = md(cleaned_html)
            extension = ".md"
        else:  # Handle other text-based formats
            output_content = response.text
            # Try to determine a better file extension from the URL or content type
            path_suffix = Path(urlparse(final_url).path).suffix
            if path_suffix and len(path_suffix) < 7:  # e.g., .md, .js, .css, .json
                extension = path_suffix
            elif "markdown" in content_type:
                extension = ".md"
            elif "css" in content_type:
                extension = ".css"
            elif "javascript" in content_type:
                extension = ".js"
            elif "json" in content_type:
                extension = ".json"
            elif "xml" in content_type:
                extension = ".xml"

        filename = sanitized_base_filename + extension
        output_path = Path(config.output_dir) / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_content)

        # We only return a soup object if we parsed HTML, which is where we'll look for more links.
        return (soup, final_url, output_path, filename), None

    except requests.RequestException as e:
        return None, f"  -> Network Error on {current_url}: {str(e)}"
    except Exception as e:
        return None, f"  -> Error processing {current_url}: {str(e)}"


def _filter_and_queue_links(
    soup,
    pages_saved: int,
    base_url: str,
    config: CrawlerConfig,
    processed_urls,
    urls_to_visit,
    depth: int,
    url_cache=None,
    message_queue=None,
    processed_urls_lock=None,
):
    """Finds, filters, and queues new links from a parsed page, respecting the max_pages limit."""
    if soup is None:
        return

    if url_cache is None:
        url_cache = {}

    start_domain = urlparse(config.start_url).netloc
    links = soup.find_all("a", href=True)

    for link in links:
        if pages_saved + urls_to_visit.qsize() >= config.max_pages:
            logging.debug(f"Max pages limit ({config.max_pages}) reached in queue. Halting link discovery.")
            break

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

        if processed_urls_lock:
            with processed_urls_lock:
                if normalized_abs_link not in processed_urls:
                    processed_urls.add(normalized_abs_link)
                    urls_to_visit.put((abs_link, depth + 1))
        else:
            if normalized_abs_link not in processed_urls:
                processed_urls.add(normalized_abs_link)
                urls_to_visit.put((abs_link, depth + 1))


def _discover_js_nav_links(soup, base_url, session, processed_urls, urls_to_visit, depth, processed_urls_lock):
    """Fetch static navigation files referenced by JS-based doc generators (DocFX etc.)."""
    # DocFX: <meta name="docfx:navrel" content="../toc.html">
    nav_meta = soup.find("meta", attrs={"name": "docfx:navrel"})
    if nav_meta:
        toc_url = urljoin(base_url, nav_meta.get("content", ""))
        try:
            resp = session.get(toc_url, timeout=10)
            if resp.status_code == 200:
                toc_soup = BeautifulSoup(resp.text, "html.parser")
                for a in toc_soup.find_all("a", href=True):
                    href = a.get("href")
                    if href.startswith("javascript:") or href.startswith("#"):
                        continue
                    abs_link = urljoin(toc_url, href)
                    normalized = _normalize_url(abs_link)
                    with processed_urls_lock:
                        if normalized not in processed_urls:
                            processed_urls.add(normalized)
                            urls_to_visit.put((abs_link, depth + 1))
        except Exception:
            pass


def crawl_website(config: CrawlerConfig, message_queue: queue.Queue, cancel_event: threading.Event):
    """Crawls a website using multiple parallel worker threads."""
    logging.info("Starting web crawl...")

    urls_to_visit = queue.Queue()
    processed_urls_lock = threading.Lock()
    pages_saved_lock = threading.Lock()
    pages_saved = 0
    stop_event = threading.Event()

    normalized_start_url = _normalize_url(config.start_url)
    urls_to_visit.put((config.start_url, 0))
    with processed_urls_lock:
        processed_urls = {normalized_start_url}

    def worker():
        nonlocal pages_saved
        filename_cache = {}
        url_cache = {}
        with requests.Session() as session:
            while not stop_event.is_set():
                try:
                    current_url, depth = urls_to_visit.get(timeout=1)
                except queue.Empty:
                    continue

                if stop_event.is_set():
                    urls_to_visit.task_done()
                    continue

                with pages_saved_lock:
                    if pages_saved >= config.max_pages:
                        stop_event.set()
                        urls_to_visit.task_done()
                        continue

                page_data, error_msg = _process_page(session, config, current_url, filename_cache)

                if stop_event.is_set():
                    urls_to_visit.task_done()
                    continue

                if error_msg:
                    logging.warning(error_msg)
                    urls_to_visit.task_done()
                    continue

                if page_data:
                    soup, final_url, output_path, filename = page_data

                    with pages_saved_lock:
                        if pages_saved >= config.max_pages:
                            stop_event.set()
                            urls_to_visit.task_done()
                            continue
                        local_pages_saved = pages_saved + 1
                        pages_saved = local_pages_saved

                    normalized_final = _normalize_url(final_url)
                    with processed_urls_lock:
                        processed_urls.add(normalized_final)

                    if depth < config.crawl_depth:
                        _filter_and_queue_links(
                            soup,
                            local_pages_saved,
                            final_url,
                            config,
                            processed_urls,
                            urls_to_visit,
                            depth,
                            url_cache,
                            message_queue,
                            processed_urls_lock,
                        )
                        # Check for JS navigation metadata (DocFX, etc.) and follow TOC links
                        _discover_js_nav_links(
                            soup, final_url, session,
                            processed_urls, urls_to_visit, depth,
                            processed_urls_lock,
                        )

                    message_queue.put(
                        FileSavedMessage(
                            url=final_url,
                            path=str(output_path),
                            filename=filename,
                            pages_saved=local_pages_saved,
                            max_pages=config.max_pages,
                            queue_size=urls_to_visit.qsize(),
                        )
                    )

                urls_to_visit.task_done()

    def wait_for_join():
        urls_to_visit.join()
        stop_event.set()

    def wait_for_cancel():
        cancel_event.wait()
        stop_event.set()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(NUM_CRAWL_WORKERS)]
    for t in threads:
        t.start()

    join_watcher = threading.Thread(target=wait_for_join, daemon=True)
    join_watcher.start()

    cancel_watcher = threading.Thread(target=wait_for_cancel, daemon=True)
    cancel_watcher.start()

    # Block until one of: all work done, max_pages reached, or user cancelled
    stop_event.wait()

    # Drain remaining queue items so join_watcher can return
    while True:
        try:
            urls_to_visit.get(block=False)
            urls_to_visit.task_done()
        except queue.Empty:
            break

    for t in threads:
        t.join(timeout=5)

    with pages_saved_lock:
        final_pages_saved = pages_saved

    if cancel_event.is_set():
        message_queue.put(StatusMessage(status=StatusType.CANCELLED, message="Process cancelled by user."))
    elif final_pages_saved >= config.max_pages:
        message_queue.put(ProgressMessage(value=final_pages_saved, max_value=config.max_pages))
        message_queue.put(
            StatusMessage(
                status=StatusType.SOURCE_COMPLETE,
                message=f"\nWeb scrape finished: Reached 'Max Pages' limit of {config.max_pages}.",
            )
        )
    else:
        message_queue.put(
            StatusMessage(
                status=StatusType.SOURCE_COMPLETE,
                message=f"\nWeb scrape finished: Explored all reachable links within the specified 'Crawl Depth' ({config.crawl_depth}). Saved {final_pages_saved} pages.",
            )
        )

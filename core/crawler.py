from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, urljoin
from pathlib import Path
import queue
import time
import random
import re
from markdownify import markdownify as md
import platform
import subprocess
import traceback

from .platform_utils import get_browser_binary_path


def sanitize_filename(url):
    parsed_url = urlparse(url)
    path_segment = parsed_url.path
    if not path_segment or path_segment.endswith("/"):
        path_segment += "index"
    if path_segment.startswith("/"):
        path_segment = path_segment[1:]

    filename = path_segment.replace("/", "-")
    if not filename:
        filename = "index"

    return re.sub(r'[<>:"/\\|?*]', "_", filename)


def _normalize_url(url):
    url_no_fragment = url.split("#")[0]
    if url_no_fragment.endswith("/"):
        url_no_fragment = url_no_fragment[:-1]
    return url_no_fragment


def _url_matches_any_pattern(url, patterns):
    parsed_url_path = urlparse(url).path
    for pattern in patterns:
        if pattern.startswith(("http://", "https://")):
            if url.startswith(pattern):
                return True
        elif pattern in parsed_url_path:
            return True
    return False


def _initialize_driver(config, log_queue):
    """Initializes and returns a Selenium WebDriver instance."""
    log_queue.put({"type": "log", "message": "Searching for a compatible web browser..."})

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    chrome_options.page_load_strategy = "eager"
    chrome_options.add_argument(f"user-agent={config.user_agent}")
    chrome_binary_path = get_browser_binary_path("chrome")
    if chrome_binary_path:
        chrome_options.binary_location = chrome_binary_path

    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--log-level=3")
    edge_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    edge_options.page_load_strategy = "eager"
    edge_options.add_argument(f"user-agent={config.user_agent}")
    edge_binary_path = get_browser_binary_path("msedge")
    if edge_binary_path:
        edge_options.binary_location = edge_binary_path

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--log-level=3")
    firefox_options.page_load_strategy = "eager"
    firefox_options.add_argument(f"user-agent={config.user_agent}")
    firefox_binary_path = get_browser_binary_path("firefox")
    if firefox_binary_path:
        firefox_options.binary_location = firefox_binary_path

    creation_flags = 0
    if platform.system() == "Windows":
        creation_flags = subprocess.CREATE_NO_WINDOW

    browsers_to_try = [
        ("msedge", webdriver.Edge, edge_options, EdgeService),
        ("chrome", webdriver.Chrome, chrome_options, ChromeService),
        ("firefox", webdriver.Firefox, firefox_options, FirefoxService),
    ]

    for name_key, driver_class, options, service_class in browsers_to_try:
        try:
            log_queue.put({"type": "log", "message": f"  -> Attempting to initialize {name_key}..."})
            service = service_class(creationflags=creation_flags)
            driver = driver_class(service=service, options=options)
            log_queue.put({"type": "log", "message": f"✔ Success: Using {name_key} for web crawling."})
            return driver
        except WebDriverException as e:
            log_queue.put({"type": "log", "message": f"  -> {name_key} not found or failed to start. Details: {e.msg}"})
        except Exception as e:
            tb_str = traceback.format_exc()
            log_queue.put({"type": "log", "message": f"  -> An unexpected error occurred with {name_key}: {e}\n{tb_str}"})
    return None


def _process_page(driver, config, current_url):
    """Fetches, processes, and saves a single web page."""
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

    filename = sanitize_filename(final_url) + ".md"
    md_content = md(cleaned_html)

    output_path = Path(config.output_dir) / filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return (soup, final_url, output_path, filename), None


def _filter_and_queue_links(soup, base_url, config, processed_urls, urls_to_visit, depth):
    """Finds, filters, and queues new links from a parsed page."""
    start_domain = urlparse(config.start_url).netloc
    links = soup.find_all("a", href=True)

    for link in links:
        if not isinstance(link, Tag):
            continue

        href_attr = link.get("href")
        if not isinstance(href_attr, str) or not href_attr or href_attr.startswith(("mailto:", "javascript:", "#")):
            continue

        abs_link = urljoin(base_url, href_attr)
        normalized_abs_link = _normalize_url(abs_link)

        parsed_link_domain = urlparse(abs_link).netloc
        if config.stay_on_subdomain and parsed_link_domain != start_domain:
            continue

        if config.exclude_paths and _url_matches_any_pattern(abs_link, config.exclude_paths):
            continue

        if config.include_paths and not _url_matches_any_pattern(abs_link, config.include_paths):
            continue

        if normalized_abs_link not in processed_urls:
            processed_urls.add(normalized_abs_link)
            urls_to_visit.put((abs_link, depth + 1))


def crawl_website(config, log_queue, cancel_event):
    """
    Crawls a website based on the provided configuration.
    This function orchestrates the crawling process.
    """
    driver = _initialize_driver(config, log_queue)
    if not driver:
        error_msg = "ERROR: Could not find a compatible web browser or its driver.\nPlease ensure a supported browser (Edge, Chrome, or Firefox) is installed."
        log_queue.put({"type": "status", "status": "error", "message": error_msg})
        return

    driver.set_page_load_timeout(15)
    log_queue.put({"type": "log", "message": "Starting web crawl..."})

    urls_to_visit = queue.Queue()
    normalized_start_url = _normalize_url(config.start_url)
    urls_to_visit.put((config.start_url, 0))
    processed_urls = {normalized_start_url}
    pages_saved = 0

    try:
        while not urls_to_visit.empty() and pages_saved < config.max_pages:
            if cancel_event.is_set():
                break

            current_url, depth = urls_to_visit.get()

            # Check for cancellation immediately after getting URL but before processing
            if cancel_event.is_set():
                break

            log_queue.put({"type": "progress", "value": pages_saved, "max_value": config.max_pages})
            log_queue.put({"type": "log", "message": f"GET (Depth {depth}): {current_url}"})

            try:
                page_data, error_msg = _process_page(driver, config, current_url)

                if cancel_event.is_set():
                    break

                if error_msg:
                    log_queue.put({"type": "log", "message": error_msg})
                    continue

                if page_data:
                    soup, final_url, output_path, filename = page_data
                    normalized_final_url = _normalize_url(final_url)
                    processed_urls.add(normalized_final_url)

                    pages_saved += 1
                    log_queue.put(
                        {
                            "type": "file_saved",
                            "url": final_url,
                            "path": str(output_path),
                            "filename": filename,
                            "pages_saved": pages_saved,
                            "max_pages": config.max_pages,
                            "queue_size": urls_to_visit.qsize(),
                        }
                    )

                    if depth < config.crawl_depth:
                        _filter_and_queue_links(soup, final_url, config, processed_urls, urls_to_visit, depth)

            except TimeoutException:
                log_queue.put({"type": "log", "message": f"  -> TIMEOUT after 15s on: {current_url}"})
            except WebDriverException as e:
                log_queue.put({"type": "log", "message": f"  -> SELENIUM ERROR on {current_url}: {e.msg}"})
            except Exception as e:
                log_queue.put({"type": "log", "message": f"  -> PROCESSING ERROR on {current_url}: {e}"})

    finally:
        if driver:
            _cleanup_driver(driver, timeout=10, log_queue=log_queue)

    status_key = "cancelled" if cancel_event.is_set() else "source_complete"
    message = "Process cancelled by user." if cancel_event.is_set() else f"\nWeb scrape finished. Saved {pages_saved} pages."
    log_queue.put({"type": "status", "status": status_key, "message": message})


def _cleanup_driver(driver, timeout=10, log_queue=None):
    """Clean up driver with timeout and error handling."""
    if log_queue:
        log_queue.put({"type": "log", "message": "Cleaning up browser driver..."})

    try:
        # Try graceful quit first
        driver.quit()
        if log_queue:
            log_queue.put({"type": "log", "message": "Browser driver cleaned up successfully."})
    except Exception as e:
        if log_queue:
            log_queue.put({"type": "log", "message": f"Warning during driver cleanup: {e}"})

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
import os
from markdownify import markdownify as md
import platform
import subprocess
import threading
import json


def _get_browser_binary_path_windows(browser_name, log_queue):
    """
    Finds a browser's executable on Windows by checking registry keys
    and common file system locations.
    """
    import winreg

    search_config = {
        "chrome": {
            "reg_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
            ],
            "fs_paths": [r"Google\Chrome\Application\chrome.exe", r"Chromium\Application\chrome.exe"],
        },
        "msedge": {
            "reg_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
            ],
            "fs_paths": [r"Microsoft\Edge\Application\msedge.exe"],
        },
        "firefox": {
            "reg_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"),
            ],
            "fs_paths": [r"Mozilla Firefox\firefox.exe", r"Firefox Developer Edition\firefox.exe"],
        },
    }

    config = search_config.get(browser_name)
    if not config:
        return None

    for hive, subkey in config["reg_keys"]:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                path, _ = winreg.QueryValueEx(key, "")
                if Path(path).exists():
                    return path
        except FileNotFoundError:
            continue
        except Exception:
            continue

    base_paths = []
    for var in ["ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"]:
        path = os.environ.get(var)
        if path:
            base_paths.append(Path(path))
    if not os.environ.get("LOCALAPPDATA"):
        base_paths.append(Path.home() / "AppData" / "Local")

    for fs_path in config["fs_paths"]:
        for base in base_paths:
            full_path = base / fs_path
            if full_path.exists():
                return str(full_path)
    return None


def _get_browser_binary_path(browser_name, log_queue):
    """
    Finds the path to a browser's executable, checking common locations
    for the current operating system.
    """
    system = platform.system()
    if system == "Windows":
        return _get_browser_binary_path_windows(browser_name, log_queue)

    paths_to_check = []
    if system == "Darwin":
        path_map = {
            "chrome": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
            "msedge": ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
            "firefox": ["/Applications/Firefox.app/Contents/MacOS/firefox"],
        }
        paths_to_check = path_map.get(browser_name, [])
    elif system == "Linux":
        path_map = {
            "chrome": ["/usr/bin/google-chrome", "/opt/google/chrome/chrome"],
            "msedge": ["/usr/bin/microsoft-edge"],
            "firefox": ["/usr/bin/firefox"],
        }
        paths_to_check = path_map.get(browser_name, [])

    if paths_to_check:
        for path in paths_to_check:
            if Path(path).exists():
                return path
    return None


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


def crawl_website(config, log_queue, cancel_event):
    """
    Crawls a website based on the provided configuration.
    """

    def _get_driver_path_from_manager(browser_name_key):
        browser_map = {"msedge": "edge", "chrome": "chrome", "firefox": "firefox"}
        browser_arg = browser_map.get(browser_name_key)
        if not browser_arg:
            return None

        manager_path = os.environ.get("SE_MANAGER_PATH")
        if not manager_path or not os.path.isdir(manager_path):
            log_queue.put({"type": "log", "message": f"SE_MANAGER_PATH ('{manager_path}') is not a valid directory."})
            return None

        sm_exe = "selenium-manager.exe" if platform.system() == "Windows" else "selenium-manager"
        sm_exe_path = os.path.join(manager_path, sm_exe)

        if not os.path.exists(sm_exe_path):
            log_queue.put({"type": "log", "message": f"Could not find '{sm_exe}' in SE_MANAGER_PATH: {manager_path}"})
            return None
        try:
            command = [sm_exe_path, "--browser", browser_arg, "--output", "json"]
            process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", shell=False, check=False)

            if process.returncode == 0 and process.stdout:
                result_json = json.loads(process.stdout)
                driver_path = result_json.get("result", {}).get("driver_path")
                if driver_path and os.path.exists(driver_path):
                    log_queue.put({"type": "log", "message": f"  -> Located driver for {browser_arg} at: {driver_path}"})
                    return driver_path
                else:
                    log_queue.put({"type": "log", "message": f"  -> Selenium Manager ran for {browser_arg} but returned an invalid path."})
                    log_queue.put({"type": "log", "message": f"     Output: {process.stdout}"})
            else:
                log_queue.put({"type": "log", "message": f"  -> Selenium Manager failed for {browser_arg}. Return Code: {process.returncode}"})
                log_queue.put({"type": "log", "message": f"     STDERR: {process.stderr}"})

        except Exception as e:
            log_queue.put({"type": "log", "message": f"  -> An exception occurred while running Selenium Manager for {browser_arg}: {e}"})

        return None

    log_queue.put({"type": "log", "message": "Searching for a compatible web browser..."})

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    chrome_options.page_load_strategy = "eager"
    chrome_options.add_argument(f"user-agent={config.user_agent}")
    chrome_binary_path = _get_browser_binary_path("chrome", log_queue)
    if chrome_binary_path:
        chrome_options.binary_location = chrome_binary_path

    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--log-level=3")
    edge_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    edge_options.page_load_strategy = "eager"
    edge_options.add_argument(f"user-agent={config.user_agent}")
    edge_binary_path = _get_browser_binary_path("msedge", log_queue)
    if edge_binary_path:
        edge_options.binary_location = edge_binary_path

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--log-level=3")
    firefox_options.page_load_strategy = "eager"
    firefox_options.add_argument(f"user-agent={config.user_agent}")
    firefox_binary_path = _get_browser_binary_path("firefox", log_queue)
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

    driver = None
    for name_key, driver_class, options, service_class in browsers_to_try:
        try:
            log_queue.put({"type": "log", "message": f"  -> Attempting to initialize {name_key}..."})
            driver_path = _get_driver_path_from_manager(name_key)

            if not driver_path:
                log_queue.put({"type": "log", "message": f"  -> Failed to locate driver for {name_key} via Selenium Manager. Skipping."})
                continue

            service = service_class(executable_path=driver_path, creationflags=creation_flags)
            driver = driver_class(service=service, options=options)
            log_queue.put({"type": "log", "message": f"✔ Success: Using {name_key} for web crawling."})
            break

        except WebDriverException as e:
            log_queue.put({"type": "log", "message": f"  -> {name_key} not found or failed to start. Details: {str(e)}"})

    if driver is None:
        error_msg = "ERROR: Could not find a compatible web browser or its driver.\nPlease ensure a supported browser (Edge, Chrome, or Firefox) is installed."
        log_queue.put({"type": "status", "status": "error", "message": error_msg})
        return

    driver.set_page_load_timeout(15)

    def _normalize_url(url):
        url_no_fragment = url.split("#")[0]
        if url_no_fragment.endswith(".html"):
            url_no_fragment = url_no_fragment[:-5]
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

    log_queue.put({"type": "log", "message": "Starting web crawl..."})

    start_domain = urlparse(config.start_url).netloc

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
            log_queue.put({"type": "progress", "value": pages_saved, "max_value": config.max_pages})

            try:
                log_queue.put({"type": "log", "message": f"GET (Depth {depth}): {current_url}"})
                driver.get(current_url)

                pause_duration = random.uniform(config.min_pause, config.max_pause)
                time.sleep(pause_duration)

                if cancel_event.is_set():
                    break

                final_url_from_driver = driver.current_url
                if config.ignore_queries:
                    final_url_from_driver = final_url_from_driver.split("?")[0]

                normalized_final_url = _normalize_url(final_url_from_driver)

                if "404" in driver.title or "Not Found" in driver.title:
                    log_queue.put({"type": "log", "message": f"  -> Skipping (404 Not Found): {final_url_from_driver}"})
                    continue

                processed_urls.add(normalized_final_url)
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, "lxml")

                for tag in soup(["script", "style"]):
                    tag.decompose()
                cleaned_html = str(soup)

                filename = sanitize_filename(normalized_final_url) + ".md"
                md_content = md(cleaned_html)

                output_path = Path(config.output_dir) / filename
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)

                pages_saved += 1
                log_queue.put(
                    {
                        "type": "file_saved",
                        "url": final_url_from_driver,
                        "path": str(output_path),
                        "filename": filename,
                        "pages_saved": pages_saved,
                        "max_pages": config.max_pages,
                        "queue_size": urls_to_visit.qsize(),
                    }
                )

                if depth < config.crawl_depth:
                    links = soup.find_all("a", href=True)
                    for link in links:
                        if not isinstance(link, Tag):
                            continue

                        href_attr = link.get("href")
                        if not isinstance(href_attr, str):
                            continue

                        if not href_attr or href_attr.startswith(("mailto:", "javascript:", "#")):
                            continue

                        abs_link = urljoin(final_url_from_driver, href_attr)
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

            except TimeoutException:
                log_queue.put({"type": "log", "message": f"  -> TIMEOUT after 5s on: {current_url}"})
                continue
            except WebDriverException as e:
                log_queue.put({"type": "log", "message": f"  -> SELENIUM ERROR: {e.msg}"})
            except Exception as e:
                log_queue.put({"type": "log", "message": f"  -> PROCESSING ERROR: {e}"})

    finally:
        if driver:

            def _cleanup_driver(d):
                try:
                    d.quit()
                except Exception:
                    pass

            cleanup_thread = threading.Thread(target=_cleanup_driver, args=(driver,), daemon=True)
            cleanup_thread.start()

    if not cancel_event.is_set():
        log_queue.put({"type": "status", "status": "source_complete", "message": f"\nWeb scrape finished. Saved {pages_saved} pages."})
    else:
        log_queue.put({"type": "status", "status": "cancelled", "message": "Process cancelled by user."})

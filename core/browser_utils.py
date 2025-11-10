"""
Browser initialization utilities to eliminate code duplication.
Centralizes browser setup logic for Chrome, Edge, and Firefox.
"""

import traceback
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService

from .platform_utils import get_browser_binary_path
from .platform_detection import get_process_creation_flags


def _create_base_options(user_agent):
    """Create base browser options that are common to all browsers."""
    options = webdriver.ChromeOptions()  # Base class for common options
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.page_load_strategy = "eager"
    options.add_argument(f"user-agent={user_agent}")
    return options


def _create_chrome_options(user_agent):
    """Create Chrome-specific options."""
    options = _create_base_options(user_agent)
    chrome_binary_path = get_browser_binary_path("chrome")
    if chrome_binary_path:
        options.binary_location = chrome_binary_path
    return options


def _create_edge_options(user_agent):
    """Create Edge-specific options."""
    options = _create_base_options(user_agent)
    edge_binary_path = get_browser_binary_path("msedge")
    if edge_binary_path:
        options.binary_location = edge_binary_path
    return options


def _create_firefox_options(user_agent):
    """Create Firefox-specific options."""
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    options.page_load_strategy = "eager"
    options.add_argument(f"user-agent={user_agent}")
    firefox_binary_path = get_browser_binary_path("firefox")
    if firefox_binary_path:
        options.binary_location = firefox_binary_path
    return options


def _get_creation_flags():
    """Get appropriate process creation flags for the current platform."""
    return get_process_creation_flags()


def _initialize_browser_driver(browser_name, driver_class, options, service_class, log_queue, shutdown_event):
    """
    Initialize a single browser driver with standardized error handling.

    Args:
        browser_name: Name of the browser for logging
        driver_class: Selenium WebDriver class
        options: Browser options object
        service_class: Selenium Service class
        log_queue: Queue for logging messages
        shutdown_event: Event to check for shutdown

    Returns:
        WebDriver instance or None if initialization failed
    """
    try:
        if not shutdown_event.is_set():
            log_queue.put({"type": "log", "message": f"  -> Attempting to initialize {browser_name}..."})

        creation_flags = _get_creation_flags()
        service = service_class(creationflags=creation_flags)
        driver = driver_class(service=service, options=options)

        if not shutdown_event.is_set():
            log_queue.put({"type": "log", "message": f"✔ Success: Using {browser_name} for web crawling."})

        return driver

    except WebDriverException as e:
        if not shutdown_event.is_set():
            log_queue.put({"type": "log", "message": f"  -> {browser_name} not found or failed to start. Details: {e.msg}"})
    except Exception as e:
        if not shutdown_event.is_set():
            tb_str = traceback.format_exc()
            log_queue.put({"type": "log", "message": f"  -> An unexpected error occurred with {browser_name}: {e}\n{tb_str}"})

    return None


def initialize_driver(config, log_queue, shutdown_event):
    """
    Initializes and returns a Selenium WebDriver instance.
    Tries browsers in order: Edge, Chrome, Firefox.

    Args:
        config: Configuration object containing user_agent
        log_queue: Queue for logging messages
        shutdown_event: Event to check for shutdown

    Returns:
        WebDriver instance or None if no browser could be initialized
    """
    if not shutdown_event.is_set():
        log_queue.put({"type": "log", "message": "Searching for a compatible web browser..."})

    # Define browser configurations in order of preference
    browser_configs = [
        ("msedge", webdriver.Edge, _create_edge_options(config.user_agent), EdgeService),
        ("chrome", webdriver.Chrome, _create_chrome_options(config.user_agent), ChromeService),
        ("firefox", webdriver.Firefox, _create_firefox_options(config.user_agent), FirefoxService),
    ]

    for name_key, driver_class, options, service_class in browser_configs:
        driver = _initialize_browser_driver(name_key, driver_class, options, service_class, log_queue, shutdown_event)
        if driver:
            return driver

    return None


def cleanup_driver(driver, timeout=10, log_queue=None):
    """
    Clean up driver with timeout and standardized error handling.

    Args:
        driver: WebDriver instance to clean up
        timeout: Timeout for cleanup operations
        log_queue: Queue for logging messages (optional)
    """
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

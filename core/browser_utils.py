"""
Browser initialization utilities to eliminate code duplication.
Centralizes browser setup logic for Chrome, Edge, and Firefox.
"""

import traceback
import threading
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService

from .platform_detection import get_process_creation_flags
from .config_manager import get_config
from .types import LogMessage


def _create_base_options(user_agent):
    """Create base browser options that are common to all browsers."""
    options = webdriver.ChromeOptions()  # Base class for common options
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.page_load_strategy = "eager"
    options.add_argument(f"user-agent={user_agent}")
    return options


def _create_chromium_options(user_agent):
    """Create options for Chromium-based browsers (Chrome and Edge)."""
    options = _create_base_options(user_agent)
    return options


def _create_firefox_options(user_agent):
    """Create Firefox-specific options."""
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--log-level=3")
    options.page_load_strategy = "eager"
    options.add_argument(f"user-agent={user_agent}")
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
            log_queue.put(LogMessage(message=f"  -> Attempting to initialize {browser_name}..."))

        creation_flags = _get_creation_flags()
        service = service_class(creationflags=creation_flags)
        driver = driver_class(service=service, options=options)

        if not shutdown_event.is_set():
            log_queue.put(LogMessage(message=f"✔ Success: Using {browser_name} for web crawling."))

        return driver

    except WebDriverException as e:
        if not shutdown_event.is_set():
            log_queue.put(LogMessage(message=f"  -> {browser_name} not found or failed to start. Details: {e.msg}"))
    except Exception as e:
        if not shutdown_event.is_set():
            tb_str = traceback.format_exc()
            log_queue.put(LogMessage(message=f"  -> An unexpected error occurred with {browser_name}: {e}\n{tb_str}"))

    return None


def initialize_driver(config, log_queue, shutdown_event):
    """
    Initializes and returns a Selenium WebDriver instance.
    Tries browsers in order based on 'default_browser' config, then fallbacks.

    Args:
        config: Configuration object containing user_agent
        log_queue: Queue for logging messages
        shutdown_event: Event to check for shutdown

    Returns:
        WebDriver instance or None if no browser could be initialized
    """
    app_config = get_config()
    preferred_browser = app_config.get("default_browser", "msedge")

    if not shutdown_event.is_set():
        log_queue.put(LogMessage(message="Searching for a compatible web browser..."))

    # Define all browser configurations
    browser_configs = [
        ("msedge", webdriver.Edge, _create_chromium_options(config.user_agent), EdgeService),
        ("chrome", webdriver.Chrome, _create_chromium_options(config.user_agent), ChromeService),
        ("firefox", webdriver.Firefox, _create_firefox_options(config.user_agent), FirefoxService),
    ]

    # Reorder configs based on preference
    ordered_configs = []
    preferred_config_tuple = next(((name, driver_class, options, service_class) for name, driver_class, options, service_class in browser_configs if name == preferred_browser), None)

    if preferred_config_tuple:
        ordered_configs.append(preferred_config_tuple)
    ordered_configs.extend(cfg for cfg in browser_configs if cfg[0] != preferred_browser)

    for name_key, driver_class, options, service_class in ordered_configs:
        driver = _initialize_browser_driver(name_key, driver_class, options, service_class, log_queue, shutdown_event)
        if driver:
            return driver

    return None


def cleanup_driver(driver, timeout=10, log_queue=None):
    """
    Clean up driver with actual timeout enforcement to prevent hanging.

    Args:
        driver: WebDriver instance to clean up
        timeout: Timeout in seconds for cleanup operations
        log_queue: Queue for logging messages (optional)
    """
    if log_queue:
        log_queue.put(LogMessage(message="Cleaning up browser driver..."))

    cleanup_complete = threading.Event()
    cleanup_exception = None

    def _quit_driver():
        nonlocal cleanup_exception
        try:
            driver.quit()
        except Exception as e:
            cleanup_exception = e

        cleanup_complete.set()

    # Run driver.quit() in a separate thread to enforce timeout
    cleanup_thread = threading.Thread(target=_quit_driver, daemon=True)
    cleanup_thread.start()

    # Wait for cleanup with timeout
    cleanup_complete.wait(timeout=timeout)

    if cleanup_complete.is_set():
        if cleanup_exception:
            if log_queue:
                log_queue.put(LogMessage(message=f"Warning during driver cleanup: {cleanup_exception}"))
        else:
            if log_queue:
                log_queue.put(LogMessage(message="Browser driver cleaned up successfully."))
    else:
        # Timeout occurred
        if log_queue:
            log_queue.put(LogMessage(message=f"Warning: Driver cleanup timed out after {timeout}s. Thread may still be running."))
        # Note: We can't forcefully kill the thread, but at least we don't hang the main thread

"""
Application constants for ContextPacker.
This module centralizes all magic numbers and configuration values.
"""

# UI Timer Constants (in milliseconds)
BATCH_UPDATE_INTERVAL_MS = 250  # Timer for batch updates to scraped files list
EXCLUDE_UPDATE_INTERVAL_MS = 500  # Debounce timer for exclude text changes
UI_UPDATE_INTERVAL_MS = 1000  # Timer for UI updates (timestamp labels, etc.)

# Crawler Constants
PAGE_LOAD_TIMEOUT_SECONDS = 15  # Selenium page load timeout
MEMORY_MANAGEMENT_URL_LIMIT = 1000  # Minimum processed URLs to keep in memory

# Depth Constants
UNLIMITED_DEPTH_VALUE = 9  # Value that represents "unlimited" depth
UNLIMITED_DEPTH_REPLACEMENT = float("inf")  # What to replace unlimited depth with internally

# Memory Management Constants
MAX_BATCH_SIZE = 500  # Maximum items in scraped_files_batch before forcing UI update
UI_UPDATE_BATCH_SIZE = 50  # Number of files to process before UI update
MAX_LOG_LINES = 1000  # Maximum lines to keep in verbose log

# Directory Scanning Constants
LARGE_DIRECTORY_THRESHOLD = 1000  # Threshold for using heap sort vs regular sort

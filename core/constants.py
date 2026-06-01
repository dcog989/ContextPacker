"""
Application constants for ContextPacker.
This module centralizes all magic numbers and configuration values.
"""

# UI Timer Constants (in milliseconds)
BATCH_UPDATE_INTERVAL_MS = 250  # Timer for batch updates to scraped files list
EXCLUDE_UPDATE_INTERVAL_MS = 500  # Debounce timer for exclude text changes
UI_UPDATE_INTERVAL_MS = 1000  # Timer for UI updates (timestamp labels, etc.)

# UI Component Constants
DEFAULT_WINDOW_WIDTH = 1600
DEFAULT_WINDOW_HEIGHT = 950
UI_TABLE_INSERT_CHUNK_SIZE = 50  # Number of rows to insert into file list tables at a time to keep UI responsive

# Crawler Constants
MEMORY_MANAGEMENT_URL_LIMIT = 1000  # Minimum processed URLs to keep in memory before pruning
PROCESSED_URLS_MEMORY_FACTOR = 10  # Multiplier for max_pages to determine max processed URLs to keep in memory (max_pages * factor)

# Crawler Pause Defaults (in milliseconds)
DEFAULT_MIN_PAUSE_MS = 53
DEFAULT_MAX_PAUSE_MS = 735

# Depth Constants
UNLIMITED_DEPTH_VALUE = 9  # Value that represents "unlimited" depth
UNLIMITED_DEPTH_REPLACEMENT = float("inf")  # What to replace unlimited depth with internally



# Process Management Constants
PROCESS_CLEANUP_TIMEOUT_SECONDS = 2  # Seconds to wait for a graceful process termination
PROCESS_FORCE_KILL_WAIT_SECONDS = 1  # Seconds to wait after a forceful kill command
GIT_CLONE_OUTPUT_POLL_SECONDS = 0.1  # Polling interval for git clone output queue
GIT_READER_THREAD_JOIN_TIMEOUT_SECONDS = 1.0  # Max seconds to wait for git output reader thread to join

# Packaging Constants
REPOMIX_PROGRESS_UPDATE_BATCH_SIZE = 10  # Update progress bar every N files processed by Repomix

# Memory Management Constants
MAX_LOG_LINES = 1000  # Maximum lines to keep in verbose log



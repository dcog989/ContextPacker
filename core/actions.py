import threading
import shutil
from pathlib import Path
from datetime import datetime
import logging
import fnmatch
import queue

from .packager import run_repomix
from .utils import get_app_data_dir, get_downloads_folder
from .error_handling import WorkerErrorHandler, create_process_with_flags, safe_stream_enqueue, validate_tool_availability, create_tool_missing_error
from .constants import UNLIMITED_DEPTH_VALUE, UNLIMITED_DEPTH_REPLACEMENT, LARGE_DIRECTORY_THRESHOLD
from .types import StatusMessage, ProgressMessage, LogMessage, StatusType, FileType, FileInfo, message_to_dict, file_info_to_dict, dict_to_file_info


def _create_session_dir():
    """Creates a new timestamped directory for a session in the app data cache."""
    app_data_path = get_app_data_dir()
    cache_path = app_data_path / "Cache"
    cache_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    session_dir = cache_path / f"session-{timestamp}"
    session_dir.mkdir(exist_ok=True)
    return str(session_dir)


def start_download(app, cancel_event):
    """Initializes the temporary directory and is called before the web crawling process."""
    app.main_panel.clear_logs()
    app.main_panel.progress_gauge.setValue(0)

    if app.temp_dir and Path(app.temp_dir).is_dir():
        shutil.rmtree(app.temp_dir)

    app.temp_dir = _create_session_dir()
    app.log_verbose(f"Created temporary directory: {app.temp_dir}")
    app.log_verbose("Starting url conversion...")

    # The actual crawl_website call is submitted by task_handler.py to the executor.


def start_git_clone(app, url, cancel_event):
    """Initializes the temporary directory for git clone.

    Returns:
        str: The path to the created temporary directory.
    """
    app.main_panel.clear_logs()

    if app.temp_dir and Path(app.temp_dir).is_dir():
        shutil.rmtree(app.temp_dir)

    app.temp_dir = _create_session_dir()
    app.log_verbose(f"Created temporary directory for git clone: {app.temp_dir}")
    app.log_verbose(f"Starting git clone for {url}...")
    return app.temp_dir


def _clone_repo_worker(url, path, log_queue, cancel_event, shutdown_event):
    """Worker function to perform a git clone and stream output."""
    # Validate git availability using centralized utility
    if not validate_tool_availability("git"):
        log_queue.put(create_tool_missing_error("git"))
        return

    # Security: Validate and sanitize git URL
    import re

    # Allow common git URL patterns but prevent command injection
    git_url_pattern = r"^(https?://|git@|ssh://|file://)[a-zA-Z0-9._/-]+(:[0-9]+)?(/.*)?$"
    if not re.match(git_url_pattern, url.strip()):
        error_msg = StatusMessage(status=StatusType.ERROR, message="Invalid or potentially malicious git URL provided.")
        log_queue.put(message_to_dict(error_msg))
        return

    # Security: Validate path to prevent directory traversal
    try:
        resolved_path = Path(path).resolve()
        # Ensure path is within expected temp directory structure
        if not any(parent.name == "Cache" for parent in resolved_path.parents):
            error_msg = StatusMessage(status=StatusType.ERROR, message="Invalid clone path detected.")
            log_queue.put(message_to_dict(error_msg))
            return
    except Exception:
        error_msg = StatusMessage(status=StatusType.ERROR, message="Invalid path provided.")
        log_queue.put(message_to_dict(error_msg))
        return

    # Initialize centralized error handler
    error_handler = WorkerErrorHandler(log_queue, shutdown_event)
    process = None
    output_queue = None
    reader_thread = None

    try:
        # Create process with centralized utility
        process = create_process_with_flags(["git", "clone", "--depth", "1", url, path])

        if not process.stdout:
            process.wait()
            error_msg = StatusMessage(status=StatusType.ERROR, message="Failed to capture git clone output stream.")
            log_queue.put(message_to_dict(error_msg))
            return

        output_queue = queue.Queue()
        reader_thread = threading.Thread(target=safe_stream_enqueue, args=(process.stdout, output_queue, shutdown_event), daemon=True)
        reader_thread.start()

        while process.poll() is None:
            if cancel_event.is_set():
                error_handler.handle_process_cleanup(process)
                cancel_msg = StatusMessage(status=StatusType.CANCELLED, message="Git clone cancelled.")
                log_queue.put(message_to_dict(cancel_msg))
                return

            try:
                line = output_queue.get(timeout=0.1)
                if line and not shutdown_event.is_set():
                    log_msg = LogMessage(message=line.strip())
                    log_queue.put(message_to_dict(log_msg))
            except queue.Empty:
                continue

        while not output_queue.empty():
            line = output_queue.get_nowait()
            if line and not shutdown_event.is_set():
                log_msg = LogMessage(message=line.strip())
                log_queue.put(message_to_dict(log_msg))

        if cancel_event.is_set():
            cancel_msg = StatusMessage(status=StatusType.CANCELLED, message="Git clone cancelled.")
            log_queue.put(message_to_dict(cancel_msg))
            return

        if process.returncode == 0:
            complete_msg = StatusMessage(status=StatusType.CLONE_COMPLETE, message="", path=path)
            log_queue.put(message_to_dict(complete_msg))
        else:
            error_msg = StatusMessage(status=StatusType.ERROR, message="Git clone failed. Check the log for details.")
            log_queue.put(message_to_dict(error_msg))

    except Exception as e:
        error_handler.handle_worker_exception(e, "git clone")
    finally:
        # Ensure proper cleanup of process resources using centralized utilities
        if process is not None:
            # Wait for reader thread to finish processing the stream
            if reader_thread is not None and reader_thread.is_alive():
                reader_thread.join(timeout=1.0)

            # Use centralized process cleanup
            error_handler.handle_process_cleanup(process)

            # Use centralized stream cleanup
            error_handler.handle_stream_cleanup(process)


def start_packaging(app, cancel_event, file_list=None):
    """Initializes and starts the packaging process in a new thread."""
    is_web_mode = app.main_panel.web_crawl_radio.isChecked()
    app.filename_prefix = app.main_panel.output_filename_ctrl.text().strip() or "ContextPacker-package"
    source_dir = ""
    effective_excludes = []

    if is_web_mode:
        if not app.temp_dir or not any(Path(app.temp_dir).iterdir()):
            app.log_verbose("ERROR: No downloaded content to package. Please run 'Download & Convert' first.")
            return
        source_dir = app.temp_dir
        effective_excludes = []
    else:
        source_dir = app.main_panel.local_dir_ctrl.text()
        default_excludes = [p.strip() for p in app.main_panel.local_exclude_ctrl.toPlainText().splitlines() if p.strip()]
        effective_excludes = list(set(default_excludes) | app.local_files_to_exclude | app.local_depth_excludes)

    extension = app.main_panel.output_format_choice.currentText()
    style_map = {".md": "markdown", ".txt": "plain", ".xml": "xml"}
    repomix_style = style_map.get(extension, "markdown")

    app.main_panel.progress_gauge.setValue(0)

    _run_packaging_thread(app, source_dir, app.filename_prefix, effective_excludes, extension, repomix_style, cancel_event, file_list)


def _packaging_worker(source_dir, output_path, log_queue, cancel_event, repomix_style, exclude_patterns, progress_handler):
    """Worker function that wraps run_repomix to handle logging setup/teardown."""
    repomix_logger = logging.getLogger("repomix")
    original_level = repomix_logger.level
    repomix_logger.setLevel(logging.INFO)
    repomix_logger.addHandler(progress_handler)
    try:
        run_repomix(
            source_dir,
            output_path,
            log_queue,
            cancel_event,
            repomix_style=repomix_style,
            exclude_patterns=exclude_patterns,
        )
    finally:
        repomix_logger.removeHandler(progress_handler)
        repomix_logger.setLevel(original_level)


def _run_packaging_thread(app, source_dir, filename_prefix, exclude_paths, extension, repomix_style, cancel_event, file_list=None):
    """Configures and runs the repomix packager in a worker thread."""
    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    downloads_path = get_downloads_folder()
    output_basename = f"{filename_prefix}-{timestamp}{extension}"
    app.final_output_path = str(Path(downloads_path) / output_basename)

    app.log_verbose("\nStarting packaging process...")
    app.log_verbose(f"Output file will be saved to: {app.final_output_path}")

    class RepomixProgressHandler(logging.Handler):
        def __init__(self, log_queue_ref, total_files_ref, shutdown_event_ref):
            super(RepomixProgressHandler, self).__init__()
            self.log_queue = log_queue_ref
            self.processed_count = 0
            self.total_files = total_files_ref
            self.shutdown_event = shutdown_event_ref
            self.batch_size = 10  # Update progress every 10 files
            self.last_progress_value = 0

        def emit(self, record):
            # Don't emit during shutdown to prevent race conditions
            if self.shutdown_event.is_set():
                return

            msg = self.format(record)
            if "Processing file:" in msg:
                self.processed_count += 1
                progress_value = int((self.processed_count / self.total_files) * 100) if self.total_files > 0 else 0

                # Only send progress updates if progress changed significantly or every batch_size files
                if progress_value != self.last_progress_value or self.processed_count % self.batch_size == 0 or self.processed_count == self.total_files:
                    progress_msg = ProgressMessage(value=progress_value, max_value=100)
                    self.log_queue.put(message_to_dict(progress_msg))
                    self.last_progress_value = progress_value

            log_msg = LogMessage(message=msg)
            self.log_queue.put(message_to_dict(log_msg))

    total_files_for_progress = 0
    is_web_mode = app.main_panel.web_crawl_radio.isChecked()
    if file_list is not None:
        if is_web_mode:
            total_files_for_progress = len(file_list)
        else:
            total_files_for_progress = len([f for f in file_list if dict_to_file_info(f).type == FileType.FILE])

    progress_handler = RepomixProgressHandler(app.log_queue, total_files_for_progress, app.shutdown_event)
    progress_handler.setLevel(logging.INFO)

    args = (
        source_dir,
        app.final_output_path,
        app.log_queue,
        cancel_event,
        repomix_style,
        exclude_paths,
        progress_handler,
    )
    app.worker_future = app.executor.submit(_packaging_worker, *args)


def get_local_files(root_dir, max_depth, use_gitignore, custom_excludes, binary_excludes, cancel_event=None, gitignore_cache=None):
    """
    Scans a directory and returns a filtered list of files and folders,
    optimized for performance with depth-aware traversal and efficient pattern matching.
    """
    import heapq

    base_path = Path(root_dir)
    if not base_path.is_dir():
        return [], set()

    if max_depth == UNLIMITED_DEPTH_VALUE:  # Treat specific value as unlimited
        max_depth = UNLIMITED_DEPTH_REPLACEMENT

    # Use heap for efficient sorting of large directories
    files_to_show = []
    depth_excludes = set()

    # Pre-compile patterns for better performance
    compiled_patterns = []
    for pattern in custom_excludes:
        try:
            compiled_patterns.append((pattern, True))  # True for custom pattern
        except Exception:
            continue

    # Optimized gitignore loading with better caching
    def load_ignore_patterns(ignore_file_path, cache_key):
        """Load and cache ignore patterns efficiently."""
        try:
            stat_info = ignore_file_path.stat()
            mtime = stat_info.st_mtime

            # Check cache first
            if gitignore_cache is not None and cache_key in gitignore_cache:
                cached = gitignore_cache[cache_key]
                if cached.get("mtime") == mtime:
                    return cached["patterns"]

            # Load and parse file
            with open(ignore_file_path, "r", encoding="utf-8") as f:
                patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

            # Update cache
            if gitignore_cache is not None:
                gitignore_cache[cache_key] = {"mtime": mtime, "patterns": patterns}

            return patterns
        except Exception:
            # Remove invalid cache entry
            if gitignore_cache is not None and cache_key in gitignore_cache:
                del gitignore_cache[cache_key]
            return []

    # Load root-level ignore patterns once
    ignore_files_to_check = [".repomixignore"]
    if use_gitignore:
        ignore_files_to_check.append(".gitignore")

    root_patterns = []
    for filename in ignore_files_to_check:
        ignore_file_path = base_path / filename
        if ignore_file_path.is_file():
            patterns = load_ignore_patterns(ignore_file_path, str(ignore_file_path))
            root_patterns.extend(patterns)

    # Add binary excludes to compiled patterns
    for pattern in binary_excludes:
        try:
            compiled_patterns.append((pattern, True))
        except Exception:
            continue

    # Add root ignore patterns to compiled patterns
    for pattern in root_patterns:
        try:
            compiled_patterns.append((pattern, True))
        except Exception:
            continue

    # Optimized directory traversal with depth awareness
    def should_ignore_path(rel_path, is_dir=False):
        """Check if a path should be ignored using compiled patterns."""
        path_str = rel_path.as_posix()
        if is_dir:
            path_str = path_str.rstrip("/") + "/"

        for pattern, _ in compiled_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
        return False

    # Use iterative approach for better control and early termination
    def scan_directory_iterative(start_path, max_depth_limit):
        """Iteratively scan directory with depth control and early termination."""
        # Use deque for better performance with large directories
        from collections import deque

        queue = deque([(start_path, Path("."), 0)])

        # Performance counters for monitoring
        processed_dirs = 0
        processed_files = 0
        max_items_per_batch = 1000  # Process in batches to prevent memory spikes

        while queue:
            if cancel_event and cancel_event.is_set():
                return

            # Process in batches to control memory usage
            batch_size = min(len(queue), max_items_per_batch)
            for _ in range(batch_size):
                current_path, rel_path, current_depth = queue.popleft()
                processed_dirs += 1

                # Process directory contents with better error handling
                try:
                    entries = list(current_path.iterdir())
                except (OSError, PermissionError) as e:
                    # Log permission errors but continue scanning
                    if not cancel_event or not cancel_event.is_set():
                        print(f"Warning: Cannot access {current_path}: {e}")
                    continue
                except Exception as e:
                    # Handle unexpected errors gracefully
                    if not cancel_event or not cancel_event.is_set():
                        print(f"Error scanning {current_path}: {e}")
                    continue

                # Separate files and directories for optimized processing
                dirs = []
                files = []

                for entry in entries:
                    try:
                        entry_rel_path = rel_path / entry.name

                        # Skip if ignored
                        if should_ignore_path(entry_rel_path, entry.is_dir()):
                            continue

                        if entry.is_dir():
                            dirs.append((entry, entry_rel_path))
                        else:
                            files.append((entry, entry_rel_path))
                    except Exception:
                        # Skip problematic entries but continue processing
                        continue

                # Process files at current level first (before depth check)
                for file_entry, file_rel_path in files:
                    try:
                        stat_info = file_entry.stat()
                        size = stat_info.st_size
                        size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
                        rel_path_str = file_rel_path.as_posix()

                        file_info = FileInfo(name=rel_path_str, type=FileType.FILE, size=size, size_str=size_str, rel_path=rel_path_str)
                        files_to_show.append(file_info_to_dict(file_info))
                        processed_files += 1
                    except (OSError, ValueError):
                        # Skip files that can't be accessed
                        continue

                # Check depth limit for adding subdirectories to queue
                if current_depth >= max_depth_limit:
                    # Add to depth excludes if we hit the limit
                    if current_path.is_dir():
                        depth_excludes.add(rel_path.as_posix() + "/")
                    continue

                # Add directories to queue (depth-first for better memory locality)
                for dir_entry, dir_rel_path in dirs:
                    queue.appendleft((dir_entry, dir_rel_path, current_depth + 1))

                    # Add directory to results
                    rel_path_str = dir_rel_path.as_posix()
                    folder_info = FileInfo(name=rel_path_str + "/", type=FileType.FOLDER, size=0, size_str="", rel_path=rel_path_str + "/")
                    files_to_show.append(file_info_to_dict(folder_info))

            # Periodic cancellation check and progress feedback
            if cancel_event and cancel_event.is_set():
                return

            # Optional: Add progress logging for very large scans
            if processed_dirs % 1000 == 0 and processed_dirs > 0:
                print(f"Scanned {processed_dirs} directories, {processed_files} files...")

    # Start the scan
    scan_directory_iterative(base_path, max_depth)

    # Check for cancellation before sorting
    if cancel_event and cancel_event.is_set():
        return [], set()

    # Efficient sorting using heap for large datasets
    if len(files_to_show) > LARGE_DIRECTORY_THRESHOLD:  # Use heap for large directories
        # Create separate heaps for folders and files
        folders = []
        files = []

        for item in files_to_show:
            if item["type"] == "Folder":
                heapq.heappush(folders, (item["name"].lower(), item))
            else:
                heapq.heappush(files, (item["name"].lower(), item))

        # Extract sorted items
        sorted_folders = [heapq.heappop(folders)[1] for _ in range(len(folders))]
        sorted_files = [heapq.heappop(files)[1] for _ in range(len(files))]

        files_to_show = sorted_folders + sorted_files
    else:
        # Use regular sort for smaller datasets
        files_to_show.sort(key=lambda p: (p["type"] != "Folder", p["name"].lower()), reverse=True)

    return files_to_show, depth_excludes

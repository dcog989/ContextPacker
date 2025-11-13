import threading
import shutil
from pathlib import Path
from datetime import datetime
import logging
import fnmatch
import queue
import re

from .packager import run_repomix
from .utils import get_app_data_dir, get_downloads_folder
from .error_handling import WorkerErrorHandler, create_process_with_flags, safe_stream_enqueue, validate_tool_availability, create_tool_missing_error
from .constants import UNLIMITED_DEPTH_VALUE, UNLIMITED_DEPTH_REPLACEMENT, LARGE_DIRECTORY_THRESHOLD
from .types import StatusMessage, ProgressMessage, LogMessage, StatusType, FileType, FileInfo, file_info_to_dict, dict_to_file_info


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

    if app.state.temp_dir and Path(app.state.temp_dir).is_dir():
        shutil.rmtree(app.state.temp_dir)

    app.state.temp_dir = _create_session_dir()
    app.log_verbose(f"Created temporary directory: {app.state.temp_dir}")
    app.log_verbose("Starting url conversion...")

    # The actual crawl_website call is submitted by task_handler.py to the executor.


def start_git_clone(app, url, cancel_event):
    """Initializes the temporary directory for git clone.

    Returns:
        str: The path to the created temporary directory.
    """
    app.main_panel.clear_logs()

    if app.state.temp_dir and Path(app.state.temp_dir).is_dir():
        shutil.rmtree(app.state.temp_dir)

    app.state.temp_dir = _create_session_dir()
    app.log_verbose(f"Created temporary directory for git clone: {app.state.temp_dir}")
    app.log_verbose(f"Starting git clone for {url}...")
    return app.state.temp_dir


def _clone_repo_worker(url, path, log_queue, cancel_event, shutdown_event):
    """Worker function to perform a git clone and stream output."""
    # Validate git availability using centralized utility
    if not validate_tool_availability("git"):
        log_queue.put(create_tool_missing_error("git"))
        return

    # Security: Validate and sanitize git URL
    git_url_pattern = r"^(https?://|git@|ssh://|file://)[a-zA-Z0-9._/-]+(:[0-9]+)?(/.*)?$"
    if not re.match(git_url_pattern, url.strip()):
        error_msg = StatusMessage(status=StatusType.ERROR, message="Invalid or potentially malicious git URL provided.")
        log_queue.put(error_msg)
        return

    # Security: Validate path to prevent directory traversal
    try:
        resolved_path = Path(path).resolve()
        # Ensure path is within expected temp directory structure
        if not any(parent.name == "Cache" for parent in resolved_path.parents):
            error_msg = StatusMessage(status=StatusType.ERROR, message="Invalid clone path detected.")
            log_queue.put(error_msg)
            return
    except Exception:
        error_msg = StatusMessage(status=StatusType.ERROR, message="Invalid path provided.")
        log_queue.put(error_msg)
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
            log_queue.put(error_msg)
            return

        output_queue = queue.Queue()
        reader_thread = threading.Thread(target=safe_stream_enqueue, args=(process.stdout, output_queue, shutdown_event), daemon=True)
        reader_thread.start()

        while process.poll() is None:
            if cancel_event.is_set() or shutdown_event.is_set():
                error_handler.handle_process_cleanup(process)
                cancel_msg = StatusMessage(status=StatusType.CANCELLED, message="Git clone cancelled.")
                log_queue.put(cancel_msg)
                return

            try:
                line = output_queue.get(timeout=0.1)
                if line and not shutdown_event.is_set():
                    # line is already a LogMessage object from safe_stream_enqueue
                    log_queue.put(line)
            except queue.Empty:
                continue

        while not output_queue.empty():
            line = output_queue.get_nowait()
            if line and not shutdown_event.is_set():
                # line is already a LogMessage object from safe_stream_enqueue
                log_queue.put(line)

        if cancel_event.is_set() or shutdown_event.is_set():
            cancel_msg = StatusMessage(status=StatusType.CANCELLED, message="Git clone cancelled.")
            log_queue.put(cancel_msg)
            return

        if process.returncode == 0:
            complete_msg = StatusMessage(status=StatusType.CLONE_COMPLETE, message="", path=path)
            log_queue.put(complete_msg)
        else:
            error_msg = StatusMessage(status=StatusType.ERROR, message="Git clone failed. Check the log for details.")
            log_queue.put(error_msg)

    except Exception as e:
        error_msg = error_handler.handle_worker_exception(e, "git clone")
        log_queue.put(error_msg)
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
        if not app.state.temp_dir or not any(Path(app.state.temp_dir).iterdir()):
            app.log_verbose("ERROR: No downloaded content to package. Please run 'Download & Convert' first.")
            return
        source_dir = app.state.temp_dir
        effective_excludes = []
    else:
        source_dir = app.main_panel.local_dir_ctrl.text()
        default_excludes = [p.strip() for p in app.main_panel.local_exclude_ctrl.toPlainText().splitlines() if p.strip()]
        effective_excludes = list(set(default_excludes) | app.state.local_files_to_exclude | app.state.local_depth_excludes)

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
    app.state.final_output_path = str(Path(downloads_path) / output_basename)

    app.log_verbose("\nStarting packaging process...")
    app.log_verbose(f"Output file will be saved to: {app.state.final_output_path}")

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
                progress_value = min(progress_value, 100)  # Clamp at 100%

                # Only send progress updates if progress changed significantly or every batch_size files
                if progress_value != self.last_progress_value or self.processed_count % self.batch_size == 0 or self.processed_count == self.total_files:
                    progress_msg = ProgressMessage(value=progress_value, max_value=100)
                    self.log_queue.put(progress_msg)
                    self.last_progress_value = progress_value

            log_msg = LogMessage(message=msg)
            self.log_queue.put(log_msg)

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
        app.state.final_output_path,
        app.log_queue,
        cancel_event,
        repomix_style,
        exclude_paths,
        progress_handler,
    )
    app.state.worker_future = app.executor.submit(_packaging_worker, *args)


# --- Local File Scanning Refactor ---
def _load_ignore_patterns(ignore_file_path, cache, cache_lock):
    """Load and cache ignore patterns efficiently."""
    if cache is None or cache_lock is None:
        return []

    cache_key = str(ignore_file_path)
    with cache_lock:
        try:
            stat_info = ignore_file_path.stat()
            mtime = stat_info.st_mtime

            if cache_key in cache:
                cached = cache[cache_key]
                if cached.get("mtime") == mtime:
                    return cached["patterns"]

            with open(ignore_file_path, "r", encoding="utf-8") as f:
                patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

            cache[cache_key] = {"mtime": mtime, "patterns": patterns}
            return patterns
        except Exception:
            if cache_key in cache:
                del cache[cache_key]
            return []


def _prepare_filters(root_dir, use_gitignore, custom_excludes, binary_excludes, gitignore_cache, gitignore_cache_lock):
    """Loads all ignore patterns and returns a compiled filter function."""
    base_path = Path(root_dir)
    all_patterns = []

    # 1. Load gitignore patterns
    if use_gitignore:
        ignore_files_to_check = [".repomixignore", ".gitignore"]
        for filename in ignore_files_to_check:
            ignore_file_path = base_path / filename
            if ignore_file_path.is_file():
                all_patterns.extend(_load_ignore_patterns(ignore_file_path, gitignore_cache, gitignore_cache_lock))

    # 2. Add custom and binary excludes
    all_patterns.extend(custom_excludes)
    all_patterns.extend(binary_excludes)

    # 3. Compile patterns to regex
    compiled_regex_patterns = []
    for pattern in all_patterns:
        try:
            compiled_regex_patterns.append(re.compile(fnmatch.translate(pattern)))
        except re.error:
            continue

    # 4. Return a callable that checks against the compiled patterns
    def is_ignored(rel_path, is_dir=False):
        path_str = rel_path.as_posix()
        if is_dir:
            path_str = path_str.rstrip("/") + "/"

        for regex in compiled_regex_patterns:
            if regex.match(path_str):
                return True
        return False

    return is_ignored


def _scan_directory(root_dir, max_depth, is_ignored_func, cancel_event):
    """
    Scans a directory, applies filters, and formats file/folder info.
    Returns a list of FileInfo dictionaries and a set of paths excluded due to depth.
    """
    from collections import deque

    base_path = Path(root_dir)
    files_to_show = []
    depth_excludes = set()

    if max_depth == UNLIMITED_DEPTH_VALUE:
        max_depth = UNLIMITED_DEPTH_REPLACEMENT

    queue = deque([(base_path, Path("."), 0)])  # current_path, rel_path, depth

    while queue:
        if cancel_event and cancel_event.is_set():
            return [], set()

        current_path, rel_path, current_depth = queue.popleft()

        try:
            entries = list(current_path.iterdir())
        except (OSError, PermissionError):
            continue

        for entry in entries:
            if cancel_event and cancel_event.is_set():
                return [], set()

            entry_rel_path = rel_path / entry.name
            is_dir = entry.is_dir()

            if is_ignored_func(entry_rel_path, is_dir):
                continue

            if is_dir:
                rel_path_str = entry_rel_path.as_posix() + "/"
                folder_info = FileInfo(name=rel_path_str, type=FileType.FOLDER, size=0, size_str="", rel_path=rel_path_str)
                files_to_show.append(file_info_to_dict(folder_info))

                if current_depth < max_depth:
                    queue.append((entry, entry_rel_path, current_depth + 1))
                else:
                    depth_excludes.add(rel_path_str)
            else:  # is file
                try:
                    stat_info = entry.stat()
                    size = stat_info.st_size
                    size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
                    rel_path_str = entry_rel_path.as_posix()

                    file_info = FileInfo(name=rel_path_str, type=FileType.FILE, size=size, size_str=size_str, rel_path=rel_path_str)
                    files_to_show.append(file_info_to_dict(file_info))
                except (OSError, ValueError):
                    continue

    return files_to_show, depth_excludes


def _sort_key_func(item):
    """Provides a sort key for file/folder items: folders first, then by name."""
    return (0 if item["type"] == FileType.FOLDER.value else 1, item["name"].lower())


def _format_and_sort_results(scan_results):
    """Sorts the list of file info dictionaries, using a heap for large lists."""
    import heapq

    if not scan_results:
        return []

    if len(scan_results) > LARGE_DIRECTORY_THRESHOLD:
        # Use heap for efficient sorting of large lists
        heap = [(_sort_key_func(item), item) for item in scan_results]
        heapq.heapify(heap)
        return [heapq.heappop(heap)[1] for _ in range(len(heap))]
    else:
        # Use regular sort for smaller lists
        scan_results.sort(key=_sort_key_func)
        return scan_results


def get_local_files(root_dir, max_depth, use_gitignore, custom_excludes, binary_excludes, cancel_event=None, gitignore_cache=None, gitignore_cache_lock=None):
    """
    Scans a directory and returns a filtered, formatted, and sorted list of files and folders.
    This function orchestrates the scanning, filtering, and sorting process.
    """
    base_path = Path(root_dir)
    if not base_path.is_dir():
        return [], set()

    # 1. Prepare filter function from all exclusion sources
    is_ignored_func = _prepare_filters(root_dir, use_gitignore, custom_excludes, binary_excludes, gitignore_cache, gitignore_cache_lock)

    # 2. Scan directory, applying filters as we go to prune branches
    scan_results, depth_excludes = _scan_directory(root_dir, max_depth, is_ignored_func, cancel_event)

    if cancel_event and cancel_event.is_set():
        return [], set()

    # 3. Sort the collected results
    sorted_results = _format_and_sort_results(scan_results)

    return sorted_results, depth_excludes

import threading
import shutil
from pathlib import Path
from datetime import datetime
import logging
import fnmatch
import queue
import re
import os

from .packager import run_repomix
from .utils import get_app_data_dir, get_downloads_folder
from .error_handling import WorkerErrorHandler, create_process_with_flags, safe_stream_enqueue, validate_tool_availability, create_tool_missing_error
from .constants import (
    UNLIMITED_DEPTH_VALUE,
    UNLIMITED_DEPTH_REPLACEMENT,
    LARGE_DIRECTORY_THRESHOLD,
    GIT_CLONE_OUTPUT_POLL_SECONDS,
    GIT_READER_THREAD_JOIN_TIMEOUT_SECONDS,
    REPOMIX_PROGRESS_UPDATE_BATCH_SIZE,
)
from .types import (
    StatusMessage,
    ProgressMessage,
    LogMessage,
    StatusType,
    FileType,
    FileInfo,
    file_info_to_dict,
    dict_to_file_info,
    GitCloneDoneMessage,
    LocalScanCompleteMessage,
)
from .config import CrawlerConfig


def create_session_dir():
    """Creates a new timestamped directory for a session in the app data cache."""
    app_data_path = get_app_data_dir()
    cache_path = app_data_path / "Cache"
    cache_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    session_dir = cache_path / f"session-{timestamp}"
    session_dir.mkdir(exist_ok=True)
    return str(session_dir)


def clone_repo_worker(url, path, message_queue: queue.Queue, cancel_event: threading.Event):
    """Worker function to perform a git clone and stream output."""
    if not validate_tool_availability("git"):
        message_queue.put(create_tool_missing_error("git"))
        return

    git_url_pattern = r"^(https?://|git@|ssh://|file://)[a-zA-Z0-9._/-]+(:[0-9]+)?(/.*)?$"
    if not re.match(git_url_pattern, url.strip()):
        message_queue.put(StatusMessage(status=StatusType.ERROR, message="Invalid or potentially malicious git URL provided."))
        return

    try:
        resolved_path = Path(path).resolve()
        if not any(parent.name == "Cache" for parent in resolved_path.parents):
            message_queue.put(StatusMessage(status=StatusType.ERROR, message="Invalid clone path detected."))
            return
    except Exception:
        message_queue.put(StatusMessage(status=StatusType.ERROR, message="Invalid path provided."))
        return

    error_handler = WorkerErrorHandler(message_queue, cancel_event)  # shutdown_event is cancel_event now
    process = None
    output_queue = queue.Queue()
    reader_thread = None

    try:
        process = create_process_with_flags(["git", "clone", "--depth", "1", url, path])
        if not process.stdout:
            process.wait()
            message_queue.put(StatusMessage(status=StatusType.ERROR, message="Failed to capture git clone output stream."))
            return

        reader_thread = threading.Thread(target=safe_stream_enqueue, args=(process.stdout, output_queue, cancel_event), daemon=True)
        reader_thread.start()

        while process.poll() is None:
            if cancel_event.is_set():
                error_handler.handle_process_cleanup(process)
                message_queue.put(StatusMessage(status=StatusType.CANCELLED, message="Git clone cancelled."))
                return

            try:
                line = output_queue.get(timeout=GIT_CLONE_OUTPUT_POLL_SECONDS)
                if line and isinstance(line, LogMessage):
                    # The stream enqueue still produces LogMessage objects
                    logging.info(line.message.strip())
            except queue.Empty:
                continue

        while not output_queue.empty():
            line = output_queue.get_nowait()
            if line and isinstance(line, LogMessage):
                logging.info(line.message.strip())

        if cancel_event.is_set():
            message_queue.put(StatusMessage(status=StatusType.CANCELLED, message="Git clone cancelled."))
            return

        if process.returncode == 0:
            message_queue.put(GitCloneDoneMessage(path=path))
            message_queue.put(StatusMessage(status=StatusType.CLONE_COMPLETE, message="✔ Git clone successful."))
        else:
            message_queue.put(StatusMessage(status=StatusType.ERROR, message="Git clone failed. Check the log for details."))

    except Exception as e:
        message_queue.put(error_handler.handle_worker_exception(e, "git clone"))
    finally:
        if process:
            if reader_thread and reader_thread.is_alive():
                reader_thread.join(timeout=GIT_READER_THREAD_JOIN_TIMEOUT_SECONDS)
            error_handler.handle_process_cleanup(process)
            error_handler.handle_stream_cleanup(process)


def packaging_worker(source_dir, output_path, repomix_style, exclude_patterns, total_files, message_queue: queue.Queue, cancel_event: threading.Event):
    """Worker that wraps run_repomix and handles progress reporting."""

    class RepomixProgressHandler(logging.Handler):
        def __init__(self, msg_queue, total_files_count):
            super().__init__()
            self.msg_queue = msg_queue
            self.total_files = total_files_count
            self.processed_count = 0
            self.batch_size = REPOMIX_PROGRESS_UPDATE_BATCH_SIZE
            self.last_progress_value = -1

        def emit(self, record):
            if cancel_event.is_set():
                return

            msg = self.format(record)
            if "Processing file:" in msg:
                self.processed_count += 1
                if self.total_files > 0:
                    progress_value = min(int((self.processed_count / self.total_files) * 100), 100)
                    if progress_value != self.last_progress_value or self.processed_count % self.batch_size == 0:
                        self.msg_queue.put(ProgressMessage(value=progress_value, max_value=100))
                        self.last_progress_value = progress_value

            logging.info(msg)

    repomix_logger = logging.getLogger("repomix")
    original_level = repomix_logger.level
    progress_handler = RepomixProgressHandler(message_queue, total_files)

    try:
        repomix_logger.setLevel(logging.INFO)
        repomix_logger.addHandler(progress_handler)
        run_repomix(
            source_dir,
            output_path,
            message_queue,
            cancel_event,
            repomix_style=repomix_style,
            exclude_patterns=exclude_patterns,
        )
    finally:
        repomix_logger.removeHandler(progress_handler)
        repomix_logger.setLevel(original_level)


# --- Local File Scanning ---


def _load_ignore_patterns(ignore_file_path, cache, cache_lock):
    """Load and cache ignore patterns efficiently."""
    cache_key = str(ignore_file_path)
    with cache_lock:
        try:
            stat_info = ignore_file_path.stat()
            mtime = stat_info.st_mtime
            if cache_key in cache and cache[cache_key].get("mtime") == mtime:
                return cache[cache_key]["patterns"]
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
    all_patterns = set(custom_excludes) | set(binary_excludes)

    if use_gitignore:
        for filename in [".repomixignore", ".gitignore"]:
            ignore_file_path = base_path / filename
            if ignore_file_path.is_file():
                all_patterns.update(_load_ignore_patterns(ignore_file_path, gitignore_cache, gitignore_cache_lock))

    compiled_patterns = [re.compile(fnmatch.translate(p)) for p in all_patterns if p]

    def is_ignored(rel_path, is_dir=False):
        path_str = rel_path.as_posix() + ("/" if is_dir else "")
        return any(regex.match(path_str) for regex in compiled_patterns)

    return is_ignored


def _scan_directory(root_dir, max_depth, is_ignored_func, cancel_event):
    from collections import deque

    base_path = Path(root_dir)
    files_to_show, depth_excludes = [], set()
    if max_depth == UNLIMITED_DEPTH_VALUE:
        max_depth = UNLIMITED_DEPTH_REPLACEMENT

    queue = deque([(base_path, Path("."), 0)])
    while queue:
        if cancel_event.is_set():
            return [], set()
        current_path, rel_path, current_depth = queue.popleft()
        try:
            for entry in current_path.iterdir():
                if cancel_event.is_set():
                    return [], set()
                entry_rel_path = rel_path / entry.name
                if is_ignored_func(entry_rel_path, entry.is_dir()):
                    continue

                rel_path_str = entry_rel_path.as_posix()
                if entry.is_dir():
                    files_to_show.append(file_info_to_dict(FileInfo(name=f"{rel_path_str}/", type=FileType.FOLDER, rel_path=f"{rel_path_str}/")))
                    if current_depth < max_depth:
                        queue.append((entry, entry_rel_path, current_depth + 1))
                    else:
                        depth_excludes.add(f"{rel_path_str}/")
                else:
                    try:
                        stat = entry.stat()
                        size_str = f"{stat.st_size / 1024:.1f} KB" if stat.st_size >= 1024 else f"{stat.st_size} B"
                        files_to_show.append(file_info_to_dict(FileInfo(name=rel_path_str, type=FileType.FILE, size=stat.st_size, size_str=size_str, rel_path=rel_path_str)))
                    except (OSError, ValueError):
                        continue
        except (OSError, PermissionError):
            continue
    return files_to_show, depth_excludes


def _sort_results(results):
    import heapq

    sort_key = lambda item: (0 if item["type"] == FileType.FOLDER.value else 1, item["name"].lower())
    if len(results) > LARGE_DIRECTORY_THRESHOLD:
        heap = [(sort_key(item), item) for item in results]
        heapq.heapify(heap)
        return [heapq.heappop(heap)[1] for _ in range(len(heap))]
    return sorted(results, key=sort_key)


def get_local_files_worker(root_dir, max_depth, use_gitignore, custom_excludes, binary_excludes, gitignore_cache, gitignore_cache_lock, message_queue: queue.Queue, cancel_event: threading.Event):
    """Worker to scan local files and report back via message queue."""
    try:
        base_path = Path(root_dir)
        if not base_path.is_dir():
            message_queue.put(LocalScanCompleteMessage(results=([], set())))
            return

        is_ignored_func = _prepare_filters(root_dir, use_gitignore, custom_excludes, binary_excludes, gitignore_cache, gitignore_cache_lock)
        scan_results, depth_excludes = _scan_directory(root_dir, max_depth, is_ignored_func, cancel_event)
        if cancel_event.is_set():
            message_queue.put(LocalScanCompleteMessage(results=None))
            return

        sorted_results = _sort_results(scan_results)
        message_queue.put(LocalScanCompleteMessage(results=(sorted_results, depth_excludes)))
    except Exception as e:
        logging.error(f"Error scanning directory: {e}", exc_info=True)
        message_queue.put(LocalScanCompleteMessage(results=None))


def open_folder_worker(folder_path: str, message_queue: queue.Queue, cancel_event: threading.Event):
    """Simple worker to open a folder without blocking the UI."""
    from .utils import open_folder

    if cancel_event.is_set():
        return
    try:
        open_folder(folder_path)
    except Exception as e:
        logging.error(f"Failed to open folder {folder_path}: {e}")

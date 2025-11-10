import threading
import shutil
from pathlib import Path
from datetime import datetime
import logging
import os
import fnmatch
import subprocess
import queue
import sys

from .packager import run_repomix
from .crawler import crawl_website
from .utils import get_app_data_dir, get_downloads_folder


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
    """Initializes and starts the web crawling process in a new thread."""
    app.main_panel.clear_logs()
    app.main_panel.progress_gauge.setValue(0)

    if app.temp_dir and Path(app.temp_dir).is_dir():
        shutil.rmtree(app.temp_dir)

    app.temp_dir = _create_session_dir()
    app.log_verbose(f"Created temporary directory: {app.temp_dir}")
    crawler_config = app.main_panel.get_crawler_config(app.temp_dir)

    app.log_verbose("Starting url conversion...")
    app.worker_thread = threading.Thread(target=crawl_website, args=(crawler_config, app.log_queue, cancel_event, app.shutdown_event), daemon=True)
    app.worker_thread.start()


def _enqueue_output(stream, q):
    """Reads lines from a stream and puts them into a queue."""
    try:
        for line in iter(stream.readline, ""):
            q.put(line)
    finally:
        # Ensure stream is always closed, even if an exception occurs
        try:
            stream.close()
        except Exception:
            # Log the error but don't let it propagate
            # The stream might already be closed or invalid
            pass


def start_git_clone(app, cancel_event):
    """Initializes and starts a git clone process in a new thread."""
    app.main_panel.clear_logs()

    if app.temp_dir and Path(app.temp_dir).is_dir():
        shutil.rmtree(app.temp_dir)

    app.temp_dir = _create_session_dir()
    app.log_verbose(f"Created temporary directory for git clone: {app.temp_dir}")
    url = app.main_panel.start_url_ctrl.text()

    app.log_verbose(f"Starting git clone for {url}...")
    app.worker_thread = threading.Thread(target=_clone_repo_worker, args=(url, app.temp_dir, app.log_queue, cancel_event, app.shutdown_event), daemon=True)
    app.worker_thread.start()


def _clone_repo_worker(url, path, log_queue, cancel_event, shutdown_event):
    """Worker function to perform a git clone and stream output."""
    if not shutil.which("git"):
        error_msg = "ERROR: Git is not installed or not found in your system's PATH. Please install Git to use this feature."
        log_queue.put({"type": "status", "status": "error", "message": error_msg})
        return

    process = None
    output_queue = None
    reader_thread = None

    try:
        process = subprocess.Popen(
            ["git", "clone", "--depth", "1", url, path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        if not process.stdout:
            process.wait()
            log_queue.put({"type": "status", "status": "error", "message": "Failed to capture git clone output stream."})
            return

        output_queue = queue.Queue()
        reader_thread = threading.Thread(target=_enqueue_output, args=(process.stdout, output_queue), daemon=True)
        reader_thread.start()

        while process.poll() is None:
            if cancel_event.is_set():
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                log_queue.put({"type": "status", "status": "cancelled", "message": "Git clone cancelled."})
                return

            try:
                line = output_queue.get(timeout=0.1)
                if line and not shutdown_event.is_set():
                    log_queue.put({"type": "log", "message": line.strip()})
            except queue.Empty:
                continue

        while not output_queue.empty():
            line = output_queue.get_nowait()
            if line and not shutdown_event.is_set():
                log_queue.put({"type": "log", "message": line.strip()})

        if cancel_event.is_set():
            log_queue.put({"type": "status", "status": "cancelled", "message": "Git clone cancelled."})
            return

        if process.returncode == 0:
            log_queue.put({"type": "status", "status": "clone_complete", "path": path})
        else:
            log_queue.put({"type": "status", "status": "error", "message": "Git clone failed. Check the log for details."})

    except Exception as e:
        log_queue.put({"type": "status", "status": "error", "message": f"An error occurred while cloning the repository: {e}"})
    finally:
        # Ensure proper cleanup of process resources
        if process is not None:
            # Wait for reader thread to finish processing the stream
            if reader_thread is not None and reader_thread.is_alive():
                reader_thread.join(timeout=1.0)

            # Ensure the process is properly terminated
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except (subprocess.TimeoutExpired, OSError):
                    try:
                        process.kill()
                        process.wait(timeout=1)
                    except (subprocess.TimeoutExpired, OSError):
                        # Process couldn't be killed, but we've done our best
                        pass

            # Close any remaining file descriptors
            try:
                if process.stdout:
                    process.stdout.close()
            except Exception:
                pass  # Stream might already be closed

            try:
                if process.stderr:
                    process.stderr.close()
            except Exception:
                pass  # Stream might already be closed

            try:
                if process.stdin:
                    process.stdin.close()
            except Exception:
                pass  # Stream might already be closed


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

        def emit(self, record):
            # Don't emit during shutdown to prevent race conditions
            if self.shutdown_event.is_set():
                return

            msg = self.format(record)
            if "Processing file:" in msg:
                self.processed_count += 1
                progress_value = int((self.processed_count / self.total_files) * 100) if self.total_files > 0 else 0
                self.log_queue.put({"type": "progress", "value": progress_value, "max_value": 100})

            self.log_queue.put({"type": "log", "message": msg})

    total_files_for_progress = 0
    is_web_mode = app.main_panel.web_crawl_radio.isChecked()
    if file_list is not None:
        if is_web_mode:
            total_files_for_progress = len(file_list)
        else:
            total_files_for_progress = len([f for f in file_list if f.get("type") == "File"])

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
    app.worker_thread = threading.Thread(target=_packaging_worker, args=args, daemon=True)
    app.worker_thread.start()


def get_local_files(root_dir, max_depth, use_gitignore, custom_excludes, binary_excludes, cancel_event=None, gitignore_cache=None):
    """
    Scans a directory and returns a filtered list of files and folders,
    pruning ignored directories for efficiency.
    """
    base_path = Path(root_dir)
    if not base_path.is_dir():
        return [], set()

    if max_depth == 9:  # Treat 9 as unlimited
        max_depth = sys.maxsize

    files_to_show = []
    depth_excludes = set()
    all_ignore_patterns = list(custom_excludes)

    ignore_files_to_check = [".repomixignore"]
    if use_gitignore:
        ignore_files_to_check.append(".gitignore")

    for filename in ignore_files_to_check:
        ignore_file_path = base_path / filename
        if not ignore_file_path.is_file():
            continue

        cache_key = str(ignore_file_path)
        try:
            mtime = ignore_file_path.stat().st_mtime
            if gitignore_cache is not None and cache_key in gitignore_cache and gitignore_cache[cache_key].get("mtime") == mtime:
                patterns = gitignore_cache[cache_key]["patterns"]
            else:
                with open(ignore_file_path, "r", encoding="utf-8") as f:
                    read_patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
                    patterns = read_patterns
                    if gitignore_cache is not None:
                        gitignore_cache[cache_key] = {"mtime": mtime, "patterns": patterns}
            all_ignore_patterns.extend(patterns)
        except Exception:
            if gitignore_cache is not None and cache_key in gitignore_cache:
                del gitignore_cache[cache_key]

    all_ignore_patterns.extend(binary_excludes)

    for root, dirnames, filenames in os.walk(str(base_path), topdown=True):
        if cancel_event and cancel_event.is_set():
            return [], set()
        root_path = Path(root)
        rel_root_path = root_path.relative_to(base_path)

        depth = 0 if rel_root_path == Path(".") else len(rel_root_path.parts)
        if depth >= max_depth:
            for d in dirnames:
                depth_excludes.add(f"{(rel_root_path / d).as_posix()}/")
            dirnames[:] = []

        ignored_dirs = set()
        for d in dirnames:
            dir_path_posix = (rel_root_path / d).as_posix()
            if any(fnmatch.fnmatch(dir_path_posix, pattern) or fnmatch.fnmatch(f"{dir_path_posix}/", pattern) for pattern in all_ignore_patterns):
                ignored_dirs.add(d)
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs]

        # Check for cancellation before processing directories
        if cancel_event and cancel_event.is_set():
            return [], set()

        for d in dirnames:
            rel_path_str = (rel_root_path / d).as_posix()
            files_to_show.append({"name": rel_path_str + "/", "type": "Folder", "size": 0, "size_str": "", "rel_path": rel_path_str + "/"})

        # Check for cancellation before processing files
        if cancel_event and cancel_event.is_set():
            return [], set()

        for f in filenames:
            rel_path = rel_root_path / f
            if not any(fnmatch.fnmatch(rel_path.as_posix(), pattern) for pattern in all_ignore_patterns):
                try:
                    full_path = root_path / f
                    size = full_path.stat().st_size
                    size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
                    rel_path_str = rel_path.as_posix()
                    files_to_show.append({"name": rel_path_str, "type": "File", "size": size, "size_str": size_str, "rel_path": rel_path_str})
                except (OSError, ValueError):
                    continue

    if cancel_event and cancel_event.is_set():
        return [], set()

    files_to_show.sort(key=lambda p: (p["type"] != "Folder", p["name"].lower()), reverse=True)
    return files_to_show, depth_excludes

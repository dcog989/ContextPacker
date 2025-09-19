import threading
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import wx
import logging
import os
import fnmatch
import subprocess
import queue
import multiprocessing

from .packager import run_repomix


def start_download(app, cancel_event):
    """Initializes and starts the web crawling process in a new process."""
    app.main_panel.list_panel.clear_logs()
    app.main_panel.list_panel.progress_gauge.SetValue(0)

    if app.temp_dir and Path(app.temp_dir).is_dir():
        shutil.rmtree(app.temp_dir)

    app.temp_dir = tempfile.mkdtemp(prefix="ContextPacker-")
    app.log_verbose(f"Created temporary directory: {app.temp_dir}")
    crawler_config = app.main_panel.crawler_panel.get_crawler_config(app.temp_dir)

    app.log_verbose("Starting url conversion...")
    app.worker_thread = multiprocessing.Process(target=_crawl_process_worker, args=(crawler_config, app.log_queue, cancel_event), daemon=True)
    app.worker_thread.start()


def _enqueue_output(stream, q):
    """Reads lines from a stream and puts them into a queue."""
    for line in iter(stream.readline, ""):
        q.put(line)
    stream.close()


def start_git_clone(app, cancel_event):
    """Initializes and starts a git clone process in a new thread."""
    app.main_panel.list_panel.clear_logs()

    if app.temp_dir and Path(app.temp_dir).is_dir():
        shutil.rmtree(app.temp_dir)

    app.temp_dir = tempfile.mkdtemp(prefix="ContextPacker-")
    app.log_verbose(f"Created temporary directory for git clone: {app.temp_dir}")
    url = app.main_panel.crawler_panel.start_url_ctrl.GetValue()

    app.log_verbose(f"Starting git clone for {url}...")
    app.worker_thread = threading.Thread(target=_clone_repo_worker, args=(url, app.temp_dir, app.log_queue, cancel_event), daemon=True)
    app.worker_thread.start()


def _crawl_process_worker(crawler_config, log_queue, cancel_event):
    """
    This function runs in a separate process to perform the web crawl.
    It imports necessary modules within the function to ensure it works
    correctly with multiprocessing.
    """
    from .crawler import crawl_website

    crawl_website(crawler_config, log_queue, cancel_event)


def _clone_repo_worker(url, path, log_queue, cancel_event):
    """Worker function to perform a git clone and stream output."""
    if not shutil.which("git"):
        error_msg = "ERROR: Git is not installed or not found in your system's PATH. Please install Git to use this feature."
        log_queue.put({"type": "status", "status": "error", "message": error_msg})
        return

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
                break

            try:
                line = output_queue.get(timeout=0.1)
                if line:
                    log_queue.put({"type": "log", "message": line.strip()})
            except queue.Empty:
                continue

        while not output_queue.empty():
            line = output_queue.get_nowait()
            if line:
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


def start_packaging(app, cancel_event, file_list=None):
    """Initializes and starts the packaging process in a new thread."""
    is_web_mode = app.main_panel.web_crawl_radio.GetValue()
    app.filename_prefix = app.main_panel.output_filename_ctrl.GetValue().strip() or "ContextPacker-package"
    source_dir = ""
    effective_excludes = []

    if is_web_mode:
        if not app.temp_dir or not any(Path(app.temp_dir).iterdir()):
            app.log_verbose("ERROR: No downloaded content to package. Please run 'Download & Convert' first.")
            return
        source_dir = app.temp_dir
        effective_excludes = []
    else:
        source_dir = app.main_panel.local_panel.local_dir_ctrl.GetValue()
        default_excludes = [p.strip() for p in app.main_panel.local_panel.local_exclude_ctrl.GetValue().splitlines() if p.strip()]

        additional_excludes = set()
        if not app.main_panel.local_panel.include_subdirs_check.GetValue():
            source_path = Path(source_dir)
            if source_path.is_dir():
                for item in source_path.iterdir():
                    if item.is_dir():
                        additional_excludes.add(f"{item.name}/")

        effective_excludes = list(set(default_excludes) | app.local_files_to_exclude | additional_excludes)

    extension = app.main_panel.output_format_choice.GetStringSelection()
    style_map = {".md": "markdown", ".txt": "plain", ".xml": "xml"}
    repomix_style = style_map.get(extension, "markdown")

    app.main_panel.list_panel.progress_gauge.SetValue(0)

    _run_packaging_thread(app, source_dir, app.filename_prefix, effective_excludes, extension, repomix_style, cancel_event, file_list)


def _run_packaging_thread(app, source_dir, filename_prefix, exclude_paths, extension, repomix_style, cancel_event, file_list=None):
    """Configures and runs the repomix packager in a worker thread."""
    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    downloads_path = app._get_downloads_folder()
    output_basename = f"{filename_prefix}-{timestamp}{extension}"
    app.final_output_path = str(Path(downloads_path) / output_basename)

    app.log_verbose("\nStarting packaging process...")

    class RepomixProgressHandler(logging.Handler):
        def __init__(self, log_queue_ref, total_files_ref):
            super().__init__()
            self.log_queue = log_queue_ref
            self.processed_count = 0
            self.total_files = total_files_ref

        def emit(self, record):
            msg = self.format(record)
            if "Processing file:" in msg:
                self.processed_count += 1
                progress_value = int((self.processed_count / self.total_files) * 100) if self.total_files > 0 else 0
                wx.CallAfter(self.log_queue.put, {"type": "progress", "value": progress_value, "max_value": 100})

            wx.CallAfter(self.log_queue.put, {"type": "log", "message": msg})

    total_files_for_progress = 0
    is_web_mode = app.main_panel.web_crawl_radio.GetValue()
    if file_list is not None:
        if is_web_mode:
            total_files_for_progress = len(file_list)
        else:
            total_files_for_progress = len([f for f in file_list if f.get("type") == "File"])
    else:  # Fallback to scanning if file_list is not provided
        if Path(source_dir).is_dir():
            current_exclude_paths = exclude_paths or []
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    rel_path_str = file_path.relative_to(source_dir).as_posix()
                    is_excluded = any(fnmatch.fnmatch(rel_path_str, pattern) for pattern in current_exclude_paths)
                    if not is_excluded:
                        total_files_for_progress += 1

    progress_handler = RepomixProgressHandler(app.log_queue, total_files_for_progress)
    progress_handler.setLevel(logging.INFO)

    repomix_logger = logging.getLogger("repomix")
    original_level = repomix_logger.level
    repomix_logger.setLevel(logging.INFO)
    repomix_logger.addHandler(progress_handler)

    try:
        app.worker_thread = threading.Thread(target=run_repomix, args=(source_dir, app.final_output_path, app.log_queue, cancel_event, repomix_style, exclude_paths), daemon=True)
        app.worker_thread.start()
    finally:
        repomix_logger.removeHandler(progress_handler)
        repomix_logger.setLevel(original_level)


def populate_local_files(app):
    """Convenience function to trigger a refresh of the local file list."""
    app.populate_local_file_list()


def get_local_files(root_dir, include_subdirs, custom_excludes, binary_excludes, cancel_event=None):
    """
    Scans a directory and returns a filtered list of files and folders,
    pruning ignored directories for efficiency.
    """
    base_path = Path(root_dir)
    if not base_path.is_dir():
        return []

    files_to_show = []
    all_ignore_patterns = list(custom_excludes)

    gitignore_path = base_path / ".gitignore"
    if gitignore_path.is_file():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                gitignore_patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
                all_ignore_patterns.extend(gitignore_patterns)
        except Exception:
            pass

    all_ignore_patterns.extend(binary_excludes)

    for root, dirnames, filenames in os.walk(str(base_path), topdown=True):
        if cancel_event and cancel_event.is_set():
            return []
        root_path = Path(root)
        rel_root_path = root_path.relative_to(base_path)

        ignored_dirs = set()
        for d in dirnames:
            dir_path_posix = (rel_root_path / d).as_posix()
            if any(fnmatch.fnmatch(dir_path_posix, pattern) or fnmatch.fnmatch(f"{dir_path_posix}/", pattern) for pattern in all_ignore_patterns):
                ignored_dirs.add(d)
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs]

        for d in dirnames:
            rel_path_str = (rel_root_path / d).as_posix()
            files_to_show.append({"name": rel_path_str + "/", "type": "Folder", "size": 0, "size_str": "", "rel_path": rel_path_str + "/"})

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

        if not include_subdirs:
            break

    if cancel_event and cancel_event.is_set():
        return []

    files_to_show.sort(key=lambda p: (p["type"] != "Folder", p["name"].lower()), reverse=True)
    return files_to_show

import os
from datetime import datetime
from pathlib import Path
import ctypes
import subprocess
import platform
import threading
import queue
import multiprocessing
import sys
import concurrent.futures

from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtGui import QIcon, QFontDatabase

from ui.main_window import MainWindow, AboutDialog
from ui.styles import AppTheme
import core.actions as actions
from core.version import __version__
from core.config_manager import get_config, save_config
from core.task_handler import TaskHandler
from core.utils import get_app_data_dir, cleanup_old_directories, resource_path
from core.constants import (
    BATCH_UPDATE_INTERVAL_MS,
    EXCLUDE_UPDATE_INTERVAL_MS,
    UI_UPDATE_INTERVAL_MS,
    MAX_BATCH_SIZE,
    UI_UPDATE_BATCH_SIZE,
)
from core.types import LogMessage, StatusMessage, ProgressMessage, FileSavedMessage, UITaskMessage, UITaskStopMessage, UITaskStoppingMessage, GitCloneDoneMessage, LocalScanCompleteMessage, TaskType, dict_to_message, message_to_dict

config = get_config()
BINARY_FILE_PATTERNS = config.get("binary_file_patterns", [])


class WorkerSignals(QObject):
    message = Signal(dict)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        w, h = config.get("window_size", [-1, -1])
        if w > 0 and h > 0:
            self.resize(w, h)
        else:
            self.resize(1600, 950)
        self.setWindowTitle("ContextPacker")

        self._setup_app_dirs_and_cleanup()

        self.version = __version__
        self.task_handler = TaskHandler(self)
        self.temp_dir = None
        self.final_output_path = None
        self.log_queue = queue.Queue()
        self.cancel_event = None
        self.worker_future = None  # Replaces self.worker_thread
        self.queue_listener_shutdown = threading.Event()
        self.shutdown_event = threading.Event()
        self.is_task_running = False
        self.local_files_to_exclude = set()
        self.local_depth_excludes = set()
        self.gitignore_cache = {}

        # Use ThreadPoolExecutor to manage all worker tasks
        # Max workers set low as most tasks are singular (download, package)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.local_scan_future = None
        self.local_scan_cancel_event = None

        self.signals = WorkerSignals()
        self.signals.message.connect(self._process_log_queue_message)

        self.main_panel = MainWindow(self)
        self.setCentralWidget(self.main_panel)

        self._load_custom_font()

        # Apply the application theme
        theme = AppTheme()
        self.setStyleSheet(theme.get_stylesheet())

        self._set_icon()

        self.queue_listener_thread = None
        self.scraped_files_batch = []
        self.discovered_count_batch = 0
        self.batch_update_timer = QTimer(self)
        self.batch_update_timer.setInterval(BATCH_UPDATE_INTERVAL_MS)
        self.batch_update_timer.timeout.connect(self.on_batch_update_timer)
        self.batch_update_timer.start()  # Start persistent timer immediately

        # UI update batching counters
        self.ui_update_counter = 0
        self.ui_update_batch_size = UI_UPDATE_BATCH_SIZE  # Batch UI updates every N files

        # Memory management: limit batch size to prevent unbounded growth
        self.max_batch_size = MAX_BATCH_SIZE  # Maximum items in scraped_files_batch

        self.exclude_update_timer = QTimer(self)
        self.exclude_update_timer.setInterval(EXCLUDE_UPDATE_INTERVAL_MS)
        self.exclude_update_timer.setSingleShot(True)
        self.exclude_update_timer.timeout.connect(self.start_local_file_scan)

        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.setInterval(UI_UPDATE_INTERVAL_MS)
        self.ui_update_timer.timeout.connect(self._update_timestamp_label)
        self.ui_update_timer.start()

        self.toggle_input_mode()
        self.show()

    def _load_custom_font(self):
        font_path = resource_path("assets/fonts/SourceCodePro-Regular.ttf")
        if font_path.exists():
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id == -1:
                self.log_verbose(f"Warning: Failed to load font from {font_path}")

    def _setup_app_dirs_and_cleanup(self):
        app_data_dir = get_app_data_dir()
        cache_dir = app_data_dir / "Cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            days_threshold = config.get("max_age_logs", 21)
            cleanup_old_directories(cache_dir, days_threshold)
        except Exception as e:
            print(f"Warning: Failed to clean up old cache files: {e}")

    def start_queue_listener(self):
        """Start the queue listener thread if not already running."""
        if self.queue_listener_thread is None or not self.queue_listener_thread.is_alive():
            self.queue_listener_shutdown.clear()
            self.queue_listener_thread = threading.Thread(target=self._queue_listener_worker, daemon=True)
            self.queue_listener_thread.start()

    def stop_queue_listener(self, timeout=5.0):
        """
        Safely stop the queue listener thread.

        Args:
            timeout: Maximum seconds to wait for thread to finish

        Returns:
            bool: True if stopped cleanly, False if timeout occurred
        """
        if self.queue_listener_thread is None:
            return True

        if not self.queue_listener_thread.is_alive():
            self.queue_listener_thread = None
            return True

        self.queue_listener_shutdown.set()

        try:
            self.log_queue.put(None, timeout=1.0)
        except queue.Full:
            pass

        self.queue_listener_thread.join(timeout=timeout)

        if self.queue_listener_thread.is_alive():
            self._drain_queue()
            return False

        self.queue_listener_thread = None
        return True

    def _queue_listener_worker(self):
        """
        Worker thread that processes messages from log_queue.

        Runs until shutdown event is set AND queue is empty,
        or until sentinel (None) is received.
        """
        while not self.queue_listener_shutdown.is_set():
            try:
                msg_obj = self.log_queue.get(timeout=0.5)

                if msg_obj is None:
                    break

                self.signals.message.emit(msg_obj)
                self.log_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing queue message: {e}")
                continue

        self._drain_queue()

    def _drain_queue(self):
        """Process all remaining messages in the queue without blocking."""
        while True:
            try:
                msg_obj = self.log_queue.get_nowait()
                if msg_obj is not None:
                    # Don't emit signals during shutdown to prevent race conditions
                    if not self.shutdown_event.is_set():
                        self.signals.message.emit(msg_obj)
                    self.log_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                print(f"Error draining queue: {e}")
                continue

    def _process_log_queue_message(self, msg_obj):
        # Ignore messages during shutdown to prevent race conditions
        if self.shutdown_event.is_set():
            return

        # Convert dictionary to typed message for better type safety
        typed_msg = dict_to_message(msg_obj)

        if isinstance(typed_msg, LogMessage):
            self.log_verbose(typed_msg.message)
        elif isinstance(typed_msg, FileSavedMessage):
            self.scraped_files_batch.append(msg_obj)

            # Memory management: check if batch is getting too large
            if len(self.scraped_files_batch) >= self.max_batch_size:
                # Force immediate UI update to clear the batch
                self.main_panel.add_scraped_files_batch(self.scraped_files_batch)
                self.scraped_files_batch.clear()
                self.log_verbose(f"  -> Memory management: processed large batch of {self.max_batch_size} files")

            # Batch UI updates to reduce frame drops
            self.ui_update_counter += 1
            self.discovered_count_batch = max(self.discovered_count_batch, typed_msg.queue_size)

            # Only update UI every ui_update_batch_size files or on timer
            if self.ui_update_counter >= self.ui_update_batch_size:
                self.main_panel.update_discovered_count(self.discovered_count_batch)
                verbose_msg = f"  -> Saved: {typed_msg.filename} [{typed_msg.pages_saved}/{typed_msg.max_pages}]"
                self.log_verbose(verbose_msg)
                self.ui_update_counter = 0
        elif isinstance(typed_msg, ProgressMessage):
            self.main_panel.progress_gauge.setValue(typed_msg.value)
            self.main_panel.progress_gauge.setMaximum(typed_msg.max_value)
        elif isinstance(typed_msg, StatusMessage):
            self.task_handler.handle_status(typed_msg.status.value, msg_obj)
        elif isinstance(typed_msg, UITaskMessage):
            self._handle_ui_task_start(typed_msg.task.value)
        elif isinstance(typed_msg, UITaskStoppingMessage):
            self._handle_ui_task_stopping()
        elif isinstance(typed_msg, UITaskStopMessage):
            self._handle_ui_task_stop(typed_msg.was_cancelled)
        elif isinstance(typed_msg, GitCloneDoneMessage):
            self._handle_git_clone_done(typed_msg.path)
        elif isinstance(typed_msg, LocalScanCompleteMessage):
            QApplication.restoreOverrideCursor()
            self.main_panel.local_panel.setEnabled(True)
            self.local_scan_future = None
            if typed_msg.results is not None:
                files, depth_excludes = typed_msg.results
                self.main_panel.populate_local_file_list(files)
                self.local_depth_excludes = depth_excludes
        else:
            # Fallback for unknown message types
            self.log_verbose(str(msg_obj.get("message", "")))

    def _handle_ui_task_start(self, task):
        dl_button = self.main_panel.download_button
        pkg_button = self.main_panel.package_button

        widget_to_keep_enabled = dl_button if task == TaskType.DOWNLOAD.value else pkg_button
        self._toggle_ui_controls(False, widget_to_keep_enabled=widget_to_keep_enabled)

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.is_task_running = True
        self.main_panel.copy_button.setEnabled(False)

        # Reset batching counters for new task
        self.ui_update_counter = 0
        self.discovered_count_batch = 0

        if task == TaskType.DOWNLOAD.value:
            dl_button.setText("Stop!")
            pkg_button.setEnabled(False)
        elif task == TaskType.PACKAGE.value:
            pkg_button.setText("Stop!")
            dl_button.setEnabled(False)

    def _handle_ui_task_stopping(self):
        dl_button = self.main_panel.download_button
        pkg_button = self.main_panel.package_button

        if dl_button.isEnabled():
            dl_button.setText("Stopping...")
            dl_button.setEnabled(False)

        if pkg_button.isEnabled():
            pkg_button.setText("Stopping...")
            pkg_button.setEnabled(False)

        self.log_verbose("Stopping process...")

    def _handle_ui_task_stop(self, was_cancelled):
        if self.is_task_running:
            QApplication.restoreOverrideCursor()
            self.is_task_running = False

        self.stop_queue_listener(timeout=2.0)
        self._toggle_ui_controls(True)

        self.worker_future = None
        self.cancel_event = None

        if self.shutdown_event.is_set():
            self.close()
            return

        dl_button = self.main_panel.download_button
        dl_button.setText("Download & Convert")
        dl_button.setEnabled(True)

        pkg_button = self.main_panel.package_button
        pkg_button.setText("Package")
        pkg_button.setEnabled(True)

        self.main_panel.progress_gauge.setValue(0)
        self._update_button_states()

        self.ui_update_timer.start()

    def _handle_git_clone_done(self, path):
        self.main_panel.local_dir_ctrl.setText(path)
        self.main_panel.web_crawl_radio.setChecked(False)
        self.main_panel.local_dir_radio.setChecked(True)
        self.toggle_input_mode()

    def on_batch_update_timer(self):
        if self.scraped_files_batch:
            self.main_panel.add_scraped_files_batch(self.scraped_files_batch)
            self.scraped_files_batch.clear()
            self._update_button_states()

        # Update discovered count on timer to ensure final count is displayed
        if self.discovered_count_batch > 0:
            self.main_panel.update_discovered_count(self.discovered_count_batch)

        # Reset counters
        self.ui_update_counter = 0

    def _set_icon(self):
        icon_path = resource_path("assets/icons/ContextPacker.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def closeEvent(self, event):
        config["window_size"] = [self.width(), self.height()]
        sash_qba = self.main_panel.splitter.saveState().toBase64()
        config["sash_state"] = bytes(sash_qba.data()).decode("utf-8")
        save_config(config)

        # Set shutdown event first to prevent new signal processing
        self.shutdown_event.set()
        self.executor.shutdown(wait=False)  # Shutdown executor non-blocking

        # Disconnect signals to prevent race conditions during shutdown
        try:
            self.signals.message.disconnect()
        except RuntimeError:
            pass  # Signal already disconnected

        queue_stopped = self.stop_queue_listener(timeout=5.0)
        if not queue_stopped:
            print("Warning: Queue listener did not stop cleanly")

        if self._cleanup_workers():
            event.ignore()
            return

        event.accept()

    def _cleanup_workers(self):
        """
        Sends cancel signal to any running worker tasks (download/package and local scan)
        and attempts to check their status.

        Returns:
            bool: True if any worker is still running and the shutdown is deferred.
        """
        is_worker_running = False

        if self.worker_future and not self.worker_future.done():
            if not self.shutdown_event.is_set():
                self.shutdown_event.set()
                self.log_verbose("Shutdown requested. Waiting for main task to terminate...")
                if self.cancel_event:
                    self.cancel_event.set()
                self._toggle_ui_controls(False)
            is_worker_running = True

        if self.local_scan_future and not self.local_scan_future.done():
            if not self.shutdown_event.is_set():
                self.shutdown_event.set()
                self.log_verbose("Shutdown requested. Waiting for file scanner to terminate...")

            if self.local_scan_cancel_event:
                self.local_scan_cancel_event.set()

            # Since ThreadPoolExecutor threads cannot be forcefully terminated,
            # we rely on the internal logic of the task (get_local_files) to check the cancel event.
            # We don't join here as it will block the main thread.
            is_worker_running = True

        if is_worker_running:
            return True

        self.shutdown_event.clear()
        return False

    def _toggle_ui_controls(self, enable=True, widget_to_keep_enabled=None):
        widgets_to_toggle = [
            self.main_panel.web_crawl_radio,
            self.main_panel.local_dir_radio,
            self.main_panel.crawler_panel,
            self.main_panel.local_panel,
            self.main_panel.output_filename_ctrl,
            self.main_panel.output_format_choice,
            self.main_panel.package_button,
            self.main_panel.download_button,
            self.main_panel.delete_button,
        ]
        for widget in widgets_to_toggle:
            if widget is not widget_to_keep_enabled:
                widget.setEnabled(enable)
        if not enable and widget_to_keep_enabled:
            widget_to_keep_enabled.setEnabled(True)

    def on_toggle_input_mode(self):
        self.toggle_input_mode()

    def toggle_input_mode(self):
        is_url_mode = self.main_panel.web_crawl_radio.isChecked()
        self.main_panel.crawler_panel.setVisible(is_url_mode)
        self.main_panel.local_panel.setVisible(not is_url_mode)
        self.main_panel.toggle_output_view(is_web_mode=is_url_mode)
        if not is_url_mode:
            self.start_local_file_scan()
        self._update_button_states()

    def on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Choose a directory:")
        if path:
            self.main_panel.local_dir_ctrl.setText(path)
            self.start_local_file_scan()
        self._update_button_states()

    def on_local_filters_changed(self):
        self.start_local_file_scan()

    def on_exclude_text_update(self):
        self.exclude_update_timer.start()

    def on_download_button_click(self):
        if self.is_task_running:
            self.task_handler.stop_current_task()
        else:
            self.task_handler.start_download_task()

    def on_package_button_click(self):
        if self.is_task_running:
            self.task_handler.stop_current_task()
        else:
            file_list = self.main_panel.scraped_files if self.main_panel.web_crawl_radio.isChecked() else self.main_panel.local_files
            self.task_handler.start_package_task(file_list)

    def on_copy_to_clipboard(self):
        if not self.final_output_path or not Path(self.final_output_path).exists():
            self.log_verbose("ERROR: No output file found to copy.")
            return
        try:
            with open(self.final_output_path, "r", encoding="utf-8") as f:
                content = f.read()
            QApplication.clipboard().setText(content)
            self.log_verbose(f"Copied {len(content):,} characters to clipboard.")
        except Exception as e:
            self.log_verbose(f"ERROR: Failed to copy to clipboard: {e}")

    def _update_timestamp_label(self):
        if not self.is_task_running:
            ts = datetime.now().strftime("-%y%m%d-%H%M%S")
            self.main_panel.output_timestamp_label.setText(ts)

    def _update_button_states(self):
        is_web_mode = self.main_panel.web_crawl_radio.isChecked()
        package_ready = False
        copy_ready = bool(self.final_output_path and Path(self.final_output_path).exists())

        if is_web_mode:
            package_ready = bool(self.main_panel.scraped_files)
        else:
            package_ready = bool(self.main_panel.local_dir_ctrl.text() and Path(self.main_panel.local_dir_ctrl.text()).is_dir())
        self.main_panel.package_button.setEnabled(package_ready)
        self.main_panel.copy_button.setEnabled(copy_ready)

    def log_verbose(self, message):
        # Count lines in the message (handle multi-line messages)
        lines_in_message = message.count("\n") + 1
        self.main_panel.log_line_count += lines_in_message

        # Check if we need to trim the log before adding new content
        self.main_panel._manage_log_size()

        self.main_panel.verbose_log_widget.append(message)

    def _open_output_folder(self):
        if not self.final_output_path:
            return
        self.log_verbose("Opening output folder...")
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", "/select,", self.final_output_path], creationflags=0x08000000)
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-R", self.final_output_path], check=True)
            else:
                subprocess.run(["xdg-open", str(Path(self.final_output_path).parent)], check=True)
        except Exception as e:
            self.log_verbose(f"ERROR: Could not open output folder: {e}")

    def delete_scraped_file(self, filepath):
        try:
            os.remove(filepath)
            self.log_verbose(f"Deleted file: {filepath}")
        except Exception as e:
            self.log_verbose(f"ERROR: Could not delete file {filepath}: {e}")

    def remove_local_file_from_package(self, rel_path):
        self.local_files_to_exclude.add(rel_path)
        self.log_verbose(f"Will exclude from package: {rel_path}")

    def start_local_file_scan(self):
        if self.local_scan_future and not self.local_scan_future.done():
            if self.local_scan_cancel_event:
                self.local_scan_cancel_event.set()
        self.local_scan_cancel_event = threading.Event()
        input_dir = self.main_panel.local_dir_ctrl.text()
        if not input_dir or not Path(input_dir).is_dir():
            self.main_panel.populate_local_file_list([])
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.main_panel.local_panel.setEnabled(False)
        self.local_files_to_exclude.clear()
        self.local_depth_excludes.clear()
        custom_excludes = [p.strip() for p in self.main_panel.local_exclude_ctrl.toPlainText().splitlines() if p.strip()]
        binary_excludes = BINARY_FILE_PATTERNS if self.main_panel.hide_binaries_check.isChecked() else []
        args = (input_dir, self.main_panel.dir_level_ctrl.value(), self.main_panel.use_gitignore_check.isChecked(), custom_excludes, binary_excludes, self.local_scan_cancel_event, self.gitignore_cache)

        # Submit task to ThreadPoolExecutor
        self.local_scan_future = self.executor.submit(self._local_scan_worker, *args)

    def _local_scan_worker(self, *args):
        cancel_event = args[5]  # The cancel_event is the 6th argument
        try:
            results = actions.get_local_files(*args)
            if not cancel_event.is_set() and not self.shutdown_event.is_set():
                scan_msg = LocalScanCompleteMessage(results=results)
                self.signals.message.emit(message_to_dict(scan_msg))
        except Exception as e:
            if not self.shutdown_event.is_set():
                error_msg = LogMessage(message=f"ERROR scanning directory: {e}")
                self.signals.message.emit(message_to_dict(error_msg))
        finally:
            if cancel_event.is_set() and not self.shutdown_event.is_set():  # If cancelled, still unlock UI
                scan_msg = LocalScanCompleteMessage(results=None)
                self.signals.message.emit(message_to_dict(scan_msg))

    def on_show_about_dialog(self, event):
        dialog = AboutDialog(self, self.version)
        dialog.exec()


if __name__ == "__main__":
    multiprocessing.freeze_support()

    if platform.system() == "Windows":
        try:
            # Set the DPI awareness context to Per_Monitor_Aware_V2.
            # This is the level Qt6 expects and prevents a conflict with the PyInstaller bootloader.
            # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
            ctypes.windll.shcore.SetProcessDpiAwarenessContext(-4)
        except (AttributeError, OSError):
            # This function is not available on older versions of Windows.
            pass

    app_data_dir = get_app_data_dir()
    log_dir = app_data_dir / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    frame = App()
    sys.exit(app.exec())

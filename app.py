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

from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtGui import QIcon

from ui.main_window import MainWindow, AboutDialog
import core.actions as actions
from core.packager import resource_path
from core.version import __version__
from core.config_manager import get_config, save_config
from core.task_handler import TaskHandler
from core.utils import get_app_data_dir, cleanup_old_directories

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
        self.worker_thread = None
        self.is_shutting_down = False
        self.is_task_running = False
        self.local_files_to_exclude = set()
        self.local_depth_excludes = set()
        self.gitignore_cache = {}
        self.local_scan_worker = None
        self.local_scan_cancel_event = None

        self.signals = WorkerSignals()
        self.signals.message.connect(self._process_log_queue_message)

        self.main_panel = MainWindow(self)
        self.setCentralWidget(self.main_panel)
        self._set_icon()

        self.queue_listener_thread = None
        self.scraped_files_batch = []
        self.batch_update_timer = QTimer(self)
        self.batch_update_timer.setInterval(250)
        self.batch_update_timer.setSingleShot(True)
        self.batch_update_timer.timeout.connect(self.on_batch_update_timer)

        self.exclude_update_timer = QTimer(self)
        self.exclude_update_timer.setInterval(500)
        self.exclude_update_timer.setSingleShot(True)
        self.exclude_update_timer.timeout.connect(self.start_local_file_scan)

        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.setInterval(1000)
        self.ui_update_timer.timeout.connect(self._update_timestamp_label)
        self.ui_update_timer.start()

        self.toggle_input_mode()
        self.show()

    def _setup_app_dirs_and_cleanup(self):
        app_data_dir = get_app_data_dir()
        cache_dir = app_data_dir / "Cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            cleanup_old_directories(cache_dir, 21)
        except Exception as e:
            print(f"Warning: Failed to clean up old cache files: {e}")

    def start_queue_listener(self):
        if self.queue_listener_thread is None:
            self.queue_listener_thread = threading.Thread(target=self._queue_listener_worker, daemon=True)
            self.queue_listener_thread.start()

    def stop_queue_listener(self):
        if self.queue_listener_thread is not None:
            self.log_queue.put(None)
            self.queue_listener_thread.join(timeout=1)
            self.queue_listener_thread = None

    def _queue_listener_worker(self):
        while True:
            try:
                msg_obj = self.log_queue.get()
                if msg_obj is None:
                    break
                self.signals.message.emit(msg_obj)
            except Exception:
                continue

    def _process_log_queue_message(self, msg_obj):
        msg_type = msg_obj.get("type")
        if msg_type == "log":
            self.log_verbose(msg_obj.get("message", ""))
        elif msg_type == "file_saved":
            self.scraped_files_batch.append(msg_obj)
            if not self.batch_update_timer.isActive():
                self.batch_update_timer.start()
            self.main_panel.update_discovered_count(msg_obj.get("queue_size", 0))
            verbose_msg = f"  -> Saved: {msg_obj['filename']} [{msg_obj['pages_saved']}/{msg_obj['max_pages']}]"
            self.log_verbose(verbose_msg)
        elif msg_type == "progress":
            self.main_panel.progress_gauge.setValue(msg_obj["value"])
            self.main_panel.progress_gauge.setMaximum(msg_obj["max_value"])
        elif msg_type == "status":
            self.task_handler.handle_status(msg_obj.get("status"), msg_obj)
        elif msg_type == "local_scan_complete":
            QApplication.restoreOverrideCursor()
            self.main_panel.local_panel.setEnabled(True)
            self.local_scan_worker = None
            results = msg_obj.get("results")
            if results is not None:
                files, depth_excludes = results
                self.main_panel.populate_local_file_list(files)
                self.local_depth_excludes = depth_excludes
        else:
            self.log_verbose(str(msg_obj.get("message", "")))

    def on_batch_update_timer(self):
        if self.scraped_files_batch:
            self.main_panel.add_scraped_files_batch(self.scraped_files_batch)
            self.scraped_files_batch.clear()
            self._update_button_states()

    def _set_icon(self):
        icon_path = resource_path("assets/icons/ContextPacker.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def closeEvent(self, event):
        config["window_size"] = [self.width(), self.height()]
        sash_qba = self.main_panel.splitter.saveState().toBase64()
        config["sash_state"] = str(sash_qba, "utf-8")  # type: ignore
        save_config(config)

        self.stop_queue_listener()

        if self.local_scan_worker and self.local_scan_worker.is_alive():
            if self.local_scan_cancel_event:
                self.local_scan_cancel_event.set()
            self.local_scan_worker.join(timeout=1.0)

        if self.worker_thread and self.worker_thread.is_alive():
            if not self.is_shutting_down:
                self.is_shutting_down = True
                self.log_verbose("Shutdown requested. Waiting for task to terminate...")
                if self.cancel_event:
                    self.cancel_event.set()
                self._toggle_ui_controls(False)
            event.ignore()
            return
        event.accept()

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
        self.main_panel.verbose_log_ctrl.append(message)

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
        if self.local_scan_worker and self.local_scan_worker.is_alive():
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
        self.local_scan_worker = threading.Thread(target=self._local_scan_worker, args=args, daemon=True)
        self.local_scan_worker.start()

    def _local_scan_worker(self, *args):
        cancel_event = args[5]  # The cancel_event is the 6th argument
        try:
            results = actions.get_local_files(*args)
            if not cancel_event.is_set():
                self.signals.message.emit({"type": "local_scan_complete", "results": results})
        except Exception as e:
            self.signals.message.emit({"type": "log", "message": f"ERROR scanning directory: {e}"})
        finally:
            if cancel_event.is_set():  # If cancelled, still unlock UI
                self.signals.message.emit({"type": "local_scan_complete", "results": None})

    def on_show_about_dialog(self, event):
        dialog = AboutDialog(self, self.version)
        dialog.exec()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    app_data_dir = get_app_data_dir()
    log_dir = app_data_dir / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    frame = App()
    sys.exit(app.exec())

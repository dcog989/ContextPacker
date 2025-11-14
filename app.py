import os
import platform
import subprocess
import sys
import ctypes
import shutil
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon, QFontDatabase
from ui.main_window import MainWindow
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
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
)
from core.app_signals import WorkerSignals
from core.app_worker_manager import WorkerManager
from core.app_message_handler import MessageHandler
from core.app_ui_controller import UiController
from core.state_manager import StateManager
from core.theme_manager import ThemeManager

config = get_config()
BINARY_FILE_PATTERNS = config.get("binary_file_patterns", [])


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self._is_closing = False
        self.shutdown_check_timer = None
        self.Path = Path

        w, h = config.get("window_size", [-1, -1])
        if w > 0 and h > 0:
            self.resize(w, h)
        else:
            self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setWindowTitle("ContextPacker")

        # Core State & Managers
        self.version = __version__
        self.state = StateManager()

        self.max_batch_size = MAX_BATCH_SIZE
        self.ui_update_batch_size = UI_UPDATE_BATCH_SIZE
        self.BINARY_FILE_PATTERNS = BINARY_FILE_PATTERNS

        # Initialize Services
        self.worker_manager = WorkerManager(self)
        self.shutdown_event = self.worker_manager.shutdown_event
        self.log_queue = self.worker_manager.log_queue
        self.executor = self.worker_manager.executor
        self.signals = WorkerSignals()
        self.message_handler = MessageHandler(self)
        self.task_handler = TaskHandler(self)
        self.ui_controller = UiController(self)
        self.log_message_batch = []

        self._setup_app_dirs_and_cleanup()

        self.signals.message.connect(self.message_handler.process_log_queue_message)

        self.main_panel = MainWindow(self)
        self.setCentralWidget(self.main_panel)

        self.theme_manager = ThemeManager(self)
        self._load_custom_font()
        self.theme_manager.apply_theme()
        self._set_icon()

        # Timers
        self.log_update_timer = QTimer(self)
        self.log_update_timer.setInterval(100)
        self.log_update_timer.timeout.connect(lambda: self._process_log_batch())
        self.log_update_timer.start()

        self.batch_update_timer = QTimer(self)
        self.batch_update_timer.setInterval(BATCH_UPDATE_INTERVAL_MS)
        self.batch_update_timer.timeout.connect(lambda: self.ui_controller.on_batch_update_timer())
        self.batch_update_timer.start()

        self.exclude_update_timer = QTimer(self)
        self.exclude_update_timer.setInterval(EXCLUDE_UPDATE_INTERVAL_MS)
        self.exclude_update_timer.setSingleShot(True)
        self.exclude_update_timer.timeout.connect(self.ui_controller.start_local_file_scan)

        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.setInterval(UI_UPDATE_INTERVAL_MS)
        self.ui_update_timer.timeout.connect(self.ui_controller._update_timestamp_label)
        self.ui_update_timer.start()

        self.ui_controller.toggle_input_mode()
        self.show()

    def _load_custom_font(self):
        font_files = [
            "assets/fonts/SourceCodePro-VariableFont_wght.ttf",
            "assets/fonts/SourceCodePro-Italic-VariableFont_wght.ttf",
        ]
        for font_file in font_files:
            font_path = resource_path(font_file)
            if font_path.exists():
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                if font_id == -1:
                    print(f"Warning: Failed to load font from {font_path}")

    def _setup_app_dirs_and_cleanup(self):
        app_data_dir = get_app_data_dir()
        cache_dir = app_data_dir / "Cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            days_threshold = config.get("max_age_logs", 21)
            cleanup_old_directories(cache_dir, days_threshold)
        except Exception as e:
            print(f"Warning: Failed to clean up old cache files: {e}")

    def _set_icon(self):
        icon_path = resource_path("assets/icons/ContextPacker.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _toggle_ui_controls(self, enable=True, widget_to_keep_enabled=None):
        print(f"[DIAG] _toggle_ui_controls: Setting enabled state to {enable}")
        widgets_to_toggle = [
            self.main_panel.system_panel,
            self.main_panel.web_crawl_radio,
            self.main_panel.local_dir_radio,
            self.main_panel.crawler_panel,
            self.main_panel.local_panel,
            self.main_panel.output_filename_ctrl,
            self.main_panel.output_format_choice,
            self.main_panel.package_button,
            self.main_panel.download_button,
            self.main_panel.delete_button,
            self.main_panel.theme_switch_button,
        ]
        for widget in widgets_to_toggle:
            if widget is not widget_to_keep_enabled:
                widget.setEnabled(enable)
        if not enable and widget_to_keep_enabled:
            widget_to_keep_enabled.setEnabled(True)
        print(f"[DIAG] _toggle_ui_controls: Finished setting state to {enable}")

    def _update_button_states(self):
        print("[DIAG] App._update_button_states: Calling controller.")
        self.ui_controller._update_button_states()

    def log_verbose(self, message):
        if self._is_closing or self.shutdown_event.is_set():
            return

        if "[DIAG]" in message:
            print(message)

        self.log_message_batch.append(message)

    def _process_log_batch(self):
        if not self.log_message_batch:
            return

        if "[DIAG]" in self.log_message_batch[0]:
            print(f"[DIAG] _process_log_batch: Entered for {len(self.log_message_batch)} messages.")

        if self._is_closing or self.shutdown_event.is_set() or not hasattr(self, "main_panel") or not self.main_panel:
            self.log_message_batch.clear()
            return

        try:
            log_widget = self.main_panel.verbose_log_widget
            messages_to_process = "\n".join(self.log_message_batch)
            self.log_message_batch.clear()

            log_widget.setUpdatesEnabled(False)
            log_widget.blockSignals(True)

            self.main_panel._manage_log_size()
            log_widget.append(messages_to_process)

        except RuntimeError:
            pass
        finally:
            try:
                if hasattr(self, "main_panel") and self.main_panel:
                    log_widget = self.main_panel.verbose_log_widget
                    log_widget.blockSignals(False)
                    log_widget.setUpdatesEnabled(True)
            except (RuntimeError, AttributeError):
                pass

    def delete_scraped_file(self, filepath):
        try:
            os.remove(filepath)
            self.log_verbose(f"Deleted file: {filepath}")
        except Exception as e:
            self.log_verbose(f"ERROR: Could not delete file {filepath}: {e}")

    def remove_local_file_from_package(self, rel_path):
        self.state.local_files_to_exclude.add(rel_path)
        self.log_verbose(f"Deleted from package: {rel_path}")

    def _open_output_folder_blocking_task(self, output_dir_path):
        try:
            if platform.system() == "Windows":
                os.startfile(output_dir_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(output_dir_path)], check=True)
            else:
                subprocess.run(["xdg-open", str(output_dir_path)], check=True)
        except Exception as e:
            self.log_verbose(f"ERROR: Could not open output folder: {e}")

    def _open_output_folder(self):
        if self.state.final_output_path and self.Path(self.state.final_output_path).exists():
            output_dir = self.Path(self.state.final_output_path).parent
            self.worker_manager.executor.submit(self._open_output_folder_blocking_task, output_dir)
        else:
            self.log_verbose("ERROR: No output file found to locate.")

    def closeEvent(self, event):
        if not self._is_closing:
            self._is_closing = True
            self.shutdown_event.set()
            self.hide()

            self.batch_update_timer.stop()
            self.exclude_update_timer.stop()
            self.ui_update_timer.stop()
            self.log_update_timer.stop()

            try:
                self.signals.message.disconnect()
            except (RuntimeError, TypeError):
                pass

            self.worker_manager.stop_queue_listener(timeout=1.0)

            config["window_size"] = [self.width(), self.height()]
            h_sash_qba = self.main_panel.h_splitter.saveState().toBase64()
            v_sash_qba = self.main_panel.v_splitter.saveState().toBase64()
            config["h_sash_state"] = bytes(h_sash_qba.data()).decode("utf-8")
            config["v_sash_state"] = bytes(v_sash_qba.data()).decode("utf-8")
            save_config(config)

            if self.state.temp_dir and self.Path(self.state.temp_dir).is_dir():
                try:
                    shutil.rmtree(self.state.temp_dir)
                except Exception:
                    pass

            if self.state.cancel_event and not self.state.cancel_event.is_set():
                self.state.cancel_event.set()
            if self.state.local_scan_cancel_event and not self.state.local_scan_cancel_event.is_set():
                self.state.local_scan_cancel_event.set()

        if self.worker_manager.cleanup_workers():
            if not self.shutdown_check_timer:
                self.shutdown_check_timer = QTimer(self)
                self.shutdown_check_timer.setInterval(100)
                self.shutdown_check_timer.timeout.connect(self.close)
                self.shutdown_check_timer.start()
            event.ignore()
            return

        if self.shutdown_check_timer:
            self.shutdown_check_timer.stop()

        self.worker_manager.executor.shutdown(wait=False, cancel_futures=True)
        event.accept()


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()

    try:
        if platform.system() == "Windows":
            try:
                ctypes.windll.shcore.SetProcessDpiAwarenessContext(-4)
            except (AttributeError, OSError):
                pass

        app_data_dir = get_app_data_dir()
        log_dir = app_data_dir / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        app = QApplication(sys.argv)
        frame = App()
        sys.exit(app.exec())
    except Exception:
        sys.exit(1)

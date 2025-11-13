import os
import platform
import subprocess
import sys
import ctypes
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
        # Use Path from pathlib to avoid re-importing in every method
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

        # Constants used by MessageHandler
        self.max_batch_size = MAX_BATCH_SIZE
        self.ui_update_batch_size = UI_UPDATE_BATCH_SIZE
        self.BINARY_FILE_PATTERNS = BINARY_FILE_PATTERNS

        # Initialize Services
        self.worker_manager = WorkerManager(self)
        self.shutdown_event = self.worker_manager.shutdown_event  # Alias for easier access
        self.log_queue = self.worker_manager.log_queue
        self.executor = self.worker_manager.executor
        self.signals = WorkerSignals()
        self.message_handler = MessageHandler(self)
        self.task_handler = TaskHandler(self)
        self.ui_controller = UiController(self)

        self._setup_app_dirs_and_cleanup()

        # Connect Signals
        self.signals.message.connect(self.message_handler.process_log_queue_message)

        # UI Setup
        self.main_panel = MainWindow(self)
        self.setCentralWidget(self.main_panel)

        # Theme Manager (must be after main_panel is created)
        self.theme_manager = ThemeManager(self)

        self._load_custom_font()
        self.theme_manager.apply_theme()
        self._set_icon()

        # Timers
        self.batch_update_timer = QTimer(self)
        self.batch_update_timer.setInterval(BATCH_UPDATE_INTERVAL_MS)
        self.batch_update_timer.timeout.connect(self.ui_controller.on_batch_update_timer)
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

    def _set_icon(self):
        icon_path = resource_path("assets/icons/ContextPacker.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _toggle_ui_controls(self, enable=True, widget_to_keep_enabled=None):
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

    def _update_button_states(self):
        self.ui_controller._update_button_states()

    def log_verbose(self, message):
        # Check if we need to trim the log before adding new content
        self.main_panel._manage_log_size()

        self.main_panel.verbose_log_widget.append(message)

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
        """Blocking task to open the output folder in the OS."""
        try:
            if platform.system() == "Windows":
                os.startfile(output_dir_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(output_dir_path)], check=True)
            else:  # Linux and other Unix-like
                subprocess.run(["xdg-open", str(output_dir_path)], check=True)
        except Exception as e:
            self.log_verbose(f"ERROR: Could not open output folder: {e}")

    def _open_output_folder(self):
        """Opens the folder containing the final output file."""
        if self.state.final_output_path and self.Path(self.state.final_output_path).exists():
            output_dir = self.Path(self.state.final_output_path).parent
            # Submit the blocking task to the thread pool to prevent UI hang
            self.worker_manager.executor.submit(self._open_output_folder_blocking_task, output_dir)
        else:
            self.log_verbose("ERROR: No output file found to locate.")

    # --- Shutdown/Cleanup Methods ---
    def closeEvent(self, event):
        config["window_size"] = [self.width(), self.height()]
        h_sash_qba = self.main_panel.h_splitter.saveState().toBase64()
        v_sash_qba = self.main_panel.v_splitter.saveState().toBase64()
        config["h_sash_state"] = bytes(h_sash_qba.data()).decode("utf-8")
        config["v_sash_state"] = bytes(v_sash_qba.data()).decode("utf-8")
        save_config(config)

        # FIXED: Correct shutdown order - cancel workers BEFORE setting shutdown event
        # 1. Cancel any running tasks first
        if self.state.cancel_event:
            self.state.cancel_event.set()
        if self.state.local_scan_cancel_event:
            self.state.local_scan_cancel_event.set()

        # 2. Check if workers need time to stop gracefully
        workers_need_cleanup = self.worker_manager.cleanup_workers()
        if workers_need_cleanup:
            # Workers are still running, defer close
            event.ignore()
            return

        # 3. NOW set global shutdown event (after workers stopped)
        self.worker_manager.shutdown_event.set()

        # 4. Shutdown executor non-blocking
        self.worker_manager.executor.shutdown(wait=False)

        # 5. Disconnect signals
        try:
            self.signals.message.disconnect()
        except RuntimeError:
            pass

        # 6. Stop queue listener thread with timeout
        queue_stopped = self.worker_manager.stop_queue_listener(timeout=5.0)
        if not queue_stopped:
            print("Warning: Queue listener did not stop cleanly")

        event.accept()


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()

    try:
        if platform.system() == "Windows":
            try:
                # Set the DPI awareness context to Per_Monitor_Aware_V2.
                ctypes.windll.shcore.SetProcessDpiAwarenessContext(-4)
            except (AttributeError, OSError):
                pass

        app_data_dir = get_app_data_dir()
        log_dir = app_data_dir / "Logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        app = QApplication(sys.argv)
        frame = App()
        sys.exit(app.exec())
    except Exception as e:
        import traceback

        print("--- CONTEXTPACKER FATAL ERROR ---")
        print(f"Exception: {e}")
        print("Traceback:")
        traceback.print_exc()
        print("---------------------------------")
        sys.exit(1)

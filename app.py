import os
from pathlib import Path
import ctypes
import subprocess
import platform
import multiprocessing
import sys

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QIcon, QFontDatabase, QPalette, QColor

from ui.main_window import MainWindow
from ui.styles import AppTheme
from core.version import __version__
from core.config_manager import get_config, save_config
from core.task_handler import TaskHandler
from core.utils import get_app_data_dir, cleanup_old_directories, resource_path, set_title_bar_theme
from core.constants import (
    BATCH_UPDATE_INTERVAL_MS,
    EXCLUDE_UPDATE_INTERVAL_MS,
    UI_UPDATE_INTERVAL_MS,
    MAX_BATCH_SIZE,
    UI_UPDATE_BATCH_SIZE,
)

from core.app_signals import WorkerSignals
from core.app_worker_manager import WorkerManager
from core.app_message_handler import MessageHandler
from core.app_ui_controller import UiController

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
            self.resize(1600, 950)
        self.setWindowTitle("ContextPacker")

        # Core State & Managers
        self.version = __version__
        self.is_task_running = False
        self.temp_dir = None
        self.final_output_path = None
        self.local_files_to_exclude = set()
        self.local_depth_excludes = set()
        self.gitignore_cache = {}
        self.worker_future = None
        self.cancel_event = None
        self.local_scan_future = None
        self.local_scan_cancel_event = None

        # Constants used by MessageHandler (moved here for central definition)
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
        self.task_handler = TaskHandler(self)  # Still uses a mix of internal App logic and external TaskHandler
        self.ui_controller = UiController(self)

        # Theme State (Visual only, to choose correct icon)
        self.is_dark_mode_visual_state = self._check_if_system_is_dark()

        self._setup_app_dirs_and_cleanup()

        # Connect Signals
        self.signals.message.connect(self.message_handler.process_log_queue_message)

        # UI Setup
        self.main_panel = MainWindow(self)
        self.setCentralWidget(self.main_panel)

        self._load_custom_font()
        self._apply_theme()  # Apply theme, relies on theme state
        self._set_icon()

        # CORRECTED CALL: Theme icon updates are methods on App
        self._update_theme_icon()
        self._update_copy_icon(self.is_dark_mode_visual_state)

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

    # --- Theme & Utility Methods ---

    def _check_if_system_is_dark(self):
        """Checks if the system/Qt palette is currently in a dark mode."""
        app = QApplication.instance()
        if not app or not isinstance(app, QApplication):
            return False
        # A simple check: if the window background is closer to black than white
        return app.palette().color(QPalette.ColorRole.Window).lightnessF() < 0.5

    def _apply_theme(self):
        """Applies the base stylesheet and platform-specific hints, relying on Qt's built-in palette."""
        is_dark = self.is_dark_mode_visual_state
        app = QApplication.instance()
        if not app or not isinstance(app, QApplication):
            return

        # 1. Force the PySide6 palette to switch using the saved visual state
        palette = app.palette()
        if is_dark:
            # Dark Mode Palette (Setting basic dark colors)
            palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(224, 224, 224))
            palette.setColor(QPalette.ColorRole.Base, QColor(43, 43, 43))
            palette.setColor(QPalette.ColorRole.Text, QColor(224, 224, 224))
            palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(224, 224, 224))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(46, 139, 87))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        else:
            # Light Mode Palette (Reset to default system/light palette)
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(46, 139, 87))
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)

        app.setPalette(palette)

        # 2. Apply the custom stylesheet for accent colors and component specifics
        theme = AppTheme()
        app.setStyleSheet(theme.get_stylesheet())

        # 3. Update Windows title bar theme (only if running on Windows)
        set_title_bar_theme(self, is_dark)

        # 4. Update dynamic icons
        self._update_theme_icon(initial_load=False)
        self._update_copy_icon(is_dark)

    def _update_theme_icon(self, initial_load=False):
        """Updates the icon of the theme switch button based on the current visual state."""
        if not hasattr(self, "main_panel") or not self.main_panel:
            return

        is_currently_dark = self.is_dark_mode_visual_state

        # For the theme button, if the current visual state is dark, the action is to switch to light,
        # so we show the light paint bucket icon.
        if is_currently_dark:
            icon_path = resource_path("assets/icons/paint-bucket-light.png")
            tooltip = "Current: Dark (Click to switch to Light Mode)"
        else:
            icon_path = resource_path("assets/icons/paint-bucket-dark.png")
            tooltip = "Current: Light (Click to switch to Dark Mode)"

        self.main_panel.theme_switch_button.setIcon(QIcon(str(icon_path)))
        self.main_panel.theme_switch_button.setToolTip(tooltip)

    def _update_copy_icon(self, is_dark):
        """Updates the icon of the copy button based on the current mode."""
        if not hasattr(self, "main_panel") or not self.main_panel:
            return

        if is_dark:
            icon_path = resource_path("assets/icons/copy-light.png")
        else:
            icon_path = resource_path("assets/icons/copy-dark.png")

        self.main_panel.copy_button.setIcon(QIcon(str(icon_path)))

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
        # Count lines in the message (handle multi-line messages)
        lines_in_message = message.count("\n") + 1
        self.main_panel.log_line_count += lines_in_message

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
        self.local_files_to_exclude.add(rel_path)
        self.log_verbose(f"Deleted from package: {rel_path}")

    def _open_output_folder(self):
        """Opens the folder containing the final output file."""
        if self.final_output_path and self.Path(self.final_output_path).exists():
            output_dir = self.Path(self.final_output_path).parent
            try:
                if platform.system() == "Windows":
                    os.startfile(output_dir)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(output_dir)])
                else:  # Linux and other Unix-like
                    subprocess.run(["xdg-open", str(output_dir)])
            except Exception as e:
                self.log_verbose(f"ERROR: Could not open output folder: {e}")
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

        # 1. Set global shutdown event
        self.worker_manager.shutdown_event.set()

        # 2. Shutdown executor non-blocking
        self.worker_manager.executor.shutdown(wait=False)

        # 3. Disconnect signals
        try:
            self.signals.message.disconnect()
        except RuntimeError:
            pass

        # 4. Stop queue listener thread
        queue_stopped = self.worker_manager.stop_queue_listener(timeout=5.0)
        if not queue_stopped:
            print("Warning: Queue listener did not stop cleanly")

        # 5. Check if any worker is still running
        if self.worker_manager.cleanup_workers():
            event.ignore()
            return

        event.accept()


if __name__ == "__main__":
    multiprocessing.freeze_support()

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

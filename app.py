import sys
import platform
import ctypes
import shutil
from pathlib import Path
import logging
import threading
from PySide6.QtWidgets import QApplication, QMainWindow, QStyle
from PySide6.QtGui import QIcon, QFontDatabase
from PySide6.QtCore import Qt, QCoreApplication

from core.utils import get_app_data_dir, cleanup_old_directories, resource_path
from core.constants import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
from core.config_service import ConfigService
from core.state_service import StateService
from core.task_service import TaskService
from core.app_ui_controller import UiController
from core.theme_manager import ThemeManager
from core.logger_setup import setup_logging
from core.signals import app_signals
from ui.main_window import MainWindow


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ContextPacker")
        self._first_show = True
        self._is_shutting_down = False

        # --- Service Initialization ---
        self.config_service = ConfigService()
        self.state_service = StateService()
        self.task_service = TaskService()

        # --- Logging Setup ---
        log_level = self.config_service.get("logging_level", "INFO")
        if not isinstance(log_level, str):
            log_level = "INFO"

        log_max_size = self.config_service.get("log_max_size_mb", 5)
        if not isinstance(log_max_size, int) or log_max_size <= 0:
            log_max_size = 5

        log_backup_count = self.config_service.get("log_backup_count", 3)
        if not isinstance(log_backup_count, int) or log_backup_count < 0:
            log_backup_count = 3

        self.log_emitter = setup_logging(log_level, log_max_size, log_backup_count)
        logging.debug(f"[{threading.current_thread().name}] App initialized.")

        # --- UI Initialization ---
        self.main_panel = MainWindow(self.config_service)
        self.setCentralWidget(self.main_panel)

        # --- Theme and Style ---
        self.theme_manager = ThemeManager(self)
        self._load_custom_font()
        self.theme_manager.apply_theme()
        self._set_icon()

        # --- UI Controller Initialization (The Glue) ---
        self.ui_controller = UiController(
            main_window=self.main_panel,
            state_service=self.state_service,
            task_service=self.task_service,
            config_service=self.config_service,
            theme_manager=self.theme_manager,
        )
        self.ui_controller.setup_connections()
        self.ui_controller.connect_log_emitter(self.log_emitter)

        # --- Shutdown Signal ---
        app_signals.task_shutdown_finished.connect(self.on_shutdown_finished)

        # --- Window Setup ---
        self._setup_window()
        self._setup_app_dirs_and_cleanup()
        self.show()

    def __del__(self):
        logging.debug(f"[{threading.current_thread().name}] App object being destroyed.")

    def on_shutdown_finished(self):
        """Called when the TaskService confirms all background threads are stopped."""
        logging.debug(f"[{threading.current_thread().name}] Received shutdown finished signal. Quitting application.")
        QCoreApplication.quit()

    def showEvent(self, event):
        """
        This is the correct and only reliable place to perform window centering
        on the first launch. It is called after the window is created but just
        before it is shown, ensuring all geometry is stable.
        """
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            window_pos = self.config_service.get("window_pos", [-1, -1])
            if not (isinstance(window_pos, list) and len(window_pos) == 2 and window_pos[0] >= 0):
                if self.screen():
                    self.setGeometry(
                        QStyle.alignedRect(
                            Qt.LayoutDirection.LeftToRight,
                            Qt.AlignmentFlag.AlignCenter,
                            self.size(),
                            self.screen().availableGeometry(),
                        )
                    )

    def _load_custom_font(self):
        font_files = [
            "assets/fonts/SourceCodePro-VariableFont_wght.ttf",
            "assets/fonts/SourceCodePro-Italic-VariableFont_wght.ttf",
        ]
        for font_file in font_files:
            font_path = resource_path(font_file)
            if font_path.exists():
                QFontDatabase.addApplicationFont(str(font_path))

    def _setup_app_dirs_and_cleanup(self):
        app_data_dir = get_app_data_dir()
        cache_dir = app_data_dir / "Cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            days_threshold = self.config_service.get("max_age_cache_days", 7)
            cleanup_old_directories(cache_dir, days_threshold)
        except Exception as e:
            print(f"Warning: Failed to clean up old cache files: {e}")

    def _set_icon(self):
        icon_path = resource_path("assets/icons/ContextPacker.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _setup_window(self):
        window_size = self.config_service.get("window_size", [-1, -1])
        if isinstance(window_size, list) and len(window_size) == 2 and window_size[0] > 0:
            self.resize(*window_size)
        else:
            self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

        window_pos = self.config_service.get("window_pos", [-1, -1])
        if isinstance(window_pos, list) and len(window_pos) == 2 and window_pos[0] >= 0:
            self.move(*window_pos)

    def closeEvent(self, event):
        """Gracefully shut down the application."""
        if self._is_shutting_down:
            logging.debug(f"[{threading.current_thread().name}] closeEvent: Already shutting down, ignoring.")
            event.ignore()
            return

        logging.debug(f"[{threading.current_thread().name}] closeEvent: Starting shutdown sequence.")
        self._is_shutting_down = True

        self.ui_controller.cleanup()
        self.config_service.save_window_state(self.size(), self.pos(), self.main_panel.h_splitter.saveState(), self.main_panel.v_splitter.saveState())
        if self.state_service.temp_dir and Path(self.state_service.temp_dir).is_dir():
            shutil.rmtree(self.state_service.temp_dir, ignore_errors=True)

        self.hide()
        self.task_service.shutdown()

        event.ignore()


def main():
    """Main application entry point."""
    if platform.system() == "Windows":
        try:
            ctypes.windll.shcore.SetProcessDpiAwarenessContext(-4)
        except (AttributeError, OSError):
            pass

    app = QApplication(sys.argv)
    # The App instance MUST be assigned to a variable to prevent it from being
    # garbage collected immediately. Using `_window` signals intent that the
    # variable is intentionally not used elsewhere.
    _window = App()
    sys.exit(app.exec())


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    main()

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, QSize

from ui.styles import AppTheme
from core.utils import resource_path, set_title_bar_theme, get_app_data_dir
from core.icon_utils import create_themed_svg_icon


class ThemeManager:
    """Manages the application's theme, styles, and dynamic icons."""

    def __init__(self, app_instance):
        self.app = app_instance
        self.main_panel = self.app.main_panel
        self._setup_icons_dir()
        self.is_dark_mode_visual_state = self._check_if_system_is_dark()

    def _setup_icons_dir(self):
        """Creates and stores the path to the persistent icons directory."""
        app_data_dir = get_app_data_dir()
        self.icons_dir_path = app_data_dir / "icons"
        self.icons_dir_path.mkdir(parents=True, exist_ok=True)

    def _check_if_system_is_dark(self) -> bool:
        """Checks if the system/Qt palette is currently in a dark mode."""
        app = QApplication.instance()
        if not app or not isinstance(app, QApplication):
            return False
        # A simple check: if the window background is closer to black than white
        return app.palette().color(QPalette.ColorRole.Window).lightnessF() < 0.5

    def apply_theme(self):
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
        theme = AppTheme(is_dark=is_dark, icons_dir_path=self.icons_dir_path)
        app.setStyleSheet(theme.get_stylesheet())

        # 3. Update Windows title bar theme (only if running on Windows)
        set_title_bar_theme(self.app, is_dark)

        # 4. Update dynamic icons
        self.update_theme_icon()
        self.update_copy_icon()

    def update_theme_icon(self):
        """Updates the icon of the theme switch button based on the current visual state."""
        if not hasattr(self, "main_panel") or not self.main_panel:
            return

        icon = create_themed_svg_icon(
            resource_path("assets/icons/paint-bucket.svg"),
            self.app.palette().color(QPalette.ColorRole.Text).name(),
            QSize(20, 20),
        )
        self.main_panel.theme_switch_button.setIcon(icon)

        is_currently_dark = self.is_dark_mode_visual_state
        if is_currently_dark:
            tooltip = "Current: Dark (Click to switch to Light Mode)"
        else:
            tooltip = "Current: Light (Click to switch to Dark Mode)"
        self.main_panel.theme_switch_button.setToolTip(tooltip)

    def update_copy_icon(self):
        """Updates the icon of the copy button based on the current mode."""
        if not hasattr(self, "main_panel") or not self.main_panel:
            return

        icon = create_themed_svg_icon(resource_path("assets/icons/copy.svg"), self.app.palette().color(QPalette.ColorRole.Text).name(), QSize(20, 20))
        self.main_panel.copy_button.setIcon(icon)

    def toggle_theme(self):
        """Toggles the theme and applies changes."""
        self.is_dark_mode_visual_state = not self.is_dark_mode_visual_state
        self.apply_theme()

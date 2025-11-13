import os
from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt


class AppTheme:
    def __init__(self, is_dark=True):
        self.is_dark = is_dark
        self.accent_color = "#2E8B57"  # Darker green from logo
        self.accent_color_lighter = "#3CB371"  # Lighter green from logo
        self.accent_color_darker = "#153E27"  # Darker green

        if is_dark:
            # Dark theme colors
            self.bg_primary = "#2B2B2B"
            self.bg_secondary = "#3A3A3A"
            self.bg_tertiary = "#404040"
            self.bg_button = "#404040"
            self.bg_button_hover = "#4A4A4A"
            self.bg_button_pressed = "#353535"
            self.bg_button_disabled = "#2A2A2A"
            self.border_color = "#555555"
            self.border_hover = "#666666"
            self.border_pressed = "#444444"
            self.border_disabled = "#3A3A3A"
            self.text_color = "#D0D0D0"
            self.text_hover = "#E0E0E0"
            self.text_disabled = "#666666"
            self.spinbox_button_bg = "#4A4A4A"
            self.spinbox_button_hover = "#5A5A5A"
            self.spinbox_button_pressed = "#3A3A3A"
        else:
            # Light theme colors
            self.bg_primary = "#F0F0F0"
            self.bg_secondary = "#FFFFFF"
            self.bg_tertiary = "#E8E8E8"
            self.bg_button = "#F0F0F0"
            self.bg_button_hover = "#E0E0E0"
            self.bg_button_pressed = "#D0D0D0"
            self.bg_button_disabled = "#F5F5F5"
            self.border_color = "#CCCCCC"
            self.border_hover = "#AAAAAA"
            self.border_pressed = "#999999"
            self.border_disabled = "#DDDDDD"
            self.text_color = "#333333"
            self.text_hover = "#222222"
            self.text_disabled = "#999999"
            self.spinbox_button_bg = "#F0F0F0"
            self.spinbox_button_hover = "#E0E0E0"
            self.spinbox_button_pressed = "#D0D0D0"

        # Create checkmark icon and save to temp location
        self._setup_checkbox_icon()

    def _setup_checkbox_icon(self):
        """Creates and saves a checkmark icon for checkboxes."""
        size = 18
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw checkmark with color that works for both themes (white on dark, black on light)
        checkmark_color = QColor(255, 255, 255) if self.is_dark else QColor(0, 0, 0)
        pen = QPen(checkmark_color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # Checkmark path (approximate coordinates for 18x18 icon)
        painter.drawLine(4, 9, 7, 13)
        painter.drawLine(7, 13, 14, 5)

        painter.end()

        # Save to temp directory with theme-specific filename
        from core.utils import get_app_data_dir

        temp_dir = get_app_data_dir() / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        theme_suffix = "_dark" if self.is_dark else "_light"
        self.checkbox_icon_path = temp_dir / f"checkbox_check{theme_suffix}.png"
        pixmap.save(str(self.checkbox_icon_path))

    def get_stylesheet(self):
        # Convert path to use forward slashes for Qt stylesheet
        icon_path = str(self.checkbox_icon_path).replace("\\", "/")

        return f"""
            QWidget {{
                font-size: 13px;
            }}

            /* Splitter styling */
            QSplitter::handle {{
                background-color: #999999;
            }}
            QSplitter::handle:hover {{
                background-color: #A9A9A9;
            }}
            
            /* QGroupBox styling */
            QGroupBox {{
                font-size: 15px;
                font-weight: bold;
                border: 2px solid {self.border_color};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }}
            
            /* System panel app name styling */
            QLabel#AppNameLabel {{
                color: {self.accent_color};
                font-family: "Source Code Pro";
                font-size: 22px;
                font-weight: bold;
            }}
            
            /* Label styling for about dialog quote */
            QLabel#MilkshakeLabel {{
                color: #d581b0;
                font-family: "Source Code Pro";
                font-style: italic;
                font-size: 14px;
                font-weight: 600;
            }}

            /* Style for the verbose log widget */
            QTextEdit#VerboseLog {{
                font-family: "Source Code Pro";
                font-size: 10px;
            }}
            
            /* Input fields - different shade of grey from app background */
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background-color: {self.bg_secondary};
                border: 1px solid {self.border_color};
                border-radius: 3px;
                padding: 6px 8px;
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 1px solid {self.accent_color};
            }}
            
            /* QComboBox dropdown styling */
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.bg_secondary};
                selection-background-color: {self.accent_color};
                border: 1px solid {self.border_color};
                padding: 4px;
            }}
            
            /* QSpinBox buttons - better contrast and visible arrows */
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 18px;
                border: 1px solid {self.border_color};
                background-color: {self.spinbox_button_bg};
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {self.spinbox_button_hover};
                border: 1px solid {self.border_hover};
            }}
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{
                background-color: {self.spinbox_button_pressed};
            }}
            QSpinBox::up-arrow {{
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 7px solid {self.text_color};
            }}
            QSpinBox::down-arrow {{
                width: 0;
                height: 0;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid {self.text_color};
            }}
            QSpinBox::up-arrow:hover {{
                border-bottom-color: {self.text_hover};
            }}
            QSpinBox::down-arrow:hover {{
                border-top-color: {self.text_hover};
            }}
            
            /* Button styling with more padding and darker greys */
            QPushButton {{
                background-color: {self.bg_button};
                border: 1px solid {self.border_color};
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {self.bg_button_hover};
                border: 1px solid {self.border_hover};
            }}
            QPushButton:pressed {{
                background-color: {self.bg_button_pressed};
                border: 1px solid {self.border_pressed};
            }}
            QPushButton:disabled {{
                background-color: {self.bg_button_disabled};
                border: 1px solid {self.border_disabled};
                color: {self.text_disabled};
            }}
            
            /* Primary button styling (Download, Package, Delete) */
            QPushButton#PrimaryButton {{
                background-color: {self.accent_color};
                border: 1px solid {self.accent_color_darker};
                color: white;
                font-weight: bold;
            }}
            QPushButton#PrimaryButton:hover {{
                background-color: {self.accent_color_lighter};
                border: 1px solid {self.accent_color};
            }}
            QPushButton#PrimaryButton:pressed {{
                background-color: {self.accent_color_darker};
                border: 1px solid #0F2515;
            }}
            QPushButton#PrimaryButton:disabled {{
                background-color: #2A4A38;
                border: 1px solid #1F3529;
                color: #6B8F78;
            }}
            
            /* Theme switch button */
            QPushButton#ThemeSwitchButton {{
                background-color: transparent;
                border: 1px solid {self.border_color};
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton#ThemeSwitchButton:hover {{
                background-color: {self.bg_button_hover};
                border: 1px solid {self.border_hover};
            }}
            QPushButton#ThemeSwitchButton:pressed {{
                background-color: {self.bg_button_pressed};
            }}
            
            /* Checkbox styling with custom checkmark */
            QCheckBox {{
                spacing: 8px;
                padding: 4px 0px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {self.border_color};
                border-radius: 3px;
                background-color: {self.bg_secondary};
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid {self.border_hover};
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.accent_color};
                border: 1px solid {self.accent_color_darker};
                image: url({icon_path});
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {self.accent_color_lighter};
            }}
            
            /* Radio button styling */
            QRadioButton {{
                spacing: 8px;
                padding: 4px 0px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {self.border_color};
                border-radius: 9px;
                background-color: {self.bg_secondary};
            }}
            QRadioButton::indicator:hover {{
                border: 1px solid {self.border_hover};
            }}
            QRadioButton::indicator:checked {{
                background-color: {self.accent_color};
                border: 1px solid {self.accent_color_darker};
            }}
            QRadioButton::indicator:checked:hover {{
                background-color: {self.accent_color_lighter};
            }}
            
            /* Label styling */
            QLabel {{
                padding: 2px 0px;
            }}
            
            /* Table widget styling */
            QTableWidget {{
                background-color: {self.bg_secondary};
                border: 1px solid {self.border_color};
                gridline-color: {self.bg_tertiary};
            }}
            QTableWidget::item {{
                padding: 6px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {self.accent_color};
            }}
            QHeaderView::section {{
                background-color: {self.bg_tertiary};
                border: 1px solid {self.border_color};
                padding: 6px 8px;
                font-weight: bold;
            }}
            
            /* Progress bar styling */
            QProgressBar {{
                border: 1px solid {self.border_color};
                border-radius: 3px;
                background-color: {self.bg_secondary};
                text-align: center;
                padding: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {self.accent_color};
                border-radius: 2px;
            }}
            
            /* Scrollbar styling */
            QScrollBar:vertical {{
                background-color: {self.bg_primary};
                width: 14px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.border_color};
                min-height: 30px;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.border_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {self.bg_primary};
                height: 14px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {self.border_color};
                min-width: 30px;
                border-radius: 7px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {self.border_hover};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """

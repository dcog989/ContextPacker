import os
from pathlib import Path
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt


class AppTheme:
    def __init__(self):
        self.accent_color = "#2E8B57"  # Darker green from logo
        self.accent_color_lighter = "#3CB371"  # Lighter green from logo
        self.accent_color_darker = "#153E27"  # Darker green

        self.color_gray_808 = "#808080"
        self.color_gray_d0d = "#D0D0D0"
        self.color_gray_a0a = "#A0A0A0"
        self.color_gray_a9a = "#A9A9A9"
        self.color_gray_888 = "#888888"
        
        # Create checkmark icon and save to temp location
        self._setup_checkbox_icon()

    def _setup_checkbox_icon(self):
        """Creates and saves a checkmark icon for checkboxes."""
        size = 18
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw checkmark
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Checkmark path (approximate coordinates for 18x18 icon)
        painter.drawLine(4, 9, 7, 13)
        painter.drawLine(7, 13, 14, 5)
        
        painter.end()
        
        # Save to temp directory
        from core.utils import get_app_data_dir
        temp_dir = get_app_data_dir() / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        self.checkbox_icon_path = temp_dir / "checkbox_check.png"
        pixmap.save(str(self.checkbox_icon_path))

    def get_stylesheet(self):
        # Convert path to use forward slashes for Qt stylesheet
        icon_path = str(self.checkbox_icon_path).replace("\\", "/")
        
        return f"""
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
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }}
            
            /* System panel app name styling */
            QLabel#AppNameLabel {{
                color: {self.accent_color};
                font-size: 22px;
            }}
            
            /* Content inside QGroupBox - increase by 3px total (11px + 3px = 14px) */
            QGroupBox QLineEdit, QGroupBox QTextEdit, QGroupBox QSpinBox, 
            QGroupBox QComboBox, QGroupBox QPushButton, QGroupBox QCheckBox, 
            QGroupBox QRadioButton, QGroupBox QLabel {{
                font-size: 14px;
            }}
            
            /* Input fields - different shade of grey from app background */
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 6px 8px;
                font-size: 11px;
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
                background-color: #3A3A3A;
                selection-background-color: {self.accent_color};
                border: 1px solid #555555;
                padding: 4px;
            }}
            
            /* QSpinBox buttons - same color as field bg, with hover state */
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 16px;
                border: none;
                background-color: #3A3A3A;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: #4A4A4A;
            }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                width: 0px;
                height: 0px;
            }}
            
            /* Button styling with more padding and darker greys */
            QPushButton {{
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #4A4A4A;
                border: 1px solid #666666;
            }}
            QPushButton:pressed {{
                background-color: #353535;
                border: 1px solid #444444;
            }}
            QPushButton:disabled {{
                background-color: #2A2A2A;
                border: 1px solid #3A3A3A;
                color: #666666;
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
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton#ThemeSwitchButton:hover {{
                background-color: #4A4A4A;
                border: 1px solid #666666;
            }}
            QPushButton#ThemeSwitchButton:pressed {{
                background-color: #353535;
            }}
            
            /* Checkbox styling with custom checkmark */
            QCheckBox {{
                font-size: 11px;
                spacing: 8px;
                padding: 4px 0px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #3A3A3A;
            }}
            QCheckBox::indicator:hover {{
                border: 1px solid #666666;
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
                font-size: 11px;
                spacing: 8px;
                padding: 4px 0px;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid #555555;
                border-radius: 9px;
                background-color: #3A3A3A;
            }}
            QRadioButton::indicator:hover {{
                border: 1px solid #666666;
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
                font-size: 11px;
                padding: 2px 0px;
            }}
            
            /* Table widget styling */
            QTableWidget {{
                background-color: #3A3A3A;
                border: 1px solid #555555;
                gridline-color: #4A4A4A;
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {self.accent_color};
            }}
            QHeaderView::section {{
                background-color: #404040;
                border: 1px solid #555555;
                padding: 6px 8px;
                font-size: 11px;
                font-weight: bold;
            }}
            
            /* Progress bar styling */
            QProgressBar {{
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #3A3A3A;
                text-align: center;
                font-size: 11px;
                padding: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {self.accent_color};
                border-radius: 2px;
            }}
            
            /* Scrollbar styling */
            QScrollBar:vertical {{
                background-color: #2B2B2B;
                width: 14px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #555555;
                min-height: 30px;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #666666;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: #2B2B2B;
                height: 14px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #555555;
                min-width: 30px;
                border-radius: 7px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: #666666;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """

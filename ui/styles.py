class AppTheme:
    def __init__(self):
        # Only define static colors (accents and generic component colors)
        self.accent_color = "#2E8B57"  # Darker green from logo
        self.accent_color_lighter = "#3CB371"  # Lighter green from logo
        self.accent_color_darker = "#153E27"  # Darker green

        self.color_gray_active = "#808080"
        self.color_gray_highlight = "#D0D0D0"
        self.color_gray_light = "#A0A0A0"
        self.color_gray_hover = "#A9A9A9"
        self.color_gray_inactive = "#888888"
        self.group_box_bg = "transparent"  # Rely on Qt's QPalette.Base or QPalette.Window

    def get_stylesheet(self):
        return f"""
            QGroupBox {{
                /* Removing custom background color to rely on system theme */
                border: 1px solid {self.color_gray_highlight};
                margin-top: 10px;
                padding-top: 20px;
                border-radius: 4px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left; /* Align top-left */
                padding: 0 3px;
                margin-left: 5px;
            }}

            QPushButton#PrimaryButton {{
                background-color: {self.accent_color};
                color: white;
                border: 1px solid {self.accent_color};
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
            }}
            QPushButton#PrimaryButton:hover {{
                background-color: {self.accent_color_lighter};
                border: 1px solid {self.accent_color_lighter};
            }}
            QPushButton#PrimaryButton:disabled {{
                background-color: {self.color_gray_inactive};
                border: 1px solid {self.color_gray_highlight};
                color: {self.color_gray_light};
            }}
            
            QPushButton#ThemeSwitchButton {{
                border: none;
                background-color: transparent;
                padding: 0px;
            }}

            QSplitter::handle {{
                background-color: {self.color_gray_active};
            }}
            QSplitter::handle:hover {{
                background-color: {self.color_gray_hover};
            }}
            
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QTableWidget {{
                /* Keep border for clear component separation, rely on palette for colors */
                border: 1px solid {self.color_gray_active};
                padding: 2px;
                border-radius: 2px;
            }}
            QTableWidget {{
                gridline-color: {self.color_gray_highlight};
            }}
            QHeaderView::section {{
                /* Removing custom background color to rely on system theme */
                padding: 4px;
                border: 1px solid {self.color_gray_highlight};
            }}
            QTableWidget::item:selected {{
                background-color: {self.accent_color_darker};
                color: white;
            }}
        """

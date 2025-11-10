class AppTheme:
    def __init__(self, is_dark=True):
        self.accent_color = "#2E8B57"  # Darker green from logo
        self.accent_color_lighter = "#3CB371"  # Lighter green from logo
        self.accent_color_darker = "#153E27"  # Darker green

        # Colors for stylesheet components, allowing Qt palette to handle background/text
        self.color_gray_active = "#999" if not is_dark else "#666"
        self.color_gray_highlight = "#ccc" if not is_dark else "#444"
        self.color_gray_light = "#ddd" if not is_dark else "#333"  # Used for disabled text
        self.color_gray_hover = "#aaa" if not is_dark else "#777"
        self.color_gray_inactive = "#888"  # Used for disabled buttons/elements
        self.group_box_bg = "#f0f0f0" if not is_dark else "#3c3c3c"

    def get_stylesheet(self):
        # Rely on Qt palette for window/text/base colors. Stylesheet is only for component customization.
        return f"""
            QGroupBox {{
                background-color: {self.group_box_bg};
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
                border: 1px solid {self.color_gray_active};
                padding: 2px;
                border-radius: 2px;
            }}
            QTableWidget {{
                gridline-color: {self.color_gray_highlight};
            }}
            QHeaderView::section {{
                background-color: {self.group_box_bg}; /* Match group box background */
                padding: 4px;
                border: 1px solid {self.color_gray_highlight};
            }}
            QTableWidget::item:selected {{
                background-color: {self.accent_color_darker};
                color: white;
            }}
        """

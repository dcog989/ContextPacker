class AppTheme:
    def __init__(self, mode="system"):
        self.accent_color = "#2E8B57"  # Darker green from logo
        self.accent_color_lighter = "#3CB371"  # Lighter green from logo
        self.accent_color_darker = "#153E27"  # Darker green

        # Color palette based on mode
        if mode == "light":
            # Light Mode Palette
            self.background_color = "white"
            self.text_color = "black"
            self.group_box_bg = "#f0f0f0"
            self.color_gray_active = "#999"
            self.color_gray_highlight = "#ccc"
            self.color_gray_dark = "#333"
            self.color_gray_light = "#ddd"
            self.color_gray_hover = "#aaa"
            self.color_gray_inactive = "#666"
        else:
            # Dark Mode Palette (default for system/dark)
            self.background_color = "#2b2b2b"
            self.text_color = "#e0e0e0"
            self.group_box_bg = "#3c3c3c"
            self.color_gray_active = "#666"
            self.color_gray_highlight = "#444"
            self.color_gray_dark = "#ddd"
            self.color_gray_light = "#333"
            self.color_gray_hover = "#777"
            self.color_gray_inactive = "#999"

    def get_stylesheet(self):
        return f"""
            QWidget {{
                background-color: {self.background_color};
                color: {self.text_color};
            }}
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
                border: 1px solid {self.color_gray_active};
                color: {self.color_gray_highlight};
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
                background-color: {self.background_color};
                color: {self.text_color};
                border: 1px solid {self.color_gray_active};
                padding: 2px;
                border-radius: 2px;
            }}
            QTableWidget {{
                gridline-color: {self.color_gray_active};
            }}
            QHeaderView::section {{
                background-color: {self.group_box_bg};
                color: {self.text_color};
                padding: 4px;
                border: 1px solid {self.color_gray_active};
            }}
            QTableWidget::item:selected {{
                background-color: {self.accent_color_darker};
                color: white;
            }}
        """

class AppTheme:
    def __init__(self):
        self.accent_color = "#2E8B57"  # Darker green from logo
        self.accent_color_lighter = "#3CB371"  # Lighter green from logo
        self.accent_color_darker = "#153E27"  # Darker green
        self.color_gray_active = "#999"
        self.color_gray_highlight = "#ccc"
        self.color_gray_dark = "#333"
        self.color_gray_light = "#ddd"
        self.color_gray_hover = "#aaa"
        self.color_gray_inactive = "#666"

    def get_stylesheet(self):
        return f"""
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
                background-color: #888;
                border: 1px solid #ccc;
            }}
            QSplitter::handle {{
                background-color: {self.color_gray_active};
            }}
            QSplitter::handle:hover {{
                background-color: {self.color_gray_hover};
            }}
        """

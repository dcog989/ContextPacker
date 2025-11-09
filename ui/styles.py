class AppTheme:
    def __init__(self):
        self.accent_color = "#2E8B57"  # Darker green from logo
        self.accent_color_lighter = "#3CB371"  # Lighter green from logo
        self.accent_color_darker = "#153E27"  # Darker green

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
                background-color: {self.accent_color_darker};
            }}
            QSplitter::handle:hover {{
                background-color: {self.accent_color_lighter};
            }}
        """

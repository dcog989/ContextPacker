class AppTheme:
    def __init__(self):
        self.accent_color = "#2E8B57"  # Darker green from logo
        self.accent_hover_color = "#3CB371"  # Lighter green from logo

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
                background-color: {self.accent_hover_color};
                border: 1px solid {self.accent_hover_color};
            }}
            QPushButton#PrimaryButton:disabled {{
                background-color: #888;
                border: 1px solid #888;
            }}
            QProgressBar::chunk {{
                background-color: {self.accent_color};
            }}
            QSplitter::handle {{
                background-color: #555; /* Visible splitter handle */
            }}
            QSplitter::handle:hover {{
                background-color: {self.accent_hover_color};
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 1px solid {self.accent_color};
            }}
            QRadioButton::indicator:checked, QRadioButton::indicator:checked:hover {{
                background-color: {self.accent_color};
            }}
            QCheckBox::indicator:checked, QCheckBox::indicator:checked:hover {{
                background-color: {self.accent_color};
            }}
        """

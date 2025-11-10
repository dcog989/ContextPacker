class AppTheme:
    def __init__(self):
        self.accent_color = "#2E8B57"  # Darker green from logo
        self.accent_color_lighter = "#3CB371"  # Lighter green from logo
        self.accent_color_darker = "#153E27"  # Darker green

        self.color_gray_active = "#808080"
        self.color_gray_highlight = "#D0D0D0"
        self.color_gray_light = "#A0A0A0"
        self.color_gray_hover = "#A9A9A9"
        self.color_gray_inactive = "#888888"

    def get_stylesheet(self):
        return ""

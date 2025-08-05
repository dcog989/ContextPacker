import wx


class ThemedListCtrl(wx.ListCtrl):
    def __init__(self, parent, style, theme, is_dark):
        super().__init__(parent, style=style)
        self.theme = theme
        self.is_dark = is_dark

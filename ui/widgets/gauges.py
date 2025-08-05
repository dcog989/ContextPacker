import wx


class CustomGauge(wx.Panel):
    def __init__(self, parent, range=100, theme=None):
        super().__init__(parent)
        self.is_custom_themed = True
        self.theme = theme if theme else {}
        self._range = range
        self._value = 0
        self.UpdateTheme(self.theme)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.SetMinSize(wx.Size(-1, 10))

    def UpdateTheme(self, theme):
        self.theme = theme
        palette = self.theme.get("palette", {})
        self.track_color = palette.get("field", wx.Colour(60, 60, 60))
        self.bar_color = self.theme.get("accent_color", wx.Colour(60, 179, 113))
        self.SetBackgroundColour(palette.get("bg", wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)))
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()

        gc.SetBrush(wx.Brush(self.track_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, width, height, 3)

        if self._range > 0 and self._value > 0:
            progress_width = (self._value / self._range) * width
            gc.SetBrush(wx.Brush(self.bar_color))
            gc.DrawRoundedRectangle(0, 0, progress_width, height, 3)

    def SetValue(self, value):
        self._value = max(0, min(value, self._range))
        self.Refresh()

    def SetRange(self, range_val):
        self._range = range_val
        self.Refresh()

    def GetValue(self):
        return self._value

    def GetRange(self):
        return self._range

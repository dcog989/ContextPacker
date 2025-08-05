import wx


class CustomButton(wx.Panel):
    def __init__(self, parent, label, theme):
        super().__init__(parent)
        self.is_custom_themed = True
        self.label = label
        self.hover = False
        self.theme = theme if theme else {}
        self.color = None
        self.hover_color = None
        self.UpdateTheme(self.theme)
        self.disabled_color = wx.Colour(128, 128, 128)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_hover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_hover)
        self.SetMinSize(self.DoGetBestSize())

    def UpdateTheme(self, theme):
        self.theme = theme
        self.color = self.theme.get("accent_hover_color")
        self.hover_color = self.theme.get("accent_color")
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()

        bg_color = self.disabled_color
        if self.IsEnabled():
            if self.hover:
                bg_color = self.hover_color if self.hover_color else self.color
            else:
                bg_color = self.color

        if not bg_color:
            bg_color = self.disabled_color

        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, width, height, 5)
        gc.SetFont(self.GetFont(), wx.WHITE)
        label_width, label_height, _, _ = gc.GetFullTextExtent(self.label)
        gc.DrawText(self.label, (width - label_width) / 2, (height - label_height) / 2)

    def on_mouse_down(self, event):
        if self.IsEnabled():
            wx.PostEvent(self, wx.CommandEvent(wx.EVT_BUTTON.typeId, self.GetId()))

    def on_hover(self, event):
        self.hover = event.Entering()
        if self.hover and self.IsEnabled():
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.Refresh()

    def DoGetBestSize(self):
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        width, height = dc.GetTextExtent(self.label)
        return wx.Size(width + 40, height + 20)

    def Enable(self, enable=True):
        result = super().Enable(enable)
        self.Refresh()
        return result

    def Disable(self):
        return self.Enable(False)


class CustomSecondaryButton(CustomButton):
    def __init__(self, parent, label, theme):
        self.alert_active = False
        super().__init__(parent, label, theme)

    def UpdateTheme(self, theme):
        self.theme = theme
        palette = self.theme.get("palette", {})
        self.color = palette.get("secondary_bg")
        self.hover_color = self.theme.get("hover_color")
        self.Refresh()

    def SetAlertState(self, active=False):
        self.alert_active = active
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()

        bg_color = self.disabled_color
        text_color = self.theme.get("palette", {}).get("fg")

        if self.IsEnabled():
            if self.alert_active:
                bg_color = self.theme.get("danger_color")
                text_color = wx.WHITE
            elif self.hover:
                bg_color = self.hover_color
            else:
                bg_color = self.color

        if not bg_color:
            bg_color = self.disabled_color
        if not text_color:
            text_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT)

        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, width, height, 5)

        gc.SetFont(self.GetFont(), text_color)
        label_width, label_height, _, _ = gc.GetFullTextExtent(self.label)
        gc.DrawText(self.label, (width - label_width) / 2, (height - label_height) / 2)


class IconCustomButton(CustomSecondaryButton):
    def __init__(self, parent, bitmap, theme, size):
        self.bitmap = bitmap
        self.success_active = False
        super().__init__(parent, label="", theme=theme)
        self.SetMinSize(size)
        self.SetSize(size)

    def UpdateTheme(self, theme):
        super().UpdateTheme(theme)
        self.success_color = self.theme.get("accent_color")
        self.Refresh()

    def SetSuccessState(self, active=False):
        self.success_active = active
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()

        bg_color = self.disabled_color
        if self.IsEnabled():
            if self.success_active:
                bg_color = self.success_color
            elif self.hover:
                bg_color = self.hover_color
            else:
                bg_color = self.color

        if not bg_color:
            bg_color = self.disabled_color

        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, width, height, 5)

        if self.bitmap and self.bitmap.IsOk():
            bmp_w, bmp_h = self.bitmap.GetSize()
            dc.DrawBitmap(self.bitmap, int((width - bmp_w) / 2), int((height - bmp_h) / 2), useMask=False)

    def DoGetBestSize(self):
        return self.GetSize()

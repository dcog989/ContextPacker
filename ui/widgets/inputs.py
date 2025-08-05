import wx


class FocusTextCtrl(wx.Panel):
    def __init__(self, parent, value="", size=(-1, -1), style=wx.BORDER_NONE, theme=None):
        super().__init__(parent, size=size)
        self.is_custom_themed = True
        self.theme = theme if theme else {}
        self.unfocus_color = None

        self.padding_panel = wx.Panel(self)
        self.text_ctrl = wx.TextCtrl(self.padding_panel, value=value, style=style | wx.BORDER_NONE)

        padding_sizer = wx.BoxSizer(wx.VERTICAL)
        padding_sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, border=4)
        self.padding_panel.SetSizer(padding_sizer)

        border_sizer = wx.BoxSizer(wx.VERTICAL)
        border_sizer.Add(self.padding_panel, 1, wx.EXPAND | wx.ALL, border=1)
        self.SetSizer(border_sizer)

        self.text_ctrl.Bind(wx.EVT_SET_FOCUS, self.on_focus)
        self.text_ctrl.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

        self.UpdateTheme(self.theme)

    def UpdateTheme(self, theme):
        self.theme = theme
        palette = self.theme.get("palette", {})
        self.unfocus_color = palette.get("field")
        fg_color = palette.get("fg")

        if self.unfocus_color:
            self.SetBackgroundColour(self.unfocus_color)
            self.padding_panel.SetBackgroundColour(self.unfocus_color)
            self.text_ctrl.SetBackgroundColour(self.unfocus_color)
        if fg_color:
            self.text_ctrl.SetForegroundColour(fg_color)
        self.Refresh()

    def on_focus(self, event):
        accent_color = self.theme.get("accent_color")
        focus_field_color = self.theme.get("palette", {}).get("focus_field")

        if accent_color:
            self.SetBackgroundColour(accent_color)
        if focus_field_color:
            self.padding_panel.SetBackgroundColour(focus_field_color)
            self.text_ctrl.SetBackgroundColour(focus_field_color)

        self.Refresh()
        event.Skip()

    def on_kill_focus(self, event):
        if self.unfocus_color:
            self.SetBackgroundColour(self.unfocus_color)
            self.padding_panel.SetBackgroundColour(self.unfocus_color)
            self.text_ctrl.SetBackgroundColour(self.unfocus_color)
        self.Refresh()
        event.Skip()

    def GetValue(self):
        return self.text_ctrl.GetValue()

    def SetValue(self, value):
        self.text_ctrl.SetValue(value)

    def SetFocus(self):
        """Override to pass focus to the child text control."""
        self.text_ctrl.SetFocus()


class BaseToggleButton(wx.Panel):
    def __init__(self, parent, label, style=0, theme=None):
        super().__init__(parent, style=style)
        self.is_custom_themed = True
        self.label = label
        self.value = False
        self.theme = theme if theme else {}
        self.palette = {}
        self.accent_color = None
        self.hover_color = None
        self.hover = False

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_hover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_hover)
        self.UpdateTheme(self.theme)
        self.SetMinSize(self.DoGetBestSize())

    def UpdateTheme(self, theme):
        self.theme = theme if theme else {}
        self.palette = self.theme.get("palette", {})
        self.accent_color = self.theme.get("accent_color")
        self.hover_color = self.theme.get("hover_color")
        self.SetBackgroundColour(self.palette.get("bg"))
        self.Refresh()

    def on_paint(self, event):
        raise NotImplementedError

    def on_mouse_down(self, event):
        raise NotImplementedError

    def on_hover(self, event):
        self.hover = event.Entering()
        if self.hover:
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.Refresh()

    def SetValue(self, value):
        self.value = bool(value)
        self.Refresh()

    def GetValue(self):
        return self.value

    def DoGetBestSize(self):
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        width, height = dc.GetTextExtent(self.label)
        return wx.Size(width + 50, height + 10)


class CustomRadioButton(BaseToggleButton):
    def __init__(self, parent, label, style=0, theme=None):
        super().__init__(parent, label, style, theme)
        self.group = []

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()
        radius = height // 3
        indicator_x = radius + 5
        indicator_y = height // 2

        bg_color = self.hover_color if self.hover and self.hover_color else self.GetBackgroundColour()
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, width, height)

        if self.accent_color:
            gc.SetPen(wx.Pen(self.accent_color, 2))
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            gc.DrawEllipse(indicator_x - radius, indicator_y - radius, radius * 2, radius * 2)
            if self.value:
                gc.SetBrush(wx.Brush(self.accent_color))
                gc.DrawEllipse(indicator_x - radius / 2, indicator_y - radius / 2, radius, radius)

        fg_color = self.palette.get("fg")
        if fg_color:
            gc.SetFont(self.GetFont(), fg_color)
            _, label_height, _, _ = gc.GetFullTextExtent(self.label)
            gc.DrawText(self.label, indicator_x + radius + 10, (height - label_height) / 2)

    def on_mouse_down(self, event):
        if not self.value:
            self.SetValue(True)
            wx.PostEvent(self, wx.CommandEvent(wx.EVT_RADIOBUTTON.typeId, self.GetId()))

    def SetValue(self, value):
        self.value = bool(value)
        if self.value:
            for btn in self.group:
                if btn != self:
                    btn.SetValue(False)
        self.Refresh()


class CustomCheckBox(BaseToggleButton):
    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()
        box_size = height * 0.6
        box_x = 5
        box_y = (height - box_size) / 2

        bg_color = self.hover_color if self.hover and self.hover_color else self.GetBackgroundColour()
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, width, height)

        if self.accent_color:
            gc.SetPen(wx.Pen(self.accent_color, 2))
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            gc.DrawRoundedRectangle(box_x, box_y, box_size, box_size, 3)
            if self.value:
                gc.SetPen(wx.Pen(self.accent_color, 3))
                gc.StrokeLine(box_x + 3, box_y + box_size / 2, box_x + box_size / 2.5, box_y + box_size - 3)
                gc.StrokeLine(box_x + box_size / 2.5, box_y + box_size - 3, box_x + box_size - 3, box_y + 3)

        fg_color = self.palette.get("fg")
        if fg_color:
            gc.SetFont(self.GetFont(), fg_color)
            _, label_height, _, _ = gc.GetFullTextExtent(self.label)
            gc.DrawText(self.label, box_x + box_size + 10, (height - label_height) / 2)

    def on_mouse_down(self, event):
        self.SetValue(not self.value)
        wx.PostEvent(self, wx.CommandEvent(wx.EVT_CHECKBOX.typeId, self.GetId()))


class ThemedLogCtrl(wx.Panel):
    def __init__(self, parent, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.VSCROLL | wx.BORDER_NONE):
        super().__init__(parent)
        self.text_ctrl = wx.TextCtrl(self, style=style)
        log_font = wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Consolas")
        self.text_ctrl.SetFont(log_font)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def SetFocus(self):
        """Override to pass focus to the child text control."""
        self.text_ctrl.SetFocus()

    def AppendText(self, text):
        self.text_ctrl.AppendText(text)
        self.ScrollToEnd()

    def ScrollToEnd(self):
        wx.CallAfter(self.text_ctrl.ShowPosition, self.text_ctrl.GetLastPosition())

    def Clear(self):
        self.text_ctrl.Clear()

    def GetValue(self):
        return self.text_ctrl.GetValue()

    def SetValue(self, value):
        self.text_ctrl.SetValue(value)


class ThemedTextCtrl(ThemedLogCtrl):
    def __init__(self, parent, value=""):
        style = wx.TE_MULTILINE | wx.TE_RICH2 | wx.VSCROLL | wx.BORDER_NONE | wx.TE_PROCESS_ENTER
        super().__init__(parent, style=style)
        self.text_ctrl.SetEditable(True)
        self.text_ctrl.SetValue(value)
        self.text_ctrl.SetStyle(0, -1, wx.TextAttr())

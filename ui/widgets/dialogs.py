import wx
import webbrowser
from .buttons import CustomButton, CustomSecondaryButton
from core.packager import resource_path
from core.utils import set_title_bar_theme


class ThemedMessageDialog(wx.Dialog):
    def __init__(self, parent, message, title, style, theme):
        super().__init__(parent, title=title)
        self.theme = theme
        self.SetBackgroundColour(self.theme["palette"]["bg"])
        self.Bind(wx.EVT_SHOW, self.on_show)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        message_text = wx.StaticText(self, label=message)
        message_text.SetForegroundColour(self.theme["palette"]["fg"])
        message_text.Wrap(350)
        main_sizer.Add(message_text, flag=wx.ALL | wx.EXPAND, border=20)

        button_sizer = self.CreateButtonSizer(style)
        main_sizer.Add(button_sizer, flag=wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, border=20)

        self.SetSizerAndFit(main_sizer)
        self.CenterOnParent()

    def CreateButtonSizer(self, flags):
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if flags & wx.YES_NO:
            yes_button = CustomButton(self, "Yes", self.theme)
            no_button = CustomSecondaryButton(self, "No", self.theme)
            yes_button.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_YES))
            no_button.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_NO))
            button_sizer.Add(no_button, 0, wx.RIGHT, 10)
            button_sizer.Add(yes_button, 0)
        elif flags & wx.OK:
            ok_button = CustomButton(self, "OK", self.theme)
            ok_button.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
            button_sizer.Add(ok_button, 0)

        return button_sizer

    def on_show(self, event):
        if event.IsShown():
            wx.CallAfter(self._set_title_bar_theme)
        event.Skip()

    def _set_title_bar_theme(self):
        is_dark = self.theme.get("palette", {}).get("bg").GetRed() < 128
        set_title_bar_theme(self, is_dark)


class AboutDialog(wx.Dialog):
    def __init__(self, parent, theme, version, font_path, log_verbose_func):
        super().__init__(parent, title="About ContextPacker")
        self.theme = theme
        self.version = version
        self.font_path = font_path
        self.log_verbose = log_verbose_func

        self.SetBackgroundColour(self.theme["palette"]["bg"])
        self.Bind(wx.EVT_SHOW, self.on_show)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSpacer(20)

        font_loaded = False
        if self.font_path.exists():
            if wx.Font.AddPrivateFont(str(self.font_path)):
                font_loaded = True
            else:
                self.log_verbose("Warning: Failed to load custom font 'Source Code Pro'.")
        else:
            self.log_verbose(f"Warning: Custom font not found at '{self.font_path}'.")

        logo_path = resource_path("assets/icons/ContextPacker.svg")
        if logo_path.exists():
            bundle = wx.BitmapBundle.FromSVGFile(str(logo_path), wx.Size(128, 128))
            logo_bitmap = wx.StaticBitmap(self, bitmap=bundle)
            main_sizer.Add(logo_bitmap, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        title_font = wx.Font(22, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        if font_loaded:
            title_font.SetFaceName("Source Code Pro")

        title_text = wx.StaticText(self, label="ContextPacker")
        title_text.SetFont(title_font)
        title_text.SetForegroundColour(self.theme["accent_color"])
        main_sizer.Add(title_text, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        description = "Scrape websites or select local files, then package into a single file, optimized for LLMs."
        desc_font = self.GetFont()
        desc_font.SetPointSize(12)
        desc_text = wx.StaticText(self, label=description, style=wx.ALIGN_CENTER)
        desc_text.SetFont(desc_font)
        desc_text.SetForegroundColour(self.theme["palette"]["fg"])
        main_sizer.Add(desc_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        main_sizer.AddSpacer(15)

        milkshake_font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        if font_loaded:
            milkshake_font.SetFaceName("Source Code Pro")

        milkshake_text = wx.StaticText(self, label='"I drink your milkshake! I drink it up!"')
        milkshake_text.SetFont(milkshake_font)
        milkshake_text.SetForegroundColour(self.theme["palette"]["fg"])
        main_sizer.Add(milkshake_text, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        version_font = self.GetFont()
        version_font.SetPointSize(12)
        version_text = wx.StaticText(self, label=f"Version {self.version}")
        version_text.SetFont(version_font)
        version_text.SetForegroundColour(self.theme["palette"]["fg"])
        main_sizer.Add(version_text, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        url = "https://github.com/dcog989/ContextPacker"
        hyperlink = wx.StaticText(self, label=url)
        link_font = self.GetFont()
        link_font.SetPointSize(12)
        link_font.SetUnderlined(True)
        hyperlink.SetFont(link_font)
        is_dark = self.theme.get("palette", {}).get("bg").GetRed() < 128
        link_color = wx.Colour(102, 178, 255) if is_dark else wx.Colour(0, 102, 204)
        hyperlink.SetForegroundColour(link_color)
        hyperlink.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        hyperlink.Bind(wx.EVT_LEFT_DOWN, lambda event: webbrowser.open(url))
        main_sizer.Add(hyperlink, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        ok_button = CustomButton(self, "OK", self.theme)
        ok_button.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
        main_sizer.Add(ok_button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        outer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outer_sizer.Add(main_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 40)

        self.SetSizerAndFit(outer_sizer)
        self.CenterOnParent()

    def on_show(self, event):
        if event.IsShown():
            wx.CallAfter(self._set_title_bar_theme)
        event.Skip()

    def _set_title_bar_theme(self):
        is_dark = self.theme.get("palette", {}).get("bg").GetRed() < 128
        set_title_bar_theme(self, is_dark)

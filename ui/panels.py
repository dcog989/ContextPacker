import wx
from pathlib import Path
from .widgets.buttons import CustomButton, CustomSecondaryButton
from .widgets.inputs import FocusTextCtrl, CustomRadioButton, CustomCheckBox, ThemedLogCtrl, ThemedTextCtrl
from .widgets.lists import ThemedListCtrl
from .widgets.gauges import CustomGauge
from core.config import CrawlerConfig
from core.config_manager import get_config

config = get_config()


class CrawlerInputPanel(wx.Panel):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self._create_widgets()
        self._create_sizers()
        self.on_user_agent_change(None)
        self.start_url_ctrl.text_ctrl.Bind(wx.EVT_TEXT, self.on_url_change)
        self.on_url_change(None)

    def _create_widgets(self):
        self.start_url_label = wx.StaticText(self, label="Start URL:")
        self.start_url_ctrl = FocusTextCtrl(self, value="", theme=self.theme)
        self.user_agent_label = wx.StaticText(self, label="User-Agent:")
        user_agents = config.get("user_agents", [])
        self.user_agent_combo = wx.Choice(self, choices=user_agents)
        if user_agents:
            self.user_agent_combo.SetStringSelection(user_agents[0])
        self.max_pages_label = wx.StaticText(self, label="Max Pages:")
        self.max_pages_ctrl = FocusTextCtrl(self, value="50", theme=self.theme)
        self.crawl_depth_label = wx.StaticText(self, label="Crawl Depth:")
        self.crawl_depth_ctrl = wx.SpinCtrl(self, value="1", min=0, max=99)
        crawl_depth_tooltip = "0 = only the start URL.\n1 = the start URL and all pages linked from it.\n2 = pages linked from those pages, and so on."
        self.crawl_depth_label.SetToolTip(crawl_depth_tooltip)
        self.crawl_depth_ctrl.SetToolTip(crawl_depth_tooltip)
        self.pause_label = wx.StaticText(self, label="Pause (ms):")
        self.min_pause_ctrl = FocusTextCtrl(self, value="212", theme=self.theme)
        self.max_pause_ctrl = FocusTextCtrl(self, value="2200", theme=self.theme)
        self.include_paths_label = wx.StaticText(self, label="Include Paths:")
        self.include_paths_ctrl = ThemedTextCtrl(self)
        self.exclude_paths_label = wx.StaticText(self, label="Exclude Paths:")
        self.exclude_paths_ctrl = ThemedTextCtrl(self)
        self.stay_on_subdomain_check = CustomCheckBox(self, label="Stay on start URL's subdomain", theme=self.theme)
        self.stay_on_subdomain_check.SetValue(True)
        self.ignore_queries_check = CustomCheckBox(self, label="Ignore URL query parameters (?...)", theme=self.theme)
        self.ignore_queries_check.SetValue(True)
        self.download_button = CustomButton(self, label="Download & Convert", theme=self.theme)
        self.user_agent_combo.Bind(wx.EVT_CHOICE, self.on_user_agent_change)

        font = self.include_paths_ctrl.text_ctrl.GetFont()
        dc = wx.ClientDC(self)
        dc.SetFont(font)
        _w, char_height = dc.GetTextExtent("Xg")
        min_height = (char_height * 4) + 12
        self.include_paths_ctrl.SetMinSize(wx.Size(-1, min_height))
        self.exclude_paths_ctrl.SetMinSize(wx.Size(-1, min_height))

        logo_path = Path(__file__).parent.parent / "assets" / "icons" / "ContextPacker-x64.png"
        if logo_path.exists():
            img = wx.Image(str(logo_path), wx.BITMAP_TYPE_PNG)
            img.Rescale(64, 64, wx.IMAGE_QUALITY_HIGH)
            bmp = wx.Bitmap(img)
            self.about_logo = wx.StaticBitmap(self, bitmap=wx.BitmapBundle(bmp))
            self.about_logo.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            self.about_logo = wx.StaticText(self, label="?")

        self.about_text = wx.StaticText(self, label="ContextPacker")
        self.about_text.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        about_font = wx.Font(20, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        font_path = Path(__file__).parent.parent / "assets" / "fonts" / "SourceCodePro-Regular.ttf"
        if font_path.exists():
            if wx.Font.AddPrivateFont(str(font_path)):
                about_font.SetFaceName("Source Code Pro")
        self.about_text.SetFont(about_font)
        self.about_text.SetForegroundColour(self.theme["accent_color"])

    def _create_sizers(self):
        sizer = wx.FlexGridSizer(10, 2, 15, 10)
        sizer.AddGrowableCol(1, 1)
        sizer.Add(self.start_url_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.start_url_ctrl, 1, wx.EXPAND)
        sizer.Add(self.user_agent_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.user_agent_combo, 1, wx.EXPAND)
        numerical_sizer = wx.BoxSizer(wx.HORIZONTAL)
        numerical_sizer.Add(self.max_pages_ctrl, 0, wx.RIGHT, 15)
        numerical_sizer.Add(self.crawl_depth_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        numerical_sizer.Add(self.crawl_depth_ctrl, 0)
        sizer.Add(self.max_pages_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(numerical_sizer, 1, wx.ALIGN_LEFT | wx.EXPAND)
        sizer.Add(self.pause_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        pause_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pause_sizer.Add(self.min_pause_ctrl, 1, wx.EXPAND | wx.RIGHT, 5)
        pause_sizer.Add(wx.StaticText(self, label=" to "), 0, wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT, 5)
        pause_sizer.Add(self.max_pause_ctrl, 1, wx.EXPAND)
        sizer.Add(pause_sizer, 1, wx.EXPAND)
        sizer.Add(self.include_paths_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP | wx.TOP, 5)
        sizer.Add(self.include_paths_ctrl, 1, wx.EXPAND | wx.BOTTOM, 5)
        sizer.Add(self.exclude_paths_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP | wx.TOP, 5)
        sizer.Add(self.exclude_paths_ctrl, 1, wx.EXPAND | wx.BOTTOM, 5)
        options_sizer = wx.BoxSizer(wx.VERTICAL)
        options_sizer.Add(self.stay_on_subdomain_check, 0, wx.BOTTOM, 5)
        options_sizer.Add(self.ignore_queries_check, 0)
        sizer.Add(wx.StaticText(self, label=""), 0)
        sizer.Add(options_sizer, 1, wx.EXPAND | wx.TOP, 5)
        sizer.Add(wx.StaticText(self, label=""), 0)
        sizer.Add(self.download_button, 0, wx.ALIGN_LEFT | wx.TOP, 10)
        sizer.Add(self.about_logo, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.TOP, 15)
        sizer.Add(self.about_text, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL | wx.TOP, 15)

        self.SetSizer(sizer)

    def on_user_agent_change(self, event):
        full_ua_string = self.user_agent_combo.GetStringSelection()
        self.user_agent_combo.SetToolTip(wx.ToolTip(full_ua_string))

    def on_url_change(self, event):
        url = self.start_url_ctrl.GetValue()
        self.download_button.Enable(bool(url.strip()))
        if event:
            event.Skip()

    def get_crawler_config(self, output_dir):
        return CrawlerConfig(
            start_url=self.start_url_ctrl.GetValue(),
            output_dir=output_dir,
            max_pages=int(self.max_pages_ctrl.GetValue()),
            min_pause=int(self.min_pause_ctrl.GetValue()) / 1000.0,
            max_pause=int(self.max_pause_ctrl.GetValue()) / 1000.0,
            crawl_depth=self.crawl_depth_ctrl.GetValue(),
            include_paths=[p.strip() for p in self.include_paths_ctrl.GetValue().splitlines() if p.strip()],
            exclude_paths=[p.strip() for p in self.exclude_paths_ctrl.GetValue().splitlines() if p.strip()],
            stay_on_subdomain=self.stay_on_subdomain_check.GetValue(),
            ignore_queries=self.ignore_queries_check.GetValue(),
            user_agent=self.user_agent_combo.GetStringSelection(),
        )


class LocalInputPanel(wx.Panel):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self._create_widgets()
        self._create_sizers()

    def _create_widgets(self):
        self.local_dir_label = wx.StaticText(self, label="Input Directory:")
        self.local_dir_ctrl = FocusTextCtrl(self, theme=self.theme)
        self.browse_button = CustomButton(self, label="Browse...", theme=self.theme)
        self.local_exclude_label = wx.StaticText(self, label="Excludes:")
        self.local_exclude_ctrl = ThemedTextCtrl(self)
        self.local_exclude_ctrl.SetToolTip("List of files or folders to exclude by default (e.g., node_modules/, *.log).\nThese are combined with files you delete from the Output list.\nOne pattern per line.")
        font = self.local_exclude_ctrl.text_ctrl.GetFont()
        dc = wx.ClientDC(self)
        dc.SetFont(font)
        _w, char_height = dc.GetTextExtent("Xg")
        min_height = char_height * 6 + 12
        self.local_exclude_ctrl.SetMinSize(wx.Size(-1, min_height))
        default_excludes_list = config.get("default_local_excludes", [])
        default_excludes = "\n".join(default_excludes_list)
        self.local_exclude_ctrl.SetValue(default_excludes)
        self.include_subdirs_check = CustomCheckBox(self, label="Include Subdirectories", theme=self.theme)
        self.include_subdirs_check.SetValue(True)
        self.hide_binaries_check = CustomCheckBox(self, label="Hide Images + Binaries", theme=self.theme)
        self.hide_binaries_check.SetValue(True)

    def _create_sizers(self):
        sizer = wx.FlexGridSizer(3, 2, 10, 10)
        sizer.AddGrowableCol(1, 1)
        sizer.Add(self.local_dir_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        dir_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dir_input_sizer.Add(self.local_dir_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        dir_input_sizer.Add(self.browse_button, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(dir_input_sizer, 1, wx.EXPAND)
        sizer.Add(self.local_exclude_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP | wx.TOP, 5)
        sizer.Add(self.local_exclude_ctrl, 1, wx.EXPAND)
        sizer.Add(wx.StaticText(self, label=""), 0)

        options_sizer = wx.BoxSizer(wx.VERTICAL)
        options_sizer.Add(self.include_subdirs_check, 0, wx.BOTTOM, 5)
        options_sizer.Add(self.hide_binaries_check, 0)
        sizer.Add(options_sizer, 0, wx.EXPAND | wx.TOP, 5)

        self.SetSizer(sizer)


class ListPanel(wx.Panel):
    def __init__(self, parent, theme, is_dark):
        super().__init__(parent)
        self.theme = theme
        self.is_dark = is_dark
        self.scraped_files = []
        self.local_files = []
        self.user_has_resized = False
        self.sort_col_local = 0
        self.sort_dir_local = -1
        self.sort_col_web = 0
        self.sort_dir_web = -1
        self._create_widgets()
        self._create_sizers()
        self._bind_events()
        self.toggle_output_view(is_web_mode=True)
        self.local_file_list.ShowSortIndicator(self.sort_col_local, self.sort_dir_local == 1)
        self.standard_log_list.ShowSortIndicator(self.sort_col_web, self.sort_dir_web == 1)

    def _create_widgets(self):
        self.log_mode_panel = wx.Panel(self)
        self.standard_log_radio = CustomRadioButton(self.log_mode_panel, label="Files", theme=self.theme)
        self.verbose_log_radio = CustomRadioButton(self.log_mode_panel, label="Log", theme=self.theme)
        self.standard_log_radio.group = [self.standard_log_radio, self.verbose_log_radio]
        self.verbose_log_radio.group = [self.standard_log_radio, self.verbose_log_radio]
        self.standard_log_radio.SetValue(True)

        self.standard_log_list = ThemedListCtrl(self, style=wx.LC_REPORT | wx.LC_VRULES, theme=self.theme, is_dark=self.is_dark)
        self.standard_log_list.InsertColumn(0, "URL", width=200, format=wx.LIST_FORMAT_LEFT)
        self.standard_log_list.InsertColumn(1, "Saved Filename", width=400)
        self.verbose_log_ctrl = ThemedLogCtrl(self)
        self.local_file_list = ThemedListCtrl(self, style=wx.LC_REPORT | wx.LC_VRULES, theme=self.theme, is_dark=self.is_dark)
        self.local_file_list.InsertColumn(0, "Name", width=450, format=wx.LIST_FORMAT_LEFT)
        self.local_file_list.InsertColumn(1, "Type", width=120)
        self.local_file_list.InsertColumn(2, "Size", width=120, format=wx.LIST_FORMAT_RIGHT)

        self.delete_button = CustomSecondaryButton(self, label="Delete Selected", theme=self.theme)
        self.progress_gauge = CustomGauge(self, theme=self.theme)
        self.file_count_label = wx.StaticText(self, label="")

    def _create_sizers(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        log_mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        log_mode_sizer.Add(self.standard_log_radio, 0, wx.RIGHT, 10)
        log_mode_sizer.Add(self.verbose_log_radio, 0)
        self.log_mode_panel.SetSizer(log_mode_sizer)

        sizer.Add(self.log_mode_panel, 0, wx.ALL, 5)
        sizer.Add(self.verbose_log_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.standard_log_list, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.local_file_list, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)

        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer.Add(self.file_count_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        bottom_sizer.Add(self.delete_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizer.Add(bottom_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    def _bind_events(self):
        self.standard_log_radio.Bind(wx.EVT_RADIOBUTTON, self.on_toggle_log_mode)
        self.verbose_log_radio.Bind(wx.EVT_RADIOBUTTON, self.on_toggle_log_mode)

        for list_ctrl in [self.standard_log_list, self.local_file_list]:
            list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_selection_changed)
            list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_list_selection_changed)
            list_ctrl.Bind(wx.EVT_LIST_COL_END_DRAG, self.on_col_end_drag)
            list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self.on_col_click)

    def on_col_click(self, event):
        list_ctrl = event.GetEventObject()
        col = event.GetColumn()
        is_web_mode = list_ctrl == self.standard_log_list

        if is_web_mode:
            data_source = self.scraped_files
            sort_col, sort_dir = self.sort_col_web, self.sort_dir_web
            keys = ["url", "filename"]
        else:
            data_source = self.local_files
            sort_col, sort_dir = self.sort_col_local, self.sort_dir_local
            keys = ["name", "type", "size"]

        if col == sort_col:
            sort_dir *= -1
        else:
            sort_col = col
            sort_dir = 1

        if is_web_mode:
            self.sort_col_web, self.sort_dir_web = sort_col, sort_dir
        else:
            self.sort_col_local, self.sort_dir_local = sort_col, sort_dir

        is_ascending = sort_dir == 1
        list_ctrl.ShowSortIndicator(sort_col, is_ascending)

        sort_key = keys[col]
        reverse = not is_ascending

        if not is_web_mode and sort_key == "name":
            data_source.sort(key=lambda item: (item.get("type") != "Folder", item.get("name", "").lower()), reverse=reverse)
        else:
            data_source.sort(key=lambda item: item.get(sort_key, 0) if isinstance(item.get(sort_key, 0), (int, float)) else str(item.get(sort_key, "")).lower(), reverse=reverse)

        if is_web_mode:
            self.populate_web_file_list()
        else:
            self.populate_local_file_list(data_source)

    def on_col_end_drag(self, event):
        self.user_has_resized = True
        event.Skip()

    def resize_columns(self):
        if self.user_has_resized:
            return

        scrollbar_width = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X, self) + 5

        sl_list = self.standard_log_list
        if sl_list.IsShown():
            sl_width = sl_list.GetClientSize().width - scrollbar_width
            if sl_width > 0:
                sl_url_width = int(sl_width * 0.35)
                sl_filename_width = sl_width - sl_url_width
                sl_list.SetColumnWidth(0, sl_url_width)
                sl_list.SetColumnWidth(1, sl_filename_width)

        lf_list = self.local_file_list
        if lf_list.IsShown():
            lf_width = lf_list.GetClientSize().width - scrollbar_width
            if lf_width > 0:
                lf_type_width = 120
                lf_size_width = 120
                lf_name_width = lf_width - lf_type_width - lf_size_width
                lf_list.SetColumnWidth(0, lf_name_width)
                lf_list.SetColumnWidth(1, lf_type_width)
                lf_list.SetColumnWidth(2, lf_size_width)

    def _update_delete_button_state(self):
        list_ctrl = None
        if self.standard_log_list.IsShown():
            list_ctrl = self.standard_log_list
        elif self.local_file_list.IsShown():
            list_ctrl = self.local_file_list

        if list_ctrl:
            is_anything_selected = list_ctrl.GetSelectedItemCount() > 0
            self.delete_button.SetAlertState(is_anything_selected)
        else:
            self.delete_button.SetAlertState(False)

    def on_list_selection_changed(self, event):
        self._update_delete_button_state()

    def on_toggle_log_mode(self, event):
        if self.log_mode_panel.IsShown():
            is_files_mode = self.standard_log_radio.GetValue()
            self.standard_log_list.Show(is_files_mode)
            self.verbose_log_ctrl.Show(not is_files_mode)
            self.delete_button.Show(is_files_mode)
            if not is_files_mode:
                wx.CallAfter(self.verbose_log_ctrl.ScrollToEnd)
            self._update_delete_button_state()
            self.Layout()

    def toggle_output_view(self, is_web_mode):
        self.verbose_log_ctrl.Clear()
        self.log_mode_panel.Show(is_web_mode)
        self.local_file_list.Show(not is_web_mode)
        self.progress_gauge.SetValue(0)
        self.progress_gauge.Show(is_web_mode)
        if is_web_mode:
            self.on_toggle_log_mode(None)
        else:
            self.standard_log_list.Hide()
            self.verbose_log_ctrl.Hide()
            self.delete_button.Show(True)

        self.user_has_resized = False
        self._update_delete_button_state()
        self.Layout()
        wx.CallAfter(self.resize_columns)
        self.update_file_count()

    def add_scraped_file(self, url, path, filename):
        new_file = {"url": url, "path": path, "filename": filename}
        self.scraped_files.append(new_file)

        sort_key = ["url", "filename"][self.sort_col_web]
        reverse = self.sort_dir_web == -1
        self.scraped_files.sort(key=lambda item: str(item.get(sort_key, "")).lower(), reverse=reverse)

        self.populate_web_file_list()

    def populate_web_file_list(self):
        self.standard_log_list.DeleteAllItems()
        for item in self.scraped_files:
            index = self.standard_log_list.InsertItem(self.standard_log_list.GetItemCount(), item["url"])
            self.standard_log_list.SetItem(index, 1, item["filename"])
        self.update_file_count()

    def populate_local_file_list(self, files):
        self.local_file_list.DeleteAllItems()
        self.local_files = files
        for f in files:
            index = self.local_file_list.InsertItem(self.local_file_list.GetItemCount(), f["name"])
            self.local_file_list.SetItem(index, 1, f["type"])
            self.local_file_list.SetItem(index, 2, f["size_str"])

        if not self.user_has_resized:
            self.resize_columns()
        self.update_file_count()

    def log_verbose(self, message):
        self.verbose_log_ctrl.AppendText(message + "\n")

    def clear_logs(self):
        self.verbose_log_ctrl.Clear()
        self.standard_log_list.DeleteAllItems()
        self.scraped_files.clear()
        self._update_delete_button_state()
        self.update_file_count()

    def update_file_count(self):
        count = 0
        label = ""
        if self.standard_log_list.IsShown():
            count = self.standard_log_list.GetItemCount()
            if count > 0:
                label = f"{count} file(s)"
        elif self.local_file_list.IsShown():
            count = self.local_file_list.GetItemCount()
            if count > 0:
                label = f"{count} item(s)"

        self.file_count_label.SetLabel(label)

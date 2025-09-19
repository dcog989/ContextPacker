import wx
from .widgets.buttons import CustomButton, IconCustomButton
from .widgets.dialogs import ThemedMessageDialog
from .widgets.inputs import CustomRadioButton, FocusTextCtrl
from .panels import CrawlerInputPanel, LocalInputPanel, ListPanel
from core.config_manager import get_config
from core.packager import resource_path

config = get_config()


class MainFrame(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = parent
        self.theme = self.controller.theme

        font = self.GetFont()
        font.SetPointSize(11)
        self.SetFont(font)

        self._create_widgets()
        self.create_sizers()
        self._bind_events()

    def _create_widgets(self):
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_BORDER)
        self.left_panel = wx.Panel(self.splitter)
        self.right_panel_container = wx.Panel(self.splitter)

        self.input_static_box = wx.StaticBox(self.left_panel, label="Input")
        self.web_crawl_radio = CustomRadioButton(self.input_static_box, label="Web Crawl", theme=self.theme)
        self.local_dir_radio = CustomRadioButton(self.input_static_box, label="Local Directory", theme=self.theme)
        self.web_crawl_radio.group = [self.web_crawl_radio, self.local_dir_radio]
        self.local_dir_radio.group = [self.web_crawl_radio, self.local_dir_radio]
        self.web_crawl_radio.SetValue(True)

        self.crawler_panel = CrawlerInputPanel(self.input_static_box, self.theme, self.controller.version)
        self.local_panel = LocalInputPanel(self.input_static_box, self.theme)

        self.list_static_box = wx.StaticBox(self.right_panel_container, label="List")
        self.list_panel = ListPanel(self.list_static_box, self.theme, self.controller.is_dark)

        self.output_static_box = wx.StaticBox(self.right_panel_container, label="Output")
        self.output_filename_ctrl = FocusTextCtrl(self.output_static_box, value="ContextPacker-package", theme=self.theme)
        self.output_timestamp_label = wx.StaticText(self.output_static_box, label="")
        self.output_format_choice = wx.Choice(self.output_static_box, choices=[".md", ".txt", ".xml"])
        default_format = config.get("default_output_format", ".md")
        choices = self.output_format_choice.GetStrings()
        if default_format in choices:
            self.output_format_choice.SetSelection(choices.index(default_format))
        else:
            self.output_format_choice.SetSelection(0)
        self.package_button = CustomButton(self.output_static_box, label="Package", theme=self.theme)

        package_button_height = self.package_button.GetBestSize().GetHeight()
        copy_button_size = wx.Size(package_button_height, package_button_height)

        icon_path = resource_path("assets/icons/copy.png")
        img = wx.Image(str(icon_path), wx.BITMAP_TYPE_PNG)
        copy_bitmap = wx.Bitmap(img)

        self.copy_button = IconCustomButton(self.output_static_box, copy_bitmap, self.theme, size=copy_button_size)
        self.copy_button.SetToolTip("Copy final package contents to clipboard")
        self.copy_button.Disable()

        font = self.output_timestamp_label.GetFont()
        font.SetStyle(wx.FONTSTYLE_ITALIC)
        self.output_timestamp_label.SetFont(font)

    def create_sizers(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(self.splitter, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(main_sizer)

        left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_panel.SetSizer(left_sizer)

        input_sizer = wx.StaticBoxSizer(self.input_static_box, wx.VERTICAL)
        left_sizer.Add(input_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        radio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        radio_sizer.Add(self.web_crawl_radio, 0, wx.RIGHT, 10)
        radio_sizer.Add(self.local_dir_radio, 0)
        input_sizer.Add(radio_sizer, 0, wx.ALL, 10)
        input_sizer.Add(self.crawler_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        input_sizer.Add(self.local_panel, 1, wx.EXPAND | wx.ALL, 10)

        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_panel_container.SetSizer(right_sizer)

        list_box_sizer = wx.StaticBoxSizer(self.list_static_box, wx.VERTICAL)
        list_box_sizer.Add(self.list_panel, 1, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(list_box_sizer, 1, wx.EXPAND | wx.ALL, 5)

        output_box_sizer = wx.StaticBoxSizer(self.output_static_box, wx.VERTICAL)
        filename_sizer = wx.BoxSizer(wx.HORIZONTAL)
        filename_sizer.Add(self.output_filename_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        filename_sizer.Add(self.output_timestamp_label, 0, wx.ALIGN_CENTER_VERTICAL)
        filename_sizer.Add(self.output_format_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)
        filename_sizer.Add(self.package_button, 0, wx.ALIGN_CENTER_VERTICAL)
        filename_sizer.Add(self.copy_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        output_box_sizer.Add(filename_sizer, 0, wx.EXPAND | wx.ALL, 10)
        right_sizer.Add(output_box_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.splitter.SplitVertically(self.left_panel, self.right_panel_container)
        self.splitter.SetSashPosition(650)
        self.splitter.SetMinimumPaneSize(600)

    def _bind_events(self):
        self.web_crawl_radio.Bind(wx.EVT_RADIOBUTTON, self.controller.on_toggle_input_mode)
        self.local_dir_radio.Bind(wx.EVT_RADIOBUTTON, self.controller.on_toggle_input_mode)
        self.local_panel.browse_button.Bind(wx.EVT_BUTTON, self.controller.on_browse)
        self.local_panel.include_subdirs_check.Bind(wx.EVT_CHECKBOX, self.controller.on_local_filters_changed)
        self.local_panel.hide_binaries_check.Bind(wx.EVT_CHECKBOX, self.controller.on_local_filters_changed)

        exclude_ctrl = self.local_panel.local_exclude_ctrl.text_ctrl
        exclude_ctrl.Bind(wx.EVT_KILL_FOCUS, self.controller.on_local_filters_changed)
        exclude_ctrl.Bind(wx.EVT_TEXT_ENTER, self.controller.on_local_filters_changed)
        exclude_ctrl.Bind(wx.EVT_KEY_UP, self.controller.on_exclude_text_update)
        exclude_ctrl.Bind(wx.EVT_LEFT_UP, self.controller.on_exclude_text_update)

        self.crawler_panel.download_button.Bind(wx.EVT_BUTTON, self.controller.on_download_button_click)
        self.package_button.Bind(wx.EVT_BUTTON, self.controller.on_package_button_click)
        self.list_panel.delete_button.Bind(wx.EVT_BUTTON, self.on_delete_selected_item)
        self.copy_button.Bind(wx.EVT_BUTTON, self.controller.on_copy_to_clipboard)

        self.crawler_panel.about_logo.Bind(wx.EVT_LEFT_DOWN, self.controller.on_show_about_dialog)
        self.crawler_panel.about_logo.Bind(wx.EVT_RIGHT_DOWN, self.controller.on_show_about_dialog)
        self.crawler_panel.about_text.Bind(wx.EVT_LEFT_DOWN, self.controller.on_show_about_dialog)
        self.crawler_panel.about_text.Bind(wx.EVT_RIGHT_DOWN, self.controller.on_show_about_dialog)

    def on_delete_selected_item(self, event):
        is_web_mode = self.web_crawl_radio.GetValue()
        list_ctrl = self.list_panel.standard_log_list if is_web_mode else self.list_panel.local_file_list
        data_source = self.list_panel.scraped_files if is_web_mode else self.list_panel.local_files

        selected_count = list_ctrl.GetSelectedItemCount()
        if selected_count == 0:
            return

        if is_web_mode:
            title = "Confirm Deletion"
            message = f"Are you sure you want to permanently delete {selected_count} downloaded file(s)?"
        else:
            title = "Confirm Removal"
            message = f"Are you sure you want to remove {selected_count} item(s) from the package list?"

        with ThemedMessageDialog(self, message, title, wx.YES_NO | wx.NO_DEFAULT, self.theme) as dlg:
            if dlg.ShowModal() != wx.ID_YES:
                return

        selected_indices = []
        item = list_ctrl.GetFirstSelected()
        while item != -1:
            selected_indices.append(item)
            item = list_ctrl.GetNextSelected(item)

        for index in sorted(selected_indices, reverse=True):
            item_to_remove = data_source.pop(index)
            list_ctrl.DeleteItem(index)

            if is_web_mode:
                self.controller.delete_scraped_file(item_to_remove["path"])
            else:
                self.controller.remove_local_file_from_package(item_to_remove["rel_path"])

        self.list_panel.delete_button.SetAlertState(False)
        self.controller._update_button_states()
        self.list_panel.update_file_count()

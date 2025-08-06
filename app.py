import wx
import winreg
import os
import queue
from datetime import datetime
from pathlib import Path
import ctypes
import subprocess
import platform
import multiprocessing

from ui.main_frame import MainFrame
from ui.widgets.dialogs import AboutDialog
import core.actions as actions
from core.packager import resource_path
from core.version import __version__
from core.config_manager import get_config
from core.task_handler import TaskHandler
from core.utils import get_downloads_folder, set_title_bar_theme

config = get_config()
BINARY_FILE_PATTERNS = config.get("binary_file_patterns", [])


class App(wx.Frame):
    def __init__(self):
        super().__init__(None, title="ContextPacker", size=wx.Size(1600, 950))

        self.version = __version__
        self.task_handler = TaskHandler(self)
        self.temp_dir = None
        self.final_output_path = None
        self.filename_prefix = ""
        self.log_queue = queue.Queue()
        self.cancel_event = None
        self.worker_thread = None
        self.is_shutting_down = False
        self.is_task_running = False
        self.is_dark = self._is_dark_mode()
        self.local_files_to_exclude = set()
        self.exclude_list_last_line = 0

        self._set_theme_palette()
        self.main_panel = MainFrame(self)
        self._apply_theme_to_widgets()
        self._setup_timer()
        self._set_icon()

        self.toggle_input_mode()
        self.Center()
        self.Show()
        self._set_title_bar_theme()
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def _is_dark_mode(self):
        system = platform.system()
        if system == "Windows":
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0
            except Exception:
                return False
        elif system == "Darwin":
            try:
                cmd = "defaults read -g AppleInterfaceStyle"
                p = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                return "Dark" in p.stdout
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False
        else:
            bg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
            return bg_color.GetLuminance() < 0.5

    def _set_theme_palette(self):
        self.accent_color = wx.Colour("#3CB371")
        self.accent_hover_color = wx.Colour("#2E8B57")
        danger_color = wx.Colour("#B22222")

        dark_colors = {"bg": wx.Colour(46, 46, 46), "fg": wx.Colour(224, 224, 224), "field": wx.Colour(60, 60, 60), "hover": wx.Colour(80, 80, 80), "secondary_bg": wx.Colour(80, 80, 80), "focus_field": wx.Colour(70, 70, 70)}
        light_colors = {"bg": wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK), "fg": wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT), "field": wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW), "hover": wx.Colour(212, 212, 212), "secondary_bg": wx.Colour(225, 225, 225), "focus_field": wx.Colour(230, 245, 230)}

        self.palette = dark_colors if self.is_dark else light_colors
        self.hover_color = self.palette["hover"]
        self.SetBackgroundColour(self.palette["bg"])

        self.theme = {
            "palette": self.palette,
            "accent_color": self.accent_color,
            "accent_hover_color": self.accent_hover_color,
            "hover_color": self.hover_color,
            "danger_color": danger_color,
        }

    def _apply_theme_to_widgets(self):
        def set_colors_recursive(widget):
            if hasattr(widget, "is_custom_themed") and widget.is_custom_themed:
                widget.UpdateTheme(self.theme)
                return

            widget.SetBackgroundColour(self.palette["bg"])
            widget.SetForegroundColour(self.palette["fg"])

            if isinstance(widget, (wx.TextCtrl, wx.Choice, wx.SpinCtrl, wx.ListCtrl)):
                widget.SetBackgroundColour(self.palette["field"])
            if isinstance(widget, wx.StaticBox):
                widget.SetForegroundColour(self.palette["fg"])

            for child in widget.GetChildren():
                set_colors_recursive(child)

        set_colors_recursive(self.main_panel)
        self.main_panel.list_panel.verbose_log_ctrl.text_ctrl.SetBackgroundColour(self.palette["field"])
        self.main_panel.list_panel.verbose_log_ctrl.text_ctrl.SetForegroundColour(self.palette["fg"])
        self.main_panel.list_panel.standard_log_list.SetBackgroundColour(self.palette["field"])
        self.main_panel.list_panel.standard_log_list.SetForegroundColour(self.palette["fg"])
        self.main_panel.list_panel.local_file_list.SetBackgroundColour(self.palette["field"])
        self.main_panel.list_panel.local_file_list.SetForegroundColour(self.palette["fg"])
        self.main_panel.crawler_panel.include_paths_ctrl.text_ctrl.SetBackgroundColour(self.palette["field"])
        self.main_panel.crawler_panel.exclude_paths_ctrl.text_ctrl.SetBackgroundColour(self.palette["field"])
        self.main_panel.local_panel.local_exclude_ctrl.text_ctrl.SetBackgroundColour(self.palette["field"])
        self.main_panel.crawler_panel.about_text.SetForegroundColour(self.theme["accent_color"])
        self.Refresh()

    def _set_title_bar_theme(self):
        set_title_bar_theme(self, self.is_dark)

    def _setup_timer(self):
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_check_log_queue, self.timer)
        self.timer.Start(100)

    def _set_icon(self):
        try:
            icon_path = resource_path("assets/icons/ContextPacker.ico")
            if icon_path.exists():
                self.SetIcon(wx.Icon(str(icon_path), wx.BITMAP_TYPE_ICO))
        except Exception as e:
            print(f"Warning: Failed to set icon: {e}")

    def on_close(self, event):
        self.timer.Stop()
        if self.worker_thread and self.worker_thread.is_alive():
            self.is_shutting_down = True
            if self.cancel_event:
                self.cancel_event.set()
            self.log_verbose("Shutdown requested. Waiting for process to terminate...")
            self.main_panel.crawler_panel.download_button.Disable()
            self.main_panel.package_button.Disable()
        else:
            self.Destroy()

    def _toggle_ui_controls(self, enable=True, widget_to_keep_enabled=None):
        """Enable or disable all input controls, optionally keeping one enabled."""
        widgets_to_toggle = [
            self.main_panel.web_crawl_radio,
            self.main_panel.local_dir_radio,
            self.main_panel.crawler_panel,
            self.main_panel.local_panel,
            self.main_panel.output_filename_ctrl,
            self.main_panel.output_format_choice,
        ]
        for widget in widgets_to_toggle:
            if widget is not widget_to_keep_enabled:
                widget.Enable(enable)

    def on_toggle_input_mode(self, event):
        self.toggle_input_mode()

    def toggle_input_mode(self):
        is_url_mode = self.main_panel.web_crawl_radio.GetValue()
        self.main_panel.crawler_panel.Show(is_url_mode)
        self.main_panel.local_panel.Show(not is_url_mode)
        self.main_panel.list_panel.toggle_output_view(is_web_mode=is_url_mode)
        self.main_panel.left_panel.Layout()
        if not is_url_mode:
            self.populate_local_file_list()
        self._update_button_states()

    def on_browse(self, event):
        with wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.main_panel.local_panel.local_dir_ctrl.SetValue(path)
                self.populate_local_file_list()
        self._update_button_states()
        wx.CallAfter(self.main_panel.local_panel.local_dir_ctrl.SetFocus)

    def on_local_filters_changed(self, event):
        self.populate_local_file_list()
        event.Skip()

    def on_exclude_text_update(self, event):
        def check_caret_and_refresh():
            text_ctrl = self.main_panel.local_panel.local_exclude_ctrl.text_ctrl
            pos = text_ctrl.GetInsertionPoint()
            _, _, current_line = text_ctrl.PositionToXY(pos)
            if current_line != self.exclude_list_last_line:
                self.exclude_list_last_line = current_line
                self.populate_local_file_list()
                wx.CallAfter(text_ctrl.SetFocus)

        wx.CallAfter(check_caret_and_refresh)
        event.Skip()

    def on_download_button_click(self, event):
        if self.is_task_running:
            self.on_stop_process()
        else:
            self.task_handler.start_download_task()

    def on_package_button_click(self, event):
        if self.is_task_running:
            self.on_stop_process()
        else:
            self.task_handler.start_package_task()

    def on_stop_process(self):
        self.task_handler.stop_current_task()

    def on_copy_to_clipboard(self, event):
        if not self.final_output_path or not Path(self.final_output_path).exists():
            self.log_verbose("ERROR: No output file found to copy.")
            return

        try:
            with open(self.final_output_path, "r", encoding="utf-8") as f:
                content = f.read()

            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(content))
                wx.TheClipboard.Close()
                self.log_verbose(f"Copied {len(content):,} characters to clipboard.")
                self.main_panel.copy_button.SetSuccessState(True)
            else:
                self.log_verbose("ERROR: Could not open clipboard.")
        except Exception as e:
            self.log_verbose(f"ERROR: Failed to copy to clipboard: {e}")

    def _update_timestamp_label(self):
        if self.main_panel and self.main_panel.output_timestamp_label:
            timestamp_str = datetime.now().strftime("-%y%m%d-%H%M%S")
            if self.main_panel.output_timestamp_label.GetLabel() != timestamp_str:
                self.main_panel.output_timestamp_label.SetLabel(timestamp_str)
                self.main_panel.right_panel_container.Layout()

    def on_check_log_queue(self, event):
        try:
            while True:
                msg_obj = self.log_queue.get_nowait()
                msg_type = msg_obj.get("type")
                message = msg_obj.get("message", "")

                if msg_type == "log":
                    wx.CallAfter(self.log_verbose, message)
                elif msg_type == "file_saved":
                    wx.CallAfter(self.main_panel.list_panel.add_scraped_file, msg_obj["url"], msg_obj["path"], msg_obj["filename"])
                    verbose_msg = f"  -> Saved: {msg_obj['filename']} [{msg_obj['pages_saved']}/{msg_obj['max_pages']}]"
                    wx.CallAfter(self.log_verbose, verbose_msg)
                elif msg_type == "progress":
                    wx.CallAfter(self.main_panel.list_panel.progress_gauge.SetValue, msg_obj["value"])
                    wx.CallAfter(self.main_panel.list_panel.progress_gauge.SetRange, msg_obj["max_value"])
                elif msg_type == "status":
                    wx.CallAfter(self.task_handler.handle_status, msg_obj.get("status"), msg_obj)
                else:
                    wx.CallAfter(self.log_verbose, str(message))
        except queue.Empty:
            pass
        finally:
            if not (self.worker_thread and self.worker_thread.is_alive()):
                self._update_timestamp_label()

    def _update_button_states(self):
        is_web_mode = self.main_panel.web_crawl_radio.GetValue()
        package_ready = False
        copy_ready = bool(self.final_output_path and Path(self.final_output_path).exists())

        if is_web_mode:
            if self.temp_dir and any(f.is_file() for f in Path(self.temp_dir).iterdir()):
                package_ready = True
        else:
            if self.main_panel.local_panel.local_dir_ctrl.GetValue():
                package_ready = True

        self.main_panel.package_button.Enable(package_ready)
        self.main_panel.copy_button.Enable(copy_ready)
        self.main_panel.copy_button.SetSuccessState(copy_ready)

    def log_verbose(self, message):
        self.main_panel.list_panel.log_verbose(message)

    def _open_output_folder(self):
        if not self.final_output_path:
            return
        self.log_verbose("Opening output folder...")
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["explorer", "/select,", self.final_output_path], creationflags=0x08000000)
            elif system == "Darwin":
                subprocess.run(["open", "-R", self.final_output_path], check=True)
            else:
                subprocess.run(["xdg-open", str(Path(self.final_output_path).parent)], check=True)
        except Exception as e:
            self.log_verbose(f"ERROR: Could not open output folder: {e}")

    def delete_scraped_file(self, filepath):
        try:
            os.remove(filepath)
            self.log_verbose(f"Deleted file: {filepath}")
            self._update_button_states()
        except Exception as e:
            self.log_verbose(f"ERROR: Could not delete file {filepath}: {e}")

    def remove_local_file_from_package(self, rel_path):
        self.local_files_to_exclude.add(rel_path)
        self.log_verbose(f"Will exclude from package: {rel_path}")

    def populate_local_file_list(self, include_subdirs=None):
        if include_subdirs is None:
            include_subdirs = self.main_panel.local_panel.include_subdirs_check.GetValue()

        self.local_files_to_exclude.clear()
        input_dir = self.main_panel.local_panel.local_dir_ctrl.GetValue()
        if not input_dir or not Path(input_dir).is_dir():
            self.main_panel.list_panel.populate_local_file_list([])
            return

        custom_excludes = [p.strip() for p in self.main_panel.local_panel.local_exclude_ctrl.GetValue().splitlines() if p.strip()]
        binary_excludes = BINARY_FILE_PATTERNS if self.main_panel.local_panel.hide_binaries_check.GetValue() else []

        try:
            files_to_show = actions.get_local_files(input_dir, include_subdirs, custom_excludes, binary_excludes)
            wx.CallAfter(self.main_panel.list_panel.populate_local_file_list, files_to_show)
        except Exception as e:
            self.log_verbose(f"ERROR scanning directory: {e}")

    def _get_downloads_folder(self):
        return get_downloads_folder()

    def on_show_about_dialog(self, event):
        font_path = resource_path("assets/fonts/SourceCodePro-Regular.ttf")
        with AboutDialog(self, self.theme, self.version, font_path, self.log_verbose) as dlg:
            dlg.ShowModal()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        print(f"DIAG: DPI awareness setting failed. Error: {e}")

    app = wx.App(False)
    frame = App()
    app.MainLoop()

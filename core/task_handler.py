import wx
from pathlib import Path
import threading
import multiprocessing

import core.actions as actions
from ui.widgets.dialogs import ThemedMessageDialog


class TaskHandler:
    def __init__(self, app_instance):
        self.app = app_instance

    def start_download_task(self):
        dl_button = self.app.main_panel.crawler_panel.download_button
        self.app._toggle_ui_controls(False, widget_to_keep_enabled=dl_button)

        start_url = self.app.main_panel.crawler_panel.start_url_ctrl.GetValue()
        git_pattern = r"(\.git$)|(github\.com)|(gitlab\.com)|(bitbucket\.org)"
        if __import__("re").search(git_pattern, start_url):
            self.app.main_panel.copy_button.SetSuccessState(False)
            wx.BeginBusyCursor()
            self.app.is_task_running = True
            self.app.main_panel.package_button.Disable()
            self.app.main_panel.copy_button.Disable()
            dl_button.label = "Cloning..."
            dl_button.Refresh()
            self.app.cancel_event = threading.Event()
            actions.start_git_clone(self.app, self.app.cancel_event)
            return

        try:
            self.app.main_panel.crawler_panel.get_crawler_config("dummy_dir_for_validation")
        except (ValueError, AttributeError):
            msg = "Invalid input. Please ensure 'Max Pages', 'Min Pause', and 'Max Pause' are whole numbers."
            dlg = ThemedMessageDialog(self.app, msg, "Input Error", wx.OK | wx.ICON_ERROR, self.app.theme)
            dlg.ShowModal()
            dlg.Destroy()
            self.app._toggle_ui_controls(True)
            return

        self.app.main_panel.copy_button.SetSuccessState(False)
        wx.BeginBusyCursor()
        self.app.is_task_running = True
        self.app.main_panel.package_button.Disable()
        self.app.main_panel.copy_button.Disable()
        dl_button.label = "Stop!"
        dl_button.Refresh()

        self.app.cancel_event = multiprocessing.Event()
        self.app.start_queue_listener()
        actions.start_download(self.app, self.app.cancel_event)
        

    def start_package_task(self, file_list_for_count):
        pkg_button = self.app.main_panel.package_button
        self.app._toggle_ui_controls(False, widget_to_keep_enabled=pkg_button)

        is_web_mode = self.app.main_panel.web_crawl_radio.GetValue()
        if not is_web_mode:
            source_dir = self.app.main_panel.local_panel.local_dir_ctrl.GetValue()
            if not source_dir or not Path(source_dir).is_dir():
                msg = f"The specified input directory is not valid:\n{source_dir}"
                dlg = ThemedMessageDialog(self.app, msg, "Input Error", wx.OK | wx.ICON_ERROR, self.app.theme)
                dlg.ShowModal()
                dlg.Destroy()
                self.app._toggle_ui_controls(True)
                return

        self.app.main_panel.copy_button.SetSuccessState(False)
        wx.BeginBusyCursor()
        self.app.is_task_running = True
        self.app.main_panel.crawler_panel.download_button.Disable()
        self.app.main_panel.copy_button.Disable()
        pkg_button.label = "Stop!"
        pkg_button.Refresh()

        self.app.cancel_event = threading.Event()
        self.app.start_queue_listener()
        actions.start_packaging(self.app, self.app.cancel_event, file_list_for_count)


    def stop_current_task(self):
        if self.app.cancel_event:
            self.app.cancel_event.set()

        dl_button = self.app.main_panel.crawler_panel.download_button
        pkg_button = self.app.main_panel.package_button

        # Change label to give immediate feedback and disable to prevent multi-clicks
        if dl_button.IsEnabled():
            dl_button.label = "Stopping..."
            dl_button.Disable()
            dl_button.Refresh()

        if pkg_button.IsEnabled():
            pkg_button.label = "Stopping..."
            pkg_button.Disable()
            pkg_button.Refresh()

        self.app.log_verbose("Stopping process...")


    def handle_status(self, status, msg_obj):
        message = msg_obj.get("message", "")
        if status == "error":
            dlg = ThemedMessageDialog(self.app, message, "An Error Occurred", wx.OK | wx.ICON_ERROR, self.app.theme)
            dlg.ShowModal()
            dlg.Destroy()
        elif status == "clone_complete":
            self.app.log_verbose("✔ Git clone successful.")
            self.app.main_panel.local_panel.local_dir_ctrl.SetValue(msg_obj.get("path", ""))
            self.app.main_panel.web_crawl_radio.SetValue(False)
            self.app.main_panel.local_dir_radio.SetValue(True)
            self.app.toggle_input_mode()
        elif message:
            self.app.log_verbose(message)

        if status in ["source_complete", "package_complete", "cancelled", "error", "clone_complete"]:
            if status == "package_complete":
                self.app._open_output_folder()
            self.cleanup_after_task()
            self.app._update_button_states()


    def cleanup_after_task(self):
        if self.app.is_task_running:
            wx.EndBusyCursor()
            self.app.is_task_running = False

        self.app.stop_queue_listener()
        self.app._toggle_ui_controls(True)

        self.app.worker_thread = None
        self.app.cancel_event = None

        if self.app.is_shutting_down:
            wx.CallAfter(self.app.Destroy)
            return

        dl_button = self.app.main_panel.crawler_panel.download_button
        dl_button.label = "Download & Convert"
        dl_button.Enable()
        dl_button.Refresh()

        pkg_button = self.app.main_panel.package_button
        pkg_button.label = "Package"
        pkg_button.Enable()
        pkg_button.Refresh()

        self.app.main_panel.list_panel.progress_gauge.SetValue(0)
        self.app._update_button_states()

        self.app.timer.Start(100)

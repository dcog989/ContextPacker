import threading
from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QApplication
from PySide6.QtCore import Qt

import core.actions as actions


class TaskHandler:
    def __init__(self, app_instance):
        self.app = app_instance

    def start_download_task(self):
        dl_button = self.app.main_panel.download_button
        self.app.signals.message.emit({"type": "ui_task_start", "task": "download"})

        start_url = self.app.main_panel.start_url_ctrl.text()
        git_pattern = r"(\.git$)|(github\.com)|(gitlab\.com)|(bitbucket\.org)"
        if __import__("re").search(git_pattern, start_url):
            try:
                self.app.main_panel.get_crawler_config("dummy_dir_for_validation")
            except (ValueError, AttributeError):
                msg = "Invalid input. Please ensure 'Max Pages', 'Min Pause', and 'Max Pause' are whole numbers."
                QMessageBox.critical(self.app, "Input Error", msg)
                self.app.signals.message.emit({"type": "ui_task_stop"})
                return

            self.app.cancel_event = threading.Event()
            actions.start_git_clone(self.app, self.app.cancel_event)
            return

        try:
            self.app.main_panel.get_crawler_config("dummy_dir_for_validation")
        except (ValueError, AttributeError):
            msg = "Invalid input. Please ensure 'Max Pages', 'Min Pause', and 'Max Pause' are whole numbers."
            QMessageBox.critical(self.app, "Input Error", msg)
            self.app.signals.message.emit({"type": "ui_task_stop"})
            return

        self.app.cancel_event = threading.Event()
        self.app.start_queue_listener()
        actions.start_download(self.app, self.app.cancel_event)

    def start_package_task(self, file_list_for_count):
        self.app.signals.message.emit({"type": "ui_task_start", "task": "package"})

        is_web_mode = self.app.main_panel.web_crawl_radio.isChecked()
        if not is_web_mode:
            source_dir = self.app.main_panel.local_dir_ctrl.text()
            if not source_dir or not Path(source_dir).is_dir():
                msg = f"The specified input directory is not valid:\n{source_dir}"
                QMessageBox.critical(self.app, "Input Error", msg)
                self.app.signals.message.emit({"type": "ui_task_stop"})
                return

        self.app.cancel_event = threading.Event()
        self.app.start_queue_listener()
        actions.start_packaging(self.app, self.app.cancel_event, file_list_for_count)

    def stop_current_task(self):
        if self.app.cancel_event:
            self.app.cancel_event.set()
            self.app.signals.message.emit({"type": "ui_task_stopping"})

    def handle_status(self, status, msg_obj):
        message = msg_obj.get("message", "")
        if status == "error":
            QMessageBox.critical(self.app, "An Error Occurred", message)
            self.app.signals.message.emit({"type": "log", "message": message})
        elif status == "clone_complete":
            self.app.signals.message.emit({"type": "log", "message": "✔ Git clone successful."})
            self.app.signals.message.emit({"type": "git_clone_done", "path": msg_obj.get("path", "")})
        elif message:
            self.app.signals.message.emit({"type": "log", "message": message})

        if status in ["source_complete", "package_complete", "cancelled", "error", "clone_complete"]:
            if status == "package_complete":
                self.app._open_output_folder()

            self.app.signals.message.emit({"type": "ui_task_stop", "was_cancelled": status == "cancelled"})

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import threading
from PySide6.QtWidgets import QMessageBox

from core import actions
from core.crawler import crawl_website
from core.types import UITaskMessage, UITaskStopMessage, UITaskStoppingMessage, LogMessage, GitCloneDoneMessage, TaskType, ProgressMessage, StatusMessage, StatusType, AppState


class TaskHandler:
    def __init__(self, app_instance):
        self.app = app_instance

    def start_download_task(self):
        if self.app.state.current_state != AppState.IDLE:
            self.app.log_verbose(f"[DIAG] start_download_task: Blocked by app state {self.app.state.current_state.name}")
            return

        start_url = self.app.main_panel.start_url_widget.text().strip()
        import re

        if not start_url:
            QMessageBox.critical(self.app, "Input Error", "Start URL is required.")
            return

        url_pattern = r"^(https?://|git@|ssh://|file://)[a-zA-Z0-9._/-]+(:[0-9]+)?(/.*)?$"
        if not re.match(url_pattern, start_url):
            QMessageBox.critical(self.app, "Input Error", "Invalid URL format. Please use a valid HTTP, HTTPS, or Git URL.")
            return

        git_pattern = r"(\.git$)|(github\.com)|(gitlab\.com)|(bitbucket\.org)"
        if __import__("re").search(git_pattern, start_url):
            msg = UITaskMessage(task=TaskType.DOWNLOAD)
            self.app.signals.message.emit(msg)

            self.app.state.cancel_event = threading.Event()
            path = actions.start_git_clone(self.app, start_url, self.app.state.cancel_event)
            self.app.state.worker_future = self.app.executor.submit(actions._clone_repo_worker, start_url, path, self.app.log_queue, self.app.state.cancel_event, self.app.shutdown_event)
            return

        try:
            crawler_config = self.app.main_panel.get_crawler_config("dummy_dir_for_validation")
        except (ValueError, AttributeError):
            QMessageBox.critical(self.app, "Input Error", "Invalid input values for crawler configuration.")
            return

        msg = UITaskMessage(task=TaskType.DOWNLOAD)
        self.app.signals.message.emit(msg)

        self.app.state.cancel_event = threading.Event()
        self.app.worker_manager.start_queue_listener()

        actions.start_download(self.app, self.app.state.cancel_event)
        crawler_config = self.app.main_panel.get_crawler_config(self.app.state.temp_dir)
        self.app.state.worker_future = self.app.executor.submit(crawl_website, crawler_config, self.app.log_queue, self.app.state.cancel_event, self.app.shutdown_event)

    def start_package_task(self, file_list_for_count):
        if self.app.state.current_state != AppState.IDLE:
            self.app.log_verbose(f"[DIAG] start_package_task: Blocked by app state {self.app.state.current_state.name}")
            return

        msg = UITaskMessage(task=TaskType.PACKAGE)
        self.app.signals.message.emit(msg)

        is_web_mode = self.app.main_panel.web_crawl_radio.isChecked()
        if not is_web_mode:
            source_dir = self.app.main_panel.local_dir_ctrl.text().strip()
            if not source_dir or not Path(source_dir).is_dir():
                QMessageBox.critical(self.app, "Input Error", "Invalid local directory.")
                self.app.signals.message.emit(UITaskStopMessage(was_cancelled=False))
                return

        self.app.state.cancel_event = threading.Event()
        self.app.worker_manager.start_queue_listener()
        self.app.state.worker_future = self.app.executor.submit(actions.start_packaging, self.app, self.app.state.cancel_event, file_list_for_count)

    def stop_current_task(self):
        if self.app.state.current_state == AppState.TASK_RUNNING:
            if self.app.state.cancel_event:
                self.app.state.cancel_event.set()
                msg = UITaskStoppingMessage()
                self.app.signals.message.emit(msg)

    def handle_status(self, typed_msg: StatusMessage):
        status = typed_msg.status
        message = typed_msg.message

        if status == StatusType.ERROR:
            QMessageBox.critical(self.app, "An Error Occurred", message)
            self.app.signals.message.emit(LogMessage(message=message))
        elif status == StatusType.CLONE_COMPLETE:
            self.app.signals.message.emit(LogMessage(message="✔ Git clone successful."))
            self.app.signals.message.emit(GitCloneDoneMessage(path=typed_msg.path or ""))
        elif message:
            self.app.signals.message.emit(LogMessage(message=message))

        if status in [StatusType.SOURCE_COMPLETE, StatusType.PACKAGE_COMPLETE, StatusType.CANCELLED, StatusType.ERROR, StatusType.CLONE_COMPLETE]:
            if status == StatusType.PACKAGE_COMPLETE:
                self.app.signals.message.emit(ProgressMessage(value=100, max_value=100))
                self.app._open_output_folder()

            stop_msg = UITaskStopMessage(was_cancelled=status == StatusType.CANCELLED)
            self.app.signals.message.emit(stop_msg)

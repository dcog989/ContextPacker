import os
import threading
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

import core.actions as actions
from core.crawler import crawl_website
from .types import UITaskMessage, UITaskStopMessage, UITaskStoppingMessage, LogMessage, GitCloneDoneMessage, TaskType, ProgressMessage, StatusMessage, StatusType


class TaskHandler:
    def __init__(self, app_instance):
        self.app = app_instance

    def start_download_task(self):
        msg = UITaskMessage(task=TaskType.DOWNLOAD)
        self.app.signals.message.emit(msg)

        start_url = self.app.main_panel.start_url_widget.text().strip()

        # Security: Validate URL input to prevent injection attacks
        import re

        if not start_url:
            msg_text = "Start URL is required."
            QMessageBox.critical(self.app, "Input Error", msg_text)
            stop_msg = UITaskStopMessage(was_cancelled=False)
            self.app.signals.message.emit(stop_msg)
            return

        # Basic URL validation - allow http, https, and common git protocols
        url_pattern = r"^(https?://|git@|ssh://|file://)[a-zA-Z0-9._/-]+(:[0-9]+)?(/.*)?$"
        if not re.match(url_pattern, start_url):
            msg_text = "Invalid URL format. Please use a valid HTTP, HTTPS, or Git URL."
            QMessageBox.critical(self.app, "Input Error", msg_text)
            stop_msg = UITaskStopMessage(was_cancelled=False)
            self.app.signals.message.emit(stop_msg)
            return

        git_pattern = r"(\.git$)|(github\.com)|(gitlab\.com)|(bitbucket\.org)"
        if __import__("re").search(git_pattern, start_url):
            try:
                self.app.main_panel.get_crawler_config("dummy_dir_for_validation")
            except (ValueError, AttributeError):
                msg_text = "Invalid input. Please ensure 'Max Pages', 'Min Pause', and 'Max Pause' are whole numbers."
                QMessageBox.critical(self.app, "Input Error", msg_text)
                stop_msg = UITaskStopMessage(was_cancelled=False)
                self.app.signals.message.emit(stop_msg)
                return

            self.app.cancel_event = threading.Event()
            # The git clone is a blocking process, so we submit the worker directly
            path = actions.start_git_clone(self.app, start_url, self.app.cancel_event)
            self.app.worker_future = self.app.executor.submit(actions._clone_repo_worker, start_url, path, self.app.log_queue, self.app.cancel_event, self.app.shutdown_event)
            return

        try:
            self.app.main_panel.get_crawler_config("dummy_dir_for_validation")
        except (ValueError, AttributeError):
            msg_text = "Invalid input. Please ensure 'Max Pages', 'Min Pause', and 'Max Pause' are whole numbers."
            QMessageBox.critical(self.app, "Input Error", msg_text)
            stop_msg = UITaskStopMessage(was_cancelled=False)
            self.app.signals.message.emit(stop_msg)
            return

        self.app.cancel_event = threading.Event()
        self.app.worker_manager.start_queue_listener()

        # 1. Prepare/Cleanup temp directory
        actions.start_download(self.app, self.app.cancel_event)
        # 2. Get the config using the newly set temp_dir
        crawler_config = self.app.main_panel.get_crawler_config(self.app.temp_dir)
        # 3. Submit the crawling logic to the executor
        self.app.worker_future = self.app.executor.submit(crawl_website, crawler_config, self.app.log_queue, self.app.cancel_event, self.app.shutdown_event)

    def start_package_task(self, file_list_for_count):
        msg = UITaskMessage(task=TaskType.PACKAGE)
        self.app.signals.message.emit(msg)

        is_web_mode = self.app.main_panel.web_crawl_radio.isChecked()
        if not is_web_mode:
            source_dir = self.app.main_panel.local_dir_ctrl.text().strip()

            # Security: Validate directory path to prevent traversal attacks
            if not source_dir:
                msg_text = "Input directory is required."
                QMessageBox.critical(self.app, "Input Error", msg_text)
                stop_msg = UITaskStopMessage(was_cancelled=False)
                self.app.signals.message.emit(stop_msg)
                return

            try:
                # Resolve path and check for suspicious patterns
                resolved_path = Path(source_dir).resolve()

                # Verify directory exists and is accessible
                if not resolved_path.is_dir():
                    msg_text = f"The specified input directory is not valid:\n{source_dir}"
                    QMessageBox.critical(self.app, "Input Error", msg_text)
                    stop_msg = UITaskStopMessage(was_cancelled=False)
                    self.app.signals.message.emit(stop_msg)
                    return

                # Additional security: ensure we can read the directory
                if not os.access(resolved_path, os.R_OK):
                    msg_text = f"The specified directory is not readable:\n{source_dir}"
                    QMessageBox.critical(self.app, "Input Error", msg_text)
                    stop_msg = UITaskStopMessage(was_cancelled=False)
                    self.app.signals.message.emit(stop_msg)
                    return

            except (OSError, ValueError) as e:
                msg_text = f"Invalid directory path specified:\n{str(e)}"
                QMessageBox.critical(self.app, "Input Error", msg_text)
                stop_msg = UITaskStopMessage(was_cancelled=False)
                self.app.signals.message.emit(stop_msg)
                return

        self.app.cancel_event = threading.Event()
        self.app.worker_manager.start_queue_listener()
        # Submit packaging task to executor
        self.app.worker_future = self.app.executor.submit(actions.start_packaging, self.app, self.app.cancel_event, file_list_for_count)

    def stop_current_task(self):
        if self.app.cancel_event:
            self.app.cancel_event.set()
            msg = UITaskStoppingMessage()
            self.app.signals.message.emit(msg)

    # File: core/task_handler.py
    def handle_status(self, typed_msg: StatusMessage):
        status = typed_msg.status
        message = typed_msg.message

        if status == StatusType.ERROR:
            QMessageBox.critical(self.app, "An Error Occurred", message)
            log_msg = LogMessage(message=message)
            self.app.signals.message.emit(log_msg)
        elif status == StatusType.CLONE_COMPLETE:
            success_msg = LogMessage(message="✔ Git clone successful.")
            self.app.signals.message.emit(success_msg)
            # Fix: Handle Optional[str] by defaulting to empty string
            clone_msg = GitCloneDoneMessage(path=typed_msg.path or "")
            self.app.signals.message.emit(clone_msg)
        elif message:
            log_msg = LogMessage(message=message)
            self.app.signals.message.emit(log_msg)

        if status in [StatusType.SOURCE_COMPLETE, StatusType.PACKAGE_COMPLETE, StatusType.CANCELLED, StatusType.ERROR, StatusType.CLONE_COMPLETE]:
            if status == StatusType.PACKAGE_COMPLETE:
                progress_msg = ProgressMessage(value=100, max_value=100)
                self.app.signals.message.emit(progress_msg)
                self.app._open_output_folder()

            stop_msg = UITaskStopMessage(was_cancelled=status == StatusType.CANCELLED)
            self.app.signals.message.emit(stop_msg)

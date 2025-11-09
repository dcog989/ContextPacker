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
        self.app._toggle_ui_controls(False, widget_to_keep_enabled=dl_button)

        start_url = self.app.main_panel.start_url_ctrl.text()
        git_pattern = r"(\.git$)|(github\.com)|(gitlab\.com)|(bitbucket\.org)"
        if __import__("re").search(git_pattern, start_url):
            self.app.main_panel.copy_button.setEnabled(False)
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.app.is_task_running = True
            self.app.main_panel.package_button.setEnabled(False)
            self.app.main_panel.copy_button.setEnabled(False)
            dl_button.setText("Cloning...")
            self.app.cancel_event = threading.Event()
            actions.start_git_clone(self.app, self.app.cancel_event)
            return

        try:
            self.app.main_panel.get_crawler_config("dummy_dir_for_validation")
        except (ValueError, AttributeError):
            msg = "Invalid input. Please ensure 'Max Pages', 'Min Pause', and 'Max Pause' are whole numbers."
            QMessageBox.critical(self.app, "Input Error", msg)
            self.app._toggle_ui_controls(True)
            return

        self.app.main_panel.copy_button.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.app.is_task_running = True
        self.app.main_panel.package_button.setEnabled(False)
        self.app.main_panel.copy_button.setEnabled(False)
        dl_button.setText("Stop!")

        self.app.cancel_event = threading.Event()
        self.app.start_queue_listener()
        actions.start_download(self.app, self.app.cancel_event)

    def start_package_task(self, file_list_for_count):
        pkg_button = self.app.main_panel.package_button
        self.app._toggle_ui_controls(False, widget_to_keep_enabled=pkg_button)

        is_web_mode = self.app.main_panel.web_crawl_radio.isChecked()
        if not is_web_mode:
            source_dir = self.app.main_panel.local_dir_ctrl.text()
            if not source_dir or not Path(source_dir).is_dir():
                msg = f"The specified input directory is not valid:\n{source_dir}"
                QMessageBox.critical(self.app, "Input Error", msg)
                self.app._toggle_ui_controls(True)
                return

        self.app.main_panel.copy_button.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.app.is_task_running = True
        self.app.main_panel.download_button.setEnabled(False)
        self.app.main_panel.copy_button.setEnabled(False)
        pkg_button.setText("Stop!")

        self.app.cancel_event = threading.Event()
        self.app.start_queue_listener()
        actions.start_packaging(self.app, self.app.cancel_event, file_list_for_count)

    def stop_current_task(self):
        if self.app.cancel_event:
            self.app.cancel_event.set()

        dl_button = self.app.main_panel.download_button
        pkg_button = self.app.main_panel.package_button

        if dl_button.isEnabled():
            dl_button.setText("Stopping...")
            dl_button.setEnabled(False)

        if pkg_button.isEnabled():
            pkg_button.setText("Stopping...")
            pkg_button.setEnabled(False)

        self.app.log_verbose("Stopping process...")

    def handle_status(self, status, msg_obj):
        message = msg_obj.get("message", "")
        if status == "error":
            QMessageBox.critical(self.app, "An Error Occurred", message)
        elif status == "clone_complete":
            self.app.log_verbose("✔ Git clone successful.")
            self.app.main_panel.local_dir_ctrl.setText(msg_obj.get("path", ""))
            self.app.main_panel.web_crawl_radio.setChecked(False)
            self.app.main_panel.local_dir_radio.setChecked(True)
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
            QApplication.restoreOverrideCursor()
            self.app.is_task_running = False

        self.app.stop_queue_listener()
        self.app._toggle_ui_controls(True)

        self.app.worker_thread = None
        self.app.cancel_event = None

        if self.app.is_shutting_down:
            self.app.close()
            return

        dl_button = self.app.main_panel.download_button
        dl_button.setText("Download & Convert")
        dl_button.setEnabled(True)

        pkg_button = self.app.main_panel.package_button
        pkg_button.setText("Package")
        pkg_button.setEnabled(True)

        self.app.main_panel.progress_gauge.setValue(0)
        self.app._update_button_states()

        self.app.ui_update_timer.start()

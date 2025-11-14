import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QFileDialog, QApplication
from PySide6.QtCore import Qt
import threading

from core import actions
from core.types import LocalScanCompleteMessage, LogMessage, AppState
from core.app_message_handler import MessageHandler
from ui.about_dialog import AboutDialog


class UiController:
    """Handles logic for UI interactions, state updates, and initiating tasks."""

    def __init__(self, app_instance):
        self.app = app_instance
        self.message_handler: MessageHandler = self.app.message_handler

    def on_toggle_theme(self):
        self.app.theme_manager.toggle_theme()

    def on_toggle_input_mode(self):
        self.toggle_input_mode()

    def toggle_input_mode(self):
        is_url_mode = self.app.main_panel.web_crawl_radio.isChecked()
        self.app.main_panel.crawler_panel.setVisible(is_url_mode)
        self.app.main_panel.local_panel.setVisible(not is_url_mode)
        self.app.main_panel.toggle_output_view(is_web_mode=is_url_mode)
        if not is_url_mode:
            self.start_local_file_scan()
        self.app._update_button_states()

    def on_browse(self):
        path = QFileDialog.getExistingDirectory(self.app, "Choose a directory:")
        if path:
            self.app.main_panel.local_dir_ctrl.setText(path)
            self.start_local_file_scan()
        self.app._update_button_states()

    def on_local_filters_changed(self):
        self.app.exclude_update_timer.start()

    def on_exclude_text_update(self):
        self.app.exclude_update_timer.start()

    def on_download_button_click(self):
        if self.app.state.current_state == AppState.TASK_RUNNING:
            self.app.task_handler.stop_current_task()
        else:
            self.app.task_handler.start_download_task()

    def on_package_button_click(self):
        if self.app.state.current_state == AppState.TASK_RUNNING:
            self.app.task_handler.stop_current_task()
        else:
            file_list = self.app.main_panel.scraped_files if self.app.main_panel.web_crawl_radio.isChecked() else self.app.main_panel.local_files
            self.app.task_handler.start_package_task(file_list)

    def on_copy_to_clipboard(self):
        if not self.app.state.final_output_path or not self.app.Path(self.app.state.final_output_path).exists():
            self.app.log_verbose("ERROR: No output file found to copy.")
            return
        try:
            with open(self.app.state.final_output_path, "r", encoding="utf-8") as f:
                content = f.read()
            QApplication.clipboard().setText(content)
            self.app.log_verbose(f"Copied {len(content):,} characters to clipboard.")
        except Exception as e:
            self.app.log_verbose(f"ERROR: Failed to copy to clipboard: {e}")

    def on_batch_update_timer(self):
        self.message_handler.on_batch_update_timer()

    def _update_timestamp_label(self):
        from datetime import datetime

        try:
            if self.app.state.current_state == AppState.IDLE:
                ts = datetime.now().strftime("-%y%m%d-%H%M%S")
                self.app.main_panel.output_timestamp_label.setText(ts)
        except (RuntimeError, AttributeError):
            pass

    def _update_button_states(self):
        try:
            print(f"[DIAG] UiController._update_button_states: Entered. Current state: {self.app.state.current_state.name}")
            state = self.app.state.current_state
            is_web_mode = self.app.main_panel.web_crawl_radio.isChecked()

            # Default to disabled unless explicitly enabled
            dl_enabled = False
            pkg_enabled = False

            if state == AppState.IDLE:
                dl_enabled = is_web_mode
                package_ready = False
                if is_web_mode:
                    package_ready = bool(self.app.main_panel.scraped_files)
                else:
                    package_ready = bool(self.app.main_panel.local_dir_ctrl.text() and self.app.Path(self.app.main_panel.local_dir_ctrl.text()).is_dir())
                pkg_enabled = package_ready

            elif state == AppState.TASK_RUNNING:
                # Only the button that initiated the task is enabled, as a 'Stop' button
                if self.app.main_panel.download_button.text() == "Stop!":
                    dl_enabled = True
                elif self.app.main_panel.package_button.text() == "Stop!":
                    pkg_enabled = True

            # For all other states (TASK_STOPPING, TASK_FINISHING, UI_RESETTING), buttons remain disabled.

            self.app.main_panel.download_button.setEnabled(dl_enabled)
            self.app.main_panel.package_button.setEnabled(pkg_enabled)
            print(f"[DIAG] UiController._update_button_states: dl_enabled={dl_enabled}, pkg_enabled={pkg_enabled}")

            copy_ready = bool(self.app.state.final_output_path and self.app.Path(self.app.state.final_output_path).exists())
            self.app.main_panel.copy_button.setEnabled(copy_ready)
            print(f"[DIAG] UiController._update_button_states: copy_button.enabled = {copy_ready}")

            print("[DIAG] UiController._update_button_states: Exiting.")
        except (RuntimeError, AttributeError):
            print("[DIAG] UiController._update_button_states: Caught exception.")
            pass

    def start_local_file_scan(self):
        if self.app.state.local_scan_future and not self.app.state.local_scan_future.done():
            if self.app.state.local_scan_cancel_event:
                self.app.state.local_scan_cancel_event.set()

        self.app.state.local_scan_cancel_event = threading.Event()
        input_dir = self.app.main_panel.local_dir_ctrl.text()

        if not input_dir or not self.app.Path(input_dir).is_dir():
            self.app.main_panel.populate_local_file_list([])
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.app.main_panel.local_panel.setEnabled(False)
        self.app.state.local_files_to_exclude.clear()
        self.app.state.local_depth_excludes.clear()

        custom_excludes = [p.strip() for p in self.app.main_panel.local_exclude_ctrl.toPlainText().splitlines() if p.strip()]
        binary_excludes = self.app.BINARY_FILE_PATTERNS if self.app.main_panel.hide_binaries_check.isChecked() else []

        args = (input_dir, self.app.main_panel.dir_level_ctrl.value(), self.app.main_panel.use_gitignore_check.isChecked(), custom_excludes, binary_excludes, self.app.state.local_scan_cancel_event, self.app.state.gitignore_cache, self.app.state.gitignore_cache_lock)

        self.app.state.local_scan_future = self.app.worker_manager.executor.submit(self._local_scan_worker, *args)

    def _local_scan_worker(self, *args):
        cancel_event = args[5]
        try:
            results = actions.get_local_files(*args)
            if not cancel_event.is_set() and not self.app.worker_manager.shutdown_event.is_set():
                scan_msg = LocalScanCompleteMessage(results=results)
                self.app.signals.message.emit(scan_msg)
        except Exception as e:
            if not self.app.worker_manager.shutdown_event.is_set():
                error_msg = LogMessage(message=f"ERROR scanning directory: {e}")
                self.app.signals.message.emit(error_msg)
        finally:
            if cancel_event.is_set() and not self.app.worker_manager.shutdown_event.is_set():
                scan_msg = LocalScanCompleteMessage(results=None)
                self.app.signals.message.emit(scan_msg)

    def on_show_about_dialog(self):
        dialog = AboutDialog(self.app, self.app.version)
        dialog.exec()

from PySide6.QtWidgets import QFileDialog, QApplication
from PySide6.QtCore import Qt
import threading

import core.actions as actions
from core.types import LocalScanCompleteMessage, LogMessage
from core.app_message_handler import MessageHandler
from ui.about_dialog import AboutDialog


class UiController:
    """Handles logic for UI interactions, state updates, and initiating tasks."""

    def __init__(self, app_instance):
        self.app = app_instance
        self.message_handler: MessageHandler = self.app.message_handler

    def on_toggle_theme(self):
        """Toggles the theme mode's visual state (for icons) and updates colors."""
        self.app.theme_manager.toggle_theme()
        self.app.log_verbose(f"Theme toggled to: {'Dark' if self.app.theme_manager.is_dark_mode_visual_state else 'Light'}")

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
        if self.app.state.is_task_running:
            self.app.task_handler.stop_current_task()
        else:
            self.app.task_handler.start_download_task()

    def on_package_button_click(self):
        if self.app.state.is_task_running:
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
        """Delegates to message handler for batch processing."""
        self.message_handler.on_batch_update_timer()

    def _update_timestamp_label(self):
        from datetime import datetime

        if not self.app.state.is_task_running:
            ts = datetime.now().strftime("-%y%m%d-%H%M%S")
            self.app.main_panel.output_timestamp_label.setText(ts)

    def _update_button_states(self):
        is_web_mode = self.app.main_panel.web_crawl_radio.isChecked()
        package_ready = False
        copy_ready = bool(self.app.state.final_output_path and self.app.Path(self.app.state.final_output_path).exists())

        if is_web_mode:
            package_ready = bool(self.app.main_panel.scraped_files)
        else:
            package_ready = bool(self.app.main_panel.local_dir_ctrl.text() and self.app.Path(self.app.main_panel.local_dir_ctrl.text()).is_dir())
        self.app.main_panel.package_button.setEnabled(package_ready)
        self.app.main_panel.copy_button.setEnabled(copy_ready)

    def start_local_file_scan(self):
        """Initiates the local file scanning process in a worker thread."""
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

        # Submit task to ThreadPoolExecutor
        self.app.state.local_scan_future = self.app.worker_manager.executor.submit(self._local_scan_worker, *args)

    def _local_scan_worker(self, *args):
        """Worker wrapper for get_local_files to emit results back to main thread."""
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
        """Displays the About Dialog."""
        # Note: This version is the actual logic, called internally.
        dialog = AboutDialog(self.app, self.app.version)
        dialog.exec()

    def on_show_about_dialog_wrapper(self, event):
        """Wrapper to call the about dialog method from a mousePressEvent (with event arg)."""

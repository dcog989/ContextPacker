from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .types import LogMessage, StatusMessage, ProgressMessage, FileSavedMessage, UITaskMessage, UITaskStopMessage, UITaskStoppingMessage, GitCloneDoneMessage, LocalScanCompleteMessage, TaskType, dict_to_message


class MessageHandler:
    """Handles all messages received from the worker queue and updates the UI."""

    def __init__(self, app_instance):
        self.app = app_instance
        self.scraped_files_batch = []
        self.discovered_count_batch = 0
        self.max_batch_size = self.app.max_batch_size  # From core/constants.py via App
        self.ui_update_counter = 0
        self.ui_update_batch_size = self.app.ui_update_batch_size  # From core/constants.py via App

    def process_log_queue_message(self, msg_obj):
        """Processes a single message received from the worker queue."""
        # Ignore messages during shutdown to prevent race conditions
        if self.app.shutdown_event.is_set():
            return

        # Convert dictionary to typed message for better type safety
        typed_msg = dict_to_message(msg_obj)

        if isinstance(typed_msg, LogMessage):
            self.app.log_verbose(typed_msg.message)
        elif isinstance(typed_msg, FileSavedMessage):
            self._handle_file_saved(msg_obj, typed_msg)
        elif isinstance(typed_msg, ProgressMessage):
            self.app.main_panel.progress_gauge.setValue(typed_msg.value)
            self.app.main_panel.progress_gauge.setMaximum(typed_msg.max_value)
        elif isinstance(typed_msg, StatusMessage):
            self.app.task_handler.handle_status(typed_msg.status.value, msg_obj)
        elif isinstance(typed_msg, UITaskMessage):
            self._handle_ui_task_start(typed_msg.task.value)
        elif isinstance(typed_msg, UITaskStoppingMessage):
            self._handle_ui_task_stopping()
        elif isinstance(typed_msg, UITaskStopMessage):
            self._handle_ui_task_stop(typed_msg.was_cancelled)
        elif isinstance(typed_msg, GitCloneDoneMessage):
            self._handle_git_clone_done(typed_msg.path)
        elif isinstance(typed_msg, LocalScanCompleteMessage):
            self._handle_local_scan_complete(typed_msg)
        else:
            # Fallback for unknown message types
            self.app.log_verbose(str(msg_obj.get("message", "")))

    def _handle_file_saved(self, msg_obj, typed_msg):
        """Handles the FileSavedMessage, batching UI updates."""
        self.scraped_files_batch.append(msg_obj)

        # Proactive memory management: check batch size more frequently
        batch_size = len(self.scraped_files_batch)
        if batch_size >= self.max_batch_size:
            # Force immediate UI update to clear the batch
            self.app.main_panel.add_scraped_files_batch(self.scraped_files_batch)
            self.scraped_files_batch.clear()
            self.app.log_verbose(f"  -> Memory management: processed large batch of {self.max_batch_size} files")
        elif batch_size > self.max_batch_size * 0.8:  # Warning at 80% capacity
            self.app.log_verbose(f"  -> Warning: batch approaching limit ({batch_size}/{self.max_batch_size})")

        # Batch UI updates to reduce frame drops
        self.ui_update_counter += 1
        self.discovered_count_batch = max(self.discovered_count_batch, typed_msg.queue_size)

        # Only update UI every ui_update_batch_size files or on timer
        if self.ui_update_counter >= self.ui_update_batch_size:
            self.app.main_panel.update_discovered_count(self.discovered_count_batch)
            verbose_msg = f"  -> Saved: {typed_msg.filename} [{typed_msg.pages_saved}/{typed_msg.max_pages}]"
            self.app.log_verbose(verbose_msg)
            self.ui_update_counter = 0

    def on_batch_update_timer(self):
        """Processes the batch of scraped files on a timer tick."""
        if self.scraped_files_batch:
            self.app.main_panel.add_scraped_files_batch(self.scraped_files_batch)
            self.scraped_files_batch.clear()
            self.app._update_button_states()

        # Update discovered count on timer to ensure final count is displayed
        if self.discovered_count_batch > 0:
            self.app.main_panel.update_discovered_count(self.discovered_count_batch)

        # Reset counters
        self.ui_update_counter = 0

    def _handle_ui_task_start(self, task):
        """Updates UI state when a worker task starts."""
        dl_button = self.app.main_panel.download_button
        pkg_button = self.app.main_panel.package_button

        widget_to_keep_enabled = dl_button if task == TaskType.DOWNLOAD.value else pkg_button
        self.app._toggle_ui_controls(False, widget_to_keep_enabled=widget_to_keep_enabled)

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.app.is_task_running = True
        self.app.main_panel.copy_button.setEnabled(False)

        # Reset batching counters for new task
        self.ui_update_counter = 0
        self.discovered_count_batch = 0

        if task == TaskType.DOWNLOAD.value:
            dl_button.setText("Stop!")
            pkg_button.setEnabled(False)
        elif task == TaskType.PACKAGE.value:
            pkg_button.setText("Stop!")
            dl_button.setEnabled(False)

    def _handle_ui_task_stopping(self):
        """Updates UI state when a worker task is requested to stop."""
        dl_button = self.app.main_panel.download_button
        pkg_button = self.app.main_panel.package_button

        if dl_button.isEnabled():
            dl_button.setText("Stopping...")
            dl_button.setEnabled(False)

        if pkg_button.isEnabled():
            pkg_button.setText("Stopping...")
            pkg_button.setEnabled(False)

        self.app.log_verbose("Stopping process...")

    def _handle_ui_task_stop(self, was_cancelled):
        """Final UI update when a worker task completes or is cancelled."""
        if self.app.is_task_running:
            QApplication.restoreOverrideCursor()
            self.app.is_task_running = False

        self.app.worker_manager.stop_queue_listener(timeout=2.0)
        self.app._toggle_ui_controls(True)

        self.app.worker_future = None
        self.app.cancel_event = None

        if self.app.shutdown_event.is_set():
            self.app.close()
            return

        dl_button = self.app.main_panel.download_button
        dl_button.setText("Download && Convert")
        dl_button.setEnabled(True)

        pkg_button = self.app.main_panel.package_button
        pkg_button.setText("Package")
        pkg_button.setEnabled(True)

        if was_cancelled:
            self.app.main_panel.progress_gauge.setValue(0)
        self.app._update_button_states()

        self.app.ui_update_timer.start()

    def _handle_git_clone_done(self, path):
        """Switches to local mode and sets the cloned path."""
        self.app.main_panel.local_dir_ctrl.setText(path)
        self.app.main_panel.web_crawl_radio.setChecked(False)
        self.app.main_panel.local_dir_radio.setChecked(True)
        self.app.ui_controller.toggle_input_mode()

    def _handle_local_scan_complete(self, typed_msg):
        """Updates UI after local file scanning is complete."""
        QApplication.restoreOverrideCursor()
        self.app.main_panel.local_panel.setEnabled(True)
        self.app.local_scan_future = None
        if typed_msg.results is not None:
            files, depth_excludes = typed_msg.results
            self.app.main_panel.populate_local_file_list(files)
            self.app.local_depth_excludes = depth_excludes

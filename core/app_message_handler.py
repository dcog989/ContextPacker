import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.types import LogMessage, StatusMessage, ProgressMessage, FileSavedMessage, UITaskMessage, UITaskStopMessage, UITaskStoppingMessage, GitCloneDoneMessage, LocalScanCompleteMessage, TaskType, AppState


class MessageHandler:
    """Handles all messages received from the worker queue and updates the UI."""

    def __init__(self, app_instance):
        self.app = app_instance
        self.scraped_files_batch = []
        self.discovered_count_batch = 0
        self.max_batch_size = self.app.max_batch_size
        self.ui_update_counter = 0
        self.ui_update_batch_size = self.app.ui_update_batch_size

    def process_log_queue_message(self, typed_msg):
        if self.app.shutdown_event.is_set() or self.app._is_closing:
            return

        try:
            if isinstance(typed_msg, LogMessage):
                self.app.log_verbose(typed_msg.message)
            elif isinstance(typed_msg, FileSavedMessage):
                self._handle_file_saved(typed_msg)
            elif isinstance(typed_msg, ProgressMessage):
                try:
                    self.app.main_panel.progress_gauge.setValue(typed_msg.value)
                    self.app.main_panel.progress_gauge.setMaximum(typed_msg.max_value)
                except (RuntimeError, AttributeError):
                    pass
            elif isinstance(typed_msg, StatusMessage):
                self.app.task_handler.handle_status(typed_msg)
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
                self.app.log_verbose(str(typed_msg))
        except RuntimeError:
            pass

    def _handle_file_saved(self, typed_msg):
        msg_obj = {"type": typed_msg.type.value, "url": typed_msg.url, "filename": typed_msg.filename, "path": typed_msg.path, "pages_saved": typed_msg.pages_saved, "max_pages": typed_msg.max_pages, "queue_size": typed_msg.queue_size}
        self.scraped_files_batch.append(msg_obj)

        batch_size = len(self.scraped_files_batch)
        if batch_size >= self.max_batch_size:
            self.app.main_panel.add_scraped_files_batch(self.scraped_files_batch)
            self.scraped_files_batch.clear()

        self.ui_update_counter += 1
        self.discovered_count_batch = max(self.discovered_count_batch, typed_msg.queue_size)

        if self.ui_update_counter >= self.ui_update_batch_size:
            self.app.main_panel.update_discovered_count(self.discovered_count_batch)
            self.ui_update_counter = 0

    def on_batch_update_timer(self):
        if self.scraped_files_batch:
            try:
                self.app.main_panel.add_scraped_files_batch(self.scraped_files_batch)
                self.scraped_files_batch.clear()
                self.app._update_button_states()
            except (RuntimeError, AttributeError):
                pass

        if self.discovered_count_batch > 0:
            try:
                self.app.main_panel.update_discovered_count(self.discovered_count_batch)
            except (RuntimeError, AttributeError):
                pass

        self.ui_update_counter = 0

    def _handle_ui_task_start(self, task):
        self.app.log_verbose(f"[DIAG] State Transition: {self.app.state.current_state.name} -> TASK_RUNNING")
        self.app.state.current_state = AppState.TASK_RUNNING

        self.app._toggle_ui_controls(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        dl_button = self.app.main_panel.download_button
        pkg_button = self.app.main_panel.package_button

        if task == TaskType.DOWNLOAD.value:
            dl_button.setText("Stop!")
            dl_button.setEnabled(True)
            pkg_button.setEnabled(False)
        elif task == TaskType.PACKAGE.value:
            pkg_button.setText("Stop!")
            pkg_button.setEnabled(True)
            dl_button.setEnabled(False)

        self.ui_update_counter = 0
        self.discovered_count_batch = 0

    def _handle_ui_task_stopping(self):
        self.app.log_verbose(f"[DIAG] State Transition: {self.app.state.current_state.name} -> TASK_STOPPING")
        self.app.state.current_state = AppState.TASK_STOPPING

        dl_button = self.app.main_panel.download_button
        pkg_button = self.app.main_panel.package_button

        if dl_button.text() == "Stop!":
            dl_button.setText("Stopping...")
            dl_button.setEnabled(False)

        if pkg_button.text() == "Stop!":
            pkg_button.setText("Stopping...")
            pkg_button.setEnabled(False)

        self.app.log_verbose("Stopping process...")

    def _handle_ui_task_stop(self, was_cancelled):
        # This function executes the synchronous state machine for UI reset

        # 1. State: TASK_FINISHING
        self.app.log_verbose(f"[DIAG] State Transition: {self.app.state.current_state.name} -> TASK_FINISHING")
        self.app.state.current_state = AppState.TASK_FINISHING
        QApplication.restoreOverrideCursor()
        self.app._process_log_batch()  # Process final logs
        self.app.log_verbose("[DIAG] _handle_ui_task_stop: Forcing log widget repaint.")
        QApplication.processEvents()  # Force repaint of log widget

        # 2. State: UI_RESETTING
        self.app.log_verbose(f"[DIAG] State Transition: {self.app.state.current_state.name} -> UI_RESETTING")
        self.app.state.current_state = AppState.UI_RESETTING

        if self.app.state.worker_future:
            try:
                self.app.state.worker_future.result(timeout=0)
            except Exception:
                pass
        self.app.state.worker_future = None
        self.app.state.cancel_event = None

        if was_cancelled:
            self.app.main_panel.progress_gauge.setValue(0)

        self.app.main_panel.download_button.setText("Download && Convert")
        self.app.main_panel.package_button.setText("Package")

        self.app._toggle_ui_controls(True)  # Re-enable config controls
        self.app._update_button_states()  # Update buttons (will be disabled as state is not IDLE)
        self.app.log_verbose("[DIAG] _handle_ui_task_stop: Forcing config controls repaint.")
        QApplication.processEvents()  # Force repaint of re-enabled controls

        # 3. State: IDLE
        self.app.log_verbose(f"[DIAG] State Transition: {self.app.state.current_state.name} -> IDLE")
        self.app.state.current_state = AppState.IDLE
        self.app._update_button_states()  # Final update to enable action buttons
        self.app.ui_update_timer.start()

    def _handle_git_clone_done(self, path):
        self.app.main_panel.local_dir_ctrl.setText(path)
        self.app.main_panel.web_crawl_radio.setChecked(False)
        self.app.main_panel.local_dir_radio.setChecked(True)
        self.app.ui_controller.toggle_input_mode()

    def _handle_local_scan_complete(self, typed_msg):
        QApplication.restoreOverrideCursor()
        self.app.main_panel.local_panel.setEnabled(True)
        self.app.state.local_scan_future = None
        if typed_msg.results is not None:
            files, depth_excludes = typed_msg.results
            self.app.main_panel.populate_local_file_list(files)
            self.app.state.local_depth_excludes = depth_excludes

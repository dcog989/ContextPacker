from pathlib import Path
import re
import threading
from datetime import datetime
import logging

from PySide6.QtWidgets import QFileDialog, QApplication, QMessageBox
from PySide6.QtCore import Qt, QTimer
from pydantic import ValidationError

from . import actions
from .crawler import crawl_website
from .config import CrawlerConfig
from .types import AppState, StatusType, FileType, dict_to_file_info
from .signals import app_signals
from ui.about_dialog import AboutDialog


class UiController:
    """Handles UI logic, connects UI events to backend services, and updates the UI based on service signals."""

    def __init__(self, main_window, state_service, task_service, config_service, theme_manager):
        self.main_window = main_window
        self.state_service = state_service
        self.task_service = task_service
        self.config_service = config_service
        self.theme_manager = theme_manager

        # Timers for debouncing
        self.exclude_update_timer = QTimer()
        self.exclude_update_timer.setSingleShot(True)
        self.exclude_update_timer.setInterval(500)

        self.timestamp_timer = QTimer()
        self.timestamp_timer.setInterval(1000)

        # Batching for UI updates
        self.scraped_files_batch = []
        self.batch_update_timer = QTimer()
        self.batch_update_timer.setInterval(250)

        # State for local file scanning
        self.gitignore_cache = {}
        self.gitignore_cache_lock = threading.Lock()
        self.local_files_to_exclude = set()
        self.local_depth_excludes = set()

        logging.debug(f"[{threading.current_thread().name}] UiController initialized.")

    def __del__(self):
        logging.debug(f"[{threading.current_thread().name}] UiController being destroyed.")

    def setup_connections(self):
        """Connects all UI signals to controller slots and service signals to controller slots."""
        mw = self.main_window

        # --- Connect UI Widget Signals to Controller Slots ---
        mw.web_crawl_radio.toggled.connect(self.toggle_input_mode)
        mw.browse_button.clicked.connect(self.on_browse)
        mw.download_button.clicked.connect(self.on_download_button_click)
        mw.package_button.clicked.connect(self.on_package_button_click)
        mw.copy_button.clicked.connect(self.on_copy_to_clipboard)
        mw.delete_button.clicked.connect(self.on_delete_selected_item)
        mw.about_logo.mousePressEvent = lambda event: self.on_show_about_dialog()
        mw.about_text.mousePressEvent = lambda event: self.on_show_about_dialog()
        mw.theme_switch_button.clicked.connect(self.theme_manager.toggle_theme)

        # Connections to trigger button state updates
        mw.start_url_widget.textChanged.connect(self._update_button_states)

        # Connections for local file scanning triggers
        mw.use_gitignore_check.stateChanged.connect(self.exclude_update_timer.start)
        mw.hide_binaries_check.stateChanged.connect(self.exclude_update_timer.start)
        mw.dir_level_ctrl.valueChanged.connect(self.exclude_update_timer.start)
        mw.local_exclude_ctrl.textChanged.connect(self.exclude_update_timer.start)
        mw.local_dir_ctrl.textChanged.connect(self.exclude_update_timer.start)

        # Table selection
        mw.standard_log_list.itemSelectionChanged.connect(mw.update_delete_button_state)
        mw.local_file_list.itemSelectionChanged.connect(mw.update_delete_button_state)

        # --- Connect Timer Signals ---
        self.exclude_update_timer.timeout.connect(self.start_local_file_scan)
        self.timestamp_timer.timeout.connect(self._update_timestamp_label)
        self.batch_update_timer.timeout.connect(self.on_batch_update_timer)

        # --- Connect Service Signals to Controller Slots ---
        app_signals.state_changed.connect(self.on_state_changed)
        app_signals.task_status.connect(self.on_task_status)
        app_signals.task_progress.connect(self.on_task_progress)
        app_signals.file_saved.connect(self.on_file_saved)
        app_signals.git_clone_done.connect(self.on_git_clone_done)
        app_signals.local_scan_complete.connect(self.on_local_scan_complete)

        # --- Initial Setup ---
        self.timestamp_timer.start()
        self.batch_update_timer.start()
        self.toggle_input_mode()
        self.state_service.set_state(AppState.IDLE)  # Set initial state

    def connect_log_emitter(self, log_emitter):
        """Connect the log emitter's signal to the UI update slot."""
        log_emitter.log_received.connect(self.on_log_message)

    def cleanup(self):
        """Stops all running timers to ensure a clean shutdown."""
        logging.debug(f"[{threading.current_thread().name}] Cleaning up UiController timers.")
        self.exclude_update_timer.stop()
        self.timestamp_timer.stop()
        self.batch_update_timer.stop()

    # --- UI Action Slots ---

    def toggle_input_mode(self):
        is_url_mode = self.main_window.web_crawl_radio.isChecked()
        self.main_window.crawler_panel.setVisible(is_url_mode)
        self.main_window.local_panel.setVisible(not is_url_mode)
        self.main_window.toggle_output_view(is_web_mode=is_url_mode)
        if not is_url_mode:
            self.start_local_file_scan()
        self._update_button_states()

    def on_browse(self):
        path = QFileDialog.getExistingDirectory(self.main_window, "Choose a directory:")
        if path:
            self.main_window.local_dir_ctrl.setText(path)
            # Text changed signal will trigger the scan via the timer

    def on_download_button_click(self):
        if self.state_service.current_state == AppState.TASK_RUNNING:
            self.state_service.set_state(AppState.TASK_STOPPING)
            self.task_service.cancel_current_task()
        elif self.state_service.current_state == AppState.IDLE:
            self.start_download_task()

    def on_package_button_click(self):
        if self.state_service.current_state == AppState.TASK_RUNNING:
            self.state_service.set_state(AppState.TASK_STOPPING)
            self.task_service.cancel_current_task()
        elif self.state_service.current_state == AppState.IDLE:
            self.start_package_task()

    def on_copy_to_clipboard(self):
        path = self.state_service.final_output_path
        if not path or not Path(path).exists():
            logging.error("No output file found to copy.")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            QApplication.clipboard().setText(content)
            logging.info(f"Copied {len(content):,} characters to clipboard.")
        except Exception as e:
            logging.error(f"Failed to copy to clipboard: {e}")

    def on_delete_selected_item(self):
        mw = self.main_window
        is_web_mode = mw.web_crawl_radio.isChecked()
        list_widget = mw.standard_log_list if is_web_mode else mw.local_file_list
        selected_rows = sorted([index.row() for index in list_widget.selectionModel().selectedRows()], reverse=True)
        if not selected_rows:
            return

        for row in selected_rows:
            if is_web_mode:
                item_data = mw.scraped_files.pop(row)
                if item_data.get("path"):
                    try:
                        Path(item_data["path"]).unlink(missing_ok=True)
                    except OSError:
                        pass
            else:
                rel_path = mw.local_files[row]["rel_path"]
                self.local_files_to_exclude.add(rel_path)
                mw.local_files.pop(row)
            list_widget.removeRow(row)

        mw.update_delete_button_state()
        mw.update_file_count()
        self._update_button_states()

    def on_show_about_dialog(self):
        from core.version import __version__

        dialog = AboutDialog(self.main_window, __version__)
        dialog.exec()

    # --- Task Initiation ---

    def start_download_task(self):
        self.main_window.clear_logs()
        start_url = self.main_window.start_url_widget.text().strip()
        if not start_url:
            QMessageBox.critical(self.main_window, "Input Error", "Start URL is required.")
            return

        git_pattern = r"(\.git$)|(github\.com)|(gitlab\.com)|(bitbucket\.org)"
        if re.search(git_pattern, start_url):
            self.state_service.set_state(AppState.TASK_RUNNING)
            temp_dir = actions.create_session_dir()
            self.state_service.temp_dir = temp_dir
            logging.info(f"Cloning into: {temp_dir}")
            self.task_service.submit_task(actions.clone_repo_worker, url=start_url, path=temp_dir)
        else:
            try:
                config = self._get_crawler_config()
                self.state_service.set_state(AppState.TASK_RUNNING)
                self.task_service.submit_task(crawl_website, config=config)
            except ValueError as e:
                QMessageBox.critical(self.main_window, "Input Error", str(e))

    def start_package_task(self):
        self.main_window.progress_gauge.setValue(0)
        is_web_mode = self.main_window.web_crawl_radio.isChecked()
        source_dir = self.state_service.temp_dir if is_web_mode else self.main_window.local_dir_ctrl.text()

        if not source_dir or not Path(source_dir).is_dir():
            QMessageBox.critical(self.main_window, "Input Error", "Valid source directory is required.")
            return

        filename_prefix = self.main_window.output_filename_ctrl.text().strip() or "ContextPacker-package"
        extension = self.main_window.output_format_choice.currentText()
        downloads_path = actions.get_downloads_folder()
        timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
        output_basename = f"{filename_prefix}-{timestamp}{extension}"
        output_path = str(Path(downloads_path) / output_basename)
        self.state_service.final_output_path = output_path

        style_map = {".md": "markdown", ".txt": "plain", ".xml": "xml"}
        repomix_style = style_map.get(extension, "markdown")

        if is_web_mode:
            exclude_patterns = []
            total_files = len(self.main_window.scraped_files)
        else:
            default_excludes = [p.strip() for p in self.main_window.local_exclude_ctrl.toPlainText().splitlines() if p.strip()]
            exclude_patterns = list(set(default_excludes) | self.local_files_to_exclude | self.local_depth_excludes)
            total_files = len([f for f in self.main_window.local_files if dict_to_file_info(f).type == FileType.FILE])

        self.state_service.set_state(AppState.TASK_RUNNING)
        self.task_service.submit_task(
            actions.packaging_worker,
            source_dir=source_dir,
            output_path=output_path,
            repomix_style=repomix_style,
            exclude_patterns=exclude_patterns,
            total_files=total_files,
        )

    def start_local_file_scan(self):
        if self.task_service.is_task_running():  # Don't scan if another task is running
            return

        input_dir = self.main_window.local_dir_ctrl.text()
        if not input_dir or not Path(input_dir).is_dir():
            self.main_window.populate_local_file_list([])
            self._update_button_states()  # Ensure package button is disabled if path becomes invalid
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.main_window.local_panel.setEnabled(False)
        self.local_files_to_exclude.clear()
        self.local_depth_excludes.clear()

        binary_excludes = self.config_service.get("binary_file_patterns", []) if self.main_window.hide_binaries_check.isChecked() else []

        # This task does not use the main state machine, as it's a lightweight UI feedback task.
        # We manually manage UI feedback (cursor, panel enabled state).
        self.task_service.submit_task(
            actions.get_local_files_worker,
            root_dir=input_dir,
            max_depth=self.main_window.dir_level_ctrl.value(),
            use_gitignore=self.main_window.use_gitignore_check.isChecked(),
            custom_excludes=[p.strip() for p in self.main_window.local_exclude_ctrl.toPlainText().splitlines() if p.strip()],
            binary_excludes=binary_excludes,
            gitignore_cache=self.gitignore_cache,
            gitignore_cache_lock=self.gitignore_cache_lock,
        )

    # --- Service Signal Slots ---

    def on_state_changed(self, new_state: AppState):
        self._update_ui_for_state(new_state)

    def on_log_message(self, message: str):
        mw = self.main_window
        mw.verbose_log_widget.append(message)
        mw.manage_log_size()

    def on_task_status(self, status_msg):
        if status_msg.status == StatusType.ERROR:
            QMessageBox.critical(self.main_window, "An Error Occurred", status_msg.message)
            logging.error(status_msg.message)
        elif status_msg.message:
            logging.info(status_msg.message)

        if status_msg.status in [StatusType.SOURCE_COMPLETE, StatusType.PACKAGE_COMPLETE, StatusType.CANCELLED, StatusType.ERROR, StatusType.CLONE_COMPLETE]:
            if status_msg.status == StatusType.PACKAGE_COMPLETE:
                self.main_window.progress_gauge.setValue(100)
                if self.state_service.final_output_path:
                    output_dir = Path(self.state_service.final_output_path).parent
                    self.task_service.submit_task(actions.open_folder_worker, folder_path=str(output_dir))
            self.state_service.set_state(AppState.IDLE)

    def on_task_progress(self, progress_msg):
        self.main_window.progress_gauge.setValue(progress_msg.value)
        self.main_window.progress_gauge.setMaximum(progress_msg.max_value)

    def on_file_saved(self, file_msg):
        self.scraped_files_batch.append(file_msg.__dict__)
        self.main_window.update_discovered_count(file_msg.queue_size)

    def on_git_clone_done(self, done_msg):
        self.main_window.local_dir_ctrl.setText(done_msg.path)
        self.main_window.web_crawl_radio.setChecked(False)
        self.main_window.local_dir_radio.setChecked(True)
        self.toggle_input_mode()

    def on_local_scan_complete(self, scan_msg):
        QApplication.restoreOverrideCursor()
        self.main_window.local_panel.setEnabled(True)
        if scan_msg.results:
            files, depth_excludes = scan_msg.results
            self.main_window.populate_local_file_list(files)
            self.local_depth_excludes = depth_excludes
        # Explicitly update button states now that the scan is complete and the list is populated.
        self._update_button_states()

    # --- UI Update and Helpers ---

    def on_batch_update_timer(self):
        if self.scraped_files_batch:
            self.main_window.add_scraped_files_batch(self.scraped_files_batch)
            self.scraped_files_batch.clear()
            self._update_button_states()

    def _update_timestamp_label(self):
        if self.state_service.current_state == AppState.IDLE:
            ts = datetime.now().strftime("-%y%m%d-%H%M%S")
            self.main_window.output_timestamp_label.setText(ts)

    def _update_ui_for_state(self, new_state: AppState):
        mw = self.main_window
        if new_state == AppState.IDLE:
            QApplication.restoreOverrideCursor()
            self._toggle_all_controls(True)
            mw.download_button.setText("Download && Convert")
            mw.package_button.setText("Package")
        elif new_state == AppState.TASK_RUNNING:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self._toggle_all_controls(False)
            is_web_mode = mw.web_crawl_radio.isChecked() or mw.download_button.text() == "Stop!"
            if mw.start_url_widget.text() and is_web_mode:
                mw.download_button.setText("Stop!")
                mw.download_button.setEnabled(True)
            else:
                mw.package_button.setText("Stop!")
                mw.package_button.setEnabled(True)
        elif new_state == AppState.TASK_STOPPING:
            mw.download_button.setText("Stopping...")
            mw.package_button.setText("Stopping...")
            mw.download_button.setEnabled(False)
            mw.package_button.setEnabled(False)

        self._update_button_states()

    def _toggle_all_controls(self, enable):
        widgets = [
            self.main_window.system_panel,
            self.main_window.web_crawl_radio,
            self.main_window.local_dir_radio,
            self.main_window.crawler_panel,
            self.main_window.local_panel,
            self.main_window.output_filename_ctrl,
            self.main_window.output_format_choice,
            self.main_window.package_button,
            self.main_window.download_button,
            self.main_window.delete_button,
            self.main_window.theme_switch_button,
        ]
        for widget in widgets:
            widget.setEnabled(enable)

    def _update_button_states(self):
        state = self.state_service.current_state
        mw = self.main_window
        is_web_mode = mw.web_crawl_radio.isChecked()

        dl_enabled, pkg_enabled = False, False

        if state == AppState.IDLE:
            dl_enabled = is_web_mode and bool(mw.start_url_widget.text())
            if is_web_mode:
                pkg_enabled = bool(mw.scraped_files)
            else:  # Local mode
                pkg_enabled = bool(mw.local_dir_ctrl.text() and Path(mw.local_dir_ctrl.text()).is_dir())

        elif state == AppState.TASK_RUNNING:
            # Re-enable the one that's the "Stop" button
            if mw.download_button.text() == "Stop!":
                dl_enabled = True
            if mw.package_button.text() == "Stop!":
                pkg_enabled = True

        mw.download_button.setEnabled(dl_enabled)
        mw.package_button.setEnabled(pkg_enabled)

        copy_ready = bool(self.state_service.final_output_path and Path(self.state_service.final_output_path).exists())
        mw.copy_button.setEnabled(copy_ready)

    def _get_crawler_config(self) -> CrawlerConfig:
        mw = self.main_window
        try:
            temp_dir = actions.create_session_dir()
            self.state_service.temp_dir = temp_dir

            # Pydantic will handle string-to-number conversions automatically
            config_data = {
                "start_url": mw.start_url_widget.text().strip(),
                "output_dir": temp_dir,
                "max_pages": mw.max_pages_ctrl.text(),
                "min_pause": int(mw.min_pause_ctrl.text()) / 1000.0,  # Convert from ms
                "max_pause": int(mw.max_pause_ctrl.text()) / 1000.0,  # Convert from ms
                "crawl_depth": mw.crawl_depth_ctrl.value(),
                "stay_on_subdomain": mw.stay_on_subdomain_check.isChecked(),
                "ignore_queries": mw.ignore_queries_check.isChecked(),
                "user_agent": mw.user_agent_widget.currentText(),
                "include_paths": [p.strip() for p in mw.include_paths_widget.toPlainText().splitlines() if p.strip()],
                "exclude_paths": [p.strip() for p in mw.exclude_paths_widget.toPlainText().splitlines() if p.strip()],
            }
            if not config_data["start_url"]:
                raise ValueError("Start URL is required.")

            return CrawlerConfig(**config_data)
        except ValidationError as e:
            # Pydantic provides user-friendly error messages
            raise ValueError(f"Invalid crawler configuration:\n{e}")
        except (ValueError, TypeError):
            # This will catch int() conversion on empty strings for pause values
            raise ValueError("Invalid crawler configuration: Pause values must be valid numbers.")

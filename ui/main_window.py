from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QGroupBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QCheckBox,
    QPushButton,
    QTableWidget,
    QProgressBar,
    QTableWidgetItem,
    QMenu,
    QApplication,
)
from PySide6.QtCore import Qt, QByteArray, QTimer
from PySide6.QtGui import QAction, QShortcut, QKeySequence

from core.constants import DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, MAX_LOG_LINES, UI_TABLE_INSERT_CHUNK_SIZE
from ui.input_panels import InputPanelFactory
from ui.output_panels import OutputPanelFactory


class MainWindow(QWidget):
    def __init__(self, config_service):
        super().__init__()
        self.config_service = config_service
        self.scraped_files = []
        self.local_files = []
        self._managing_log_size = False  # Guard against recursive calls
        self._batch_insert_in_progress = False
        self._pending_batch = []
        self._local_insert_generator = None

        # Initialize Factory instances, passing config data
        self.input_factory = InputPanelFactory(self, self.config_service.config)
        self.output_factory = OutputPanelFactory(self, self.config_service.config)

        # Explicitly declare all UI widgets for static analysis and clarity
        self.system_panel: QGroupBox
        self.about_logo: QLabel
        self.about_text: QLabel
        self.theme_switch_button: QPushButton
        self.save_profile_button: QPushButton
        self.load_profile_button: QPushButton
        self.crawler_panel: QWidget
        self.start_url_widget: QLineEdit
        self.user_agent_widget: QComboBox
        self.max_pages_ctrl: QLineEdit
        self.crawl_depth_ctrl: QSpinBox
        self.min_pause_ctrl: QLineEdit
        self.max_pause_ctrl: QLineEdit
        self.include_paths_widget: QTextEdit
        self.exclude_paths_widget: QTextEdit
        self.stay_on_subdomain_check: QCheckBox
        self.ignore_queries_check: QCheckBox
        self.download_button: QPushButton
        self.local_panel: QWidget
        self.local_dir_ctrl: QLineEdit
        self.browse_button: QPushButton
        self.local_exclude_ctrl: QTextEdit
        self.use_gitignore_check: QCheckBox
        self.hide_binaries_check: QCheckBox
        self.dir_level_ctrl: QSpinBox
        self.list_group: QGroupBox
        self.list_stack_layout: QVBoxLayout
        self.standard_log_list: QTableWidget
        self.local_file_list: QTableWidget
        self.progress_gauge: QProgressBar
        self.file_count_label: QLabel
        self.delete_button: QPushButton
        self.log_group: QGroupBox
        self.verbose_log_widget: QTextEdit
        self.output_group: QGroupBox
        self.output_filename_ctrl: QLineEdit
        self.output_timestamp_label: QLabel
        self.output_format_choice: QComboBox
        self.package_button: QPushButton
        self.copy_button: QPushButton
        self.input_group: QGroupBox
        self.web_crawl_radio: QRadioButton
        self.local_dir_radio: QRadioButton
        self.h_splitter: QSplitter
        self.v_splitter: QSplitter

        self._create_widgets()
        self._create_layout()
        self._create_context_menus()

        self.toggle_output_view(is_web_mode=True)
        self.max_log_lines = MAX_LOG_LINES

    def _create_widgets(self):
        w = self.input_factory.create_system_panel()
        self.system_panel = w["system_panel"]
        self.about_logo = w["about_logo"]
        self.about_text = w["about_text"]
        self.theme_switch_button = w["theme_switch_button"]
        self.save_profile_button = w["save_profile_button"]
        self.load_profile_button = w["load_profile_button"]

        w = self.input_factory.create_crawler_panel()
        self.crawler_panel = w["crawler_panel"]
        self.start_url_widget = w["start_url_widget"]
        self.user_agent_widget = w["user_agent_widget"]
        self.max_pages_ctrl = w["max_pages_ctrl"]
        self.crawl_depth_ctrl = w["crawl_depth_ctrl"]
        self.min_pause_ctrl = w["min_pause_ctrl"]
        self.max_pause_ctrl = w["max_pause_ctrl"]
        self.include_paths_widget = w["include_paths_widget"]
        self.exclude_paths_widget = w["exclude_paths_widget"]
        self.stay_on_subdomain_check = w["stay_on_subdomain_check"]
        self.ignore_queries_check = w["ignore_queries_check"]
        self.download_button = w["download_button"]

        w = self.input_factory.create_local_panel()
        self.local_panel = w["local_panel"]
        self.local_dir_ctrl = w["local_dir_ctrl"]
        self.browse_button = w["browse_button"]
        self.local_exclude_ctrl = w["local_exclude_ctrl"]
        self.use_gitignore_check = w["use_gitignore_check"]
        self.hide_binaries_check = w["hide_binaries_check"]
        self.dir_level_ctrl = w["dir_level_ctrl"]

        w = self.output_factory.create_list_log_widgets()
        self.list_group = w["list_group"]
        self.list_stack_layout = w["list_stack_layout"]
        self.standard_log_list = w["standard_log_list"]
        self.local_file_list = w["local_file_list"]
        self.progress_gauge = w["progress_gauge"]
        self.file_count_label = w["file_count_label"]
        self.delete_button = w["delete_button"]
        self.log_group = w["log_group"]
        self.verbose_log_widget = w["verbose_log_widget"]

        w = self.output_factory.create_output_group()
        self.output_group = w["output_group"]
        self.output_filename_ctrl = w["output_filename_ctrl"]
        self.output_timestamp_label = w["output_timestamp_label"]
        self.output_format_choice = w["output_format_choice"]
        self.package_button = w["package_button"]
        self.copy_button = w["copy_button"]

        self.input_group = QGroupBox("Input")
        self.web_crawl_radio = QRadioButton("Web Crawl")
        self.local_dir_radio = QRadioButton("Local Directory")
        self.web_crawl_radio.setChecked(True)

    def _create_layout(self):
        main_layout = QHBoxLayout(self)
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.h_splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(self.input_group)
        left_layout.addWidget(self.system_panel)
        self.h_splitter.addWidget(left_widget)

        input_layout = QVBoxLayout(self.input_group)
        radio_layout = QHBoxLayout()
        radio_layout.setContentsMargins(10, 10, 0, 0)
        radio_layout.setSpacing(15)
        radio_layout.addWidget(self.web_crawl_radio)
        radio_layout.addWidget(self.local_dir_radio)
        radio_layout.addStretch()
        input_layout.addLayout(radio_layout)
        input_layout.addWidget(self.crawler_panel)
        input_layout.addWidget(self.local_panel)
        self.local_panel.hide()

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)

        list_wrapper = QWidget()
        list_wrapper_layout = QVBoxLayout(list_wrapper)
        list_wrapper_layout.setContentsMargins(0, 0, 0, 5)
        list_wrapper_layout.addWidget(self.list_group)
        self.v_splitter.addWidget(list_wrapper)
        self.v_splitter.addWidget(self.log_group)

        right_layout.addWidget(self.v_splitter)
        right_layout.addWidget(self.output_group)
        self.h_splitter.addWidget(right_widget)

        self._restore_splitter_states()

    def _restore_splitter_states(self):
        h_state = self.config_service.get("h_sash_state")
        if h_state:
            self.h_splitter.restoreState(QByteArray.fromBase64(h_state.encode("utf-8")))
        else:
            total_width = self.width() if self.width() > 0 else DEFAULT_WINDOW_WIDTH
            self.h_splitter.setSizes([total_width // 2, total_width // 2])

        v_state = self.config_service.get("v_sash_state")
        if v_state:
            self.v_splitter.restoreState(QByteArray.fromBase64(v_state.encode("utf-8")))
        else:
            total_height = self.height() if self.height() > 0 else DEFAULT_WINDOW_HEIGHT
            self.v_splitter.setSizes([total_height // 2, total_height // 2])

    def _create_context_menus(self):
        self.verbose_log_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verbose_log_widget.customContextMenuRequested.connect(self.show_log_context_menu)

        self.standard_log_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.standard_log_list.customContextMenuRequested.connect(self.show_table_context_menu)
        self.local_file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.local_file_list.customContextMenuRequested.connect(self.show_table_context_menu)

        for table in [self.standard_log_list, self.local_file_list]:
            sc = QShortcut(QKeySequence.StandardKey.Copy, table)
            sc.setContext(Qt.ShortcutContext.WidgetShortcut)
            sc.activated.connect(self.copy_selected_table_rows)

    def show_log_context_menu(self, position):
        context_menu = QMenu(self)
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self.verbose_log_widget.copy())
        context_menu.addAction(copy_action)
        context_menu.addSeparator()
        clear_action = QAction("Clear Log", self)
        clear_action.triggered.connect(self.clear_logs)
        context_menu.addAction(clear_action)
        context_menu.exec(self.verbose_log_widget.mapToGlobal(position))

    def show_table_context_menu(self, position):
        table = self.sender()
        context_menu = QMenu(self)
        copy_action = QAction("Copy Selected", self)
        copy_action.triggered.connect(self.copy_selected_table_rows)
        context_menu.addAction(copy_action)
        delete_action = QAction("Delete Selected", self)
        delete_action.triggered.connect(self.delete_button.click)
        context_menu.addAction(delete_action)
        context_menu.exec(table.mapToGlobal(position))

    def copy_selected_table_rows(self):
        table = self.standard_log_list if self.standard_log_list.isVisible() else self.local_file_list
        selection = table.selectedIndexes()
        if not selection:
            return

        rows = set()
        cols = set()
        cells = {}
        for idx in selection:
            row, col = idx.row(), idx.column()
            rows.add(row)
            cols.add(col)
            cells[(row, col)] = idx.data(Qt.ItemDataRole.DisplayRole) or ""

        if not rows:
            return

        col_order = sorted(cols)
        lines = []
        for row in sorted(rows):
            lines.append("\t".join(cells.get((row, col), "") for col in col_order))

        QApplication.clipboard().setText("\n".join(lines))

    def toggle_output_view(self, is_web_mode):
        self.local_file_list.setVisible(not is_web_mode)
        self.standard_log_list.setVisible(is_web_mode)
        self.progress_gauge.setValue(0)
        self.progress_gauge.setVisible(is_web_mode)
        self.update_delete_button_state()
        self.update_stats_label()

    def add_scraped_files_batch(self, files_data):
        if not files_data:
            return
        if self._batch_insert_in_progress:
            self._pending_batch.extend(files_data)
            return
        self._batch_insert_in_progress = True
        self.standard_log_list.setSortingEnabled(False)
        self.standard_log_list.blockSignals(True)
        self.insertion_generator = iter(files_data)
        self.batch_insert_step()

    def batch_insert_step(self):
        for _ in range(UI_TABLE_INSERT_CHUNK_SIZE):
            try:
                file_data = next(self.insertion_generator)
                row = self.standard_log_list.rowCount()
                self.standard_log_list.insertRow(row)
                self.scraped_files.append(file_data)
                url_item = QTableWidgetItem(file_data["url"])
                url_item.setToolTip(file_data["url"])
                self.standard_log_list.setItem(row, 0, url_item)
                name_item = QTableWidgetItem(file_data["filename"])
                name_item.setToolTip(file_data["filename"])
                self.standard_log_list.setItem(row, 1, name_item)
            except StopIteration:
                self.standard_log_list.blockSignals(False)
                self.standard_log_list.setSortingEnabled(True)
                self._batch_insert_in_progress = False
                if self._pending_batch:
                    pending = self._pending_batch[:]
                    self._pending_batch.clear()
                    self.add_scraped_files_batch(pending)
                return
        QTimer.singleShot(0, self.batch_insert_step)

    def populate_local_file_list(self, files):
        self.local_file_list.setSortingEnabled(False)
        self.local_file_list.setRowCount(0)
        self.local_files = files
        self._local_insert_generator = iter(files)
        self.local_batch_insert_step()

    def local_batch_insert_step(self):
        for _ in range(UI_TABLE_INSERT_CHUNK_SIZE):
            try:
                f = next(self._local_insert_generator)
                row = self.local_file_list.rowCount()
                self.local_file_list.insertRow(row)
                name_item = QTableWidgetItem(f["name"])
                name_item.setToolTip(f["name"])
                self.local_file_list.setItem(row, 0, name_item)
                self.local_file_list.setItem(row, 1, QTableWidgetItem(f["type"]))
                size_item = QTableWidgetItem(f["size_str"])
                size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.local_file_list.setItem(row, 2, size_item)
            except StopIteration:
                self.local_file_list.setSortingEnabled(True)
                self.local_file_list.sortByColumn(1, Qt.SortOrder.DescendingOrder)
                self._local_insert_generator = None
                self.update_stats_label()
                return
        QTimer.singleShot(0, self.local_batch_insert_step)

    def update_delete_button_state(self):
        list_widget = self.standard_log_list if self.standard_log_list.isVisible() else self.local_file_list
        is_enabled = list_widget.selectionModel().hasSelection() if list_widget else False
        self.delete_button.setEnabled(is_enabled)

    def clear_logs(self):
        self.verbose_log_widget.clear()
        self.standard_log_list.setRowCount(0)
        self.scraped_files.clear()
        self.update_delete_button_state()
        self.update_stats_label()

    def manage_log_size(self):
        if self._managing_log_size:
            return
        self._managing_log_size = True
        try:
            document = self.verbose_log_widget.document()
            if document and document.blockCount() > self.max_log_lines:
                lines_to_remove = document.blockCount() // 4
                cursor = self.verbose_log_widget.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.movePosition(cursor.MoveOperation.NextBlock, cursor.MoveMode.KeepAnchor, lines_to_remove)
                cursor.removeSelectedText()
        finally:
            self._managing_log_size = False

    def update_web_crawl_stats(self, saved_count, total_count):
        """Updates the label with web crawl specific stats."""
        if total_count > 0:
            label = f"{saved_count} saved / {total_count} discovered"
            self.file_count_label.setText(label)
        else:
            self.file_count_label.setText("")

    def update_stats_label(self):
        """Updates the file count label based on the current view mode."""
        if self.local_file_list.isVisible():
            count = len(self.local_files)
            if count > 0:
                label = f"{count} item(s)"
                self.file_count_label.setText(label)
            else:
                self.file_count_label.setText("")
        else:
            count = len(self.scraped_files)
            if count > 0:
                self.file_count_label.setText(f"{count} file(s)")
            else:
                self.file_count_label.setText("")

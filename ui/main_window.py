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
)
from PySide6.QtCore import Qt, QByteArray, QTimer
from PySide6.QtGui import QAction

from core.constants import MAX_LOG_LINES, UI_TABLE_INSERT_CHUNK_SIZE
from ui.input_panels import InputPanelFactory
from ui.output_panels import OutputPanelFactory


class MainWindow(QWidget):
    def __init__(self, config_service):
        super().__init__()
        self.config_service = config_service
        self.scraped_files = []
        self.local_files = []
        self._managing_log_size = False  # Guard against recursive calls

        # Initialize Factory instances, passing config data
        self.input_factory = InputPanelFactory(self, self.config_service.config)
        self.output_factory = OutputPanelFactory(self, self.config_service.config)

        # Explicitly declare all UI widgets for static analysis and clarity
        self.system_panel: QGroupBox
        self.about_logo: QLabel
        self.about_text: QLabel
        self.theme_switch_button: QPushButton
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

    def _assign_widgets_from_dict(self, widgets_dict):
        for key, value in widgets_dict.items():
            setattr(self, key, value)

    def _create_widgets(self):
        system_widgets = self.input_factory.create_system_panel()
        crawler_widgets = self.input_factory.create_crawler_panel()
        local_widgets = self.input_factory.create_local_panel()
        list_log_widgets = self.output_factory.create_list_log_widgets()
        output_widgets = self.output_factory.create_output_group()

        self._assign_widgets_from_dict(system_widgets)
        self._assign_widgets_from_dict(crawler_widgets)
        self._assign_widgets_from_dict(local_widgets)
        self._assign_widgets_from_dict(list_log_widgets)
        self._assign_widgets_from_dict(output_widgets)

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
            total_width = self.width() if self.width() > 0 else 1600
            self.h_splitter.setSizes([total_width // 2, total_width // 2])

        v_state = self.config_service.get("v_sash_state")
        if v_state:
            self.v_splitter.restoreState(QByteArray.fromBase64(v_state.encode("utf-8")))
        else:
            total_height = self.height() if self.height() > 0 else 950
            self.v_splitter.setSizes([total_height // 2, total_height // 2])

    def _create_context_menus(self):
        self.verbose_log_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verbose_log_widget.customContextMenuRequested.connect(self.show_log_context_menu)

    def show_log_context_menu(self, position):
        context_menu = QMenu(self)
        clear_action = QAction("Clear Log", self)
        clear_action.triggered.connect(self.clear_logs)
        context_menu.addAction(clear_action)
        context_menu.exec(self.verbose_log_widget.mapToGlobal(position))

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
                self.standard_log_list.setItem(row, 0, QTableWidgetItem(file_data["url"]))
                self.standard_log_list.setItem(row, 1, QTableWidgetItem(file_data["filename"]))
            except StopIteration:
                self.standard_log_list.blockSignals(False)
                self.standard_log_list.setSortingEnabled(True)
                self.update_stats_label()
                return
        QTimer.singleShot(0, self.batch_insert_step)
        self.update_stats_label()

    def populate_local_file_list(self, files):
        self.local_file_list.setSortingEnabled(False)
        self.local_file_list.setRowCount(0)
        self.local_files = files
        for f in files:
            row = self.local_file_list.rowCount()
            self.local_file_list.insertRow(row)
            self.local_file_list.setItem(row, 0, QTableWidgetItem(f["name"]))
            self.local_file_list.setItem(row, 1, QTableWidgetItem(f["type"]))
            size_item = QTableWidgetItem(f["size_str"])
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.local_file_list.setItem(row, 2, size_item)
        self.local_file_list.setSortingEnabled(True)
        self.local_file_list.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        self.update_stats_label()

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
            # For web crawl, the stats are pushed from the controller,
            # so we only clear it if there are no files.
            if not self.scraped_files:
                self.file_count_label.setText("")

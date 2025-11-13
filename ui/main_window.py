from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QLabel, QLineEdit, QRadioButton, QComboBox, QSpinBox, QTextEdit, QCheckBox, QPushButton, QTableWidget, QProgressBar, QTableWidgetItem
from PySide6.QtCore import Qt, QByteArray

from core.config import CrawlerConfig
from core.config_manager import get_config
from core.constants import MAX_LOG_LINES
from ui.input_panels import InputPanelFactory
from ui.output_panels import OutputPanelFactory


config = get_config()


class MainWindow(QWidget):
    def __init__(self, parent_app):
        super().__init__()
        self.app = parent_app
        self.scraped_files = []
        self.local_files = []
        self.discovered_url_count = 0

        # Initialize Factory instances
        self.input_factory = InputPanelFactory(self)
        self.output_factory = OutputPanelFactory(self)

        # Explicitly declare widgets to satisfy Pylance/linters
        # These will be assigned in create_widgets()
        self.system_panel = QWidget()
        self.input_group = QGroupBox()
        self.web_crawl_radio = QRadioButton()
        self.local_dir_radio = QRadioButton()
        self.crawler_panel = QWidget()
        self.local_panel = QWidget()

        self.list_group = QGroupBox()
        self.log_group = QGroupBox()
        self.output_group = QGroupBox()

        self.h_splitter = QSplitter()
        self.v_splitter = QSplitter()

        # Widgets initialized in factories
        self.about_logo = QLabel()
        self.about_text = QLabel()
        self.theme_switch_button = QPushButton()
        self.start_url_widget = QLineEdit()
        self.user_agent_widget = QComboBox()
        self.max_pages_ctrl = QLineEdit()
        self.crawl_depth_ctrl = QSpinBox()
        self.min_pause_ctrl = QLineEdit()
        self.max_pause_ctrl = QLineEdit()
        self.include_paths_widget = QTextEdit()
        self.exclude_paths_widget = QTextEdit()
        self.stay_on_subdomain_check = QCheckBox()
        self.ignore_queries_check = QCheckBox()
        self.download_button = QPushButton()
        self.local_dir_ctrl = QLineEdit()
        self.browse_button = QPushButton()
        self.local_exclude_ctrl = QTextEdit()
        self.use_gitignore_check = QCheckBox()
        self.hide_binaries_check = QCheckBox()
        self.dir_level_ctrl = QSpinBox()
        self.standard_log_list = QTableWidget()
        self.local_file_list = QTableWidget()
        self.list_stack_layout = QVBoxLayout()
        self.progress_gauge = QProgressBar()
        self.file_count_label = QLabel()
        self.delete_button = QPushButton()
        self.verbose_log_widget = QTextEdit()
        self.output_filename_ctrl = QLineEdit()
        self.output_timestamp_label = QLabel()
        self.output_format_choice = QComboBox()
        self.package_button = QPushButton()
        self.copy_button = QPushButton()

        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.create_context_menus()
        self.toggle_output_view(is_web_mode=True)

        # Memory management: limit verbose log size to prevent unbounded growth
        self.max_log_lines = MAX_LOG_LINES  # Keep maximum lines in verbose log
        self.log_line_count = 0

    def _assign_widgets_from_dict(self, widgets_dict):
        """Assigns keys/values from a dictionary to self as attributes."""
        for key, value in widgets_dict.items():
            setattr(self, key, value)

    def create_widgets(self):
        # --- 1. Input/System Panels ---
        system_widgets = self.input_factory.create_system_panel()
        crawler_widgets = self.input_factory.create_crawler_panel()
        local_widgets = self.input_factory.create_local_panel()

        self._assign_widgets_from_dict(system_widgets)
        self._assign_widgets_from_dict(crawler_widgets)
        self._assign_widgets_from_dict(local_widgets)

        self.input_group = QGroupBox("Input")
        self.web_crawl_radio = QRadioButton("Web Crawl")
        self.local_dir_radio = QRadioButton("Local Directory")
        self.web_crawl_radio.setChecked(True)
        self.crawler_panel = crawler_widgets["crawler_panel"]
        self.local_panel = local_widgets["local_panel"]

        # --- 2. Output/Log Panels ---
        list_log_widgets = self.output_factory.create_list_log_widgets()
        output_widgets = self.output_factory.create_output_group()

        self._assign_widgets_from_dict(list_log_widgets)
        self._assign_widgets_from_dict(output_widgets)

        self.list_group = list_log_widgets["list_group"]
        self.log_group = list_log_widgets["log_group"]
        self.output_group = output_widgets["output_group"]

    # In the create_layout method of MainWindow class, replace the splitter initialization:

    def create_layout(self):
        main_layout = QHBoxLayout(self)
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.h_splitter)

        # Load saved horizontal splitter state or set default 50/50 split
        h_sash_state_b64 = config.get("h_sash_state")

        # LEFT PANEL (Input + System)
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

        # RIGHT PANEL (List + Log + Output)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # New Vertical Splitter for List/Log (50/50 initial split)
        self.v_splitter = QSplitter(Qt.Orientation.Vertical)

        # Load saved vertical splitter state or set default 50/50 split
        v_sash_state_b64 = config.get("v_sash_state")

        list_wrapper = QWidget()
        list_wrapper_layout = QVBoxLayout(list_wrapper)
        list_wrapper_layout.setContentsMargins(0, 0, 0, 5)
        list_wrapper_layout.addWidget(self.list_group)
        self.v_splitter.addWidget(list_wrapper)
        self.v_splitter.addWidget(self.log_group)

        right_layout.addWidget(self.v_splitter)
        right_layout.addWidget(self.output_group)
        self.h_splitter.addWidget(right_widget)

        # Apply splitter states AFTER all widgets are added
        if h_sash_state_b64:
            self.h_splitter.restoreState(QByteArray.fromBase64(h_sash_state_b64.encode("utf-8")))
        else:
            # Set equal widths for left and right panels (50/50)
            # Use actual window width for proper sizing
            total_width = self.width()
            self.h_splitter.setSizes([total_width // 2, total_width // 2])

        if v_sash_state_b64:
            self.v_splitter.restoreState(QByteArray.fromBase64(v_sash_state_b64.encode("utf-8")))
        else:
            # Set equal heights for list and log panels (50/50)
            total_height = self.height()
            self.v_splitter.setSizes([total_height // 2, total_height // 2])

    def create_connections(self):
        self.web_crawl_radio.toggled.connect(self.app.ui_controller.on_toggle_input_mode)
        self.browse_button.clicked.connect(self.app.ui_controller.on_browse)
        self.download_button.clicked.connect(self.app.ui_controller.on_download_button_click)
        self.package_button.clicked.connect(self.app.ui_controller.on_package_button_click)
        self.copy_button.clicked.connect(self.app.ui_controller.on_copy_to_clipboard)
        self.delete_button.clicked.connect(self.on_delete_selected_item)
        self.about_logo.mousePressEvent = lambda event: self.app.ui_controller.on_show_about_dialog()
        self.about_text.mousePressEvent = lambda event: self.app.ui_controller.on_show_about_dialog()
        self.theme_switch_button.clicked.connect(self.app.ui_controller.on_toggle_theme)
        self.use_gitignore_check.stateChanged.connect(self.app.ui_controller.on_local_filters_changed)
        self.hide_binaries_check.stateChanged.connect(self.app.ui_controller.on_local_filters_changed)
        self.dir_level_ctrl.valueChanged.connect(self.app.ui_controller.on_exclude_text_update)
        self.local_exclude_ctrl.textChanged.connect(self.app.ui_controller.on_exclude_text_update)
        self.standard_log_list.itemSelectionChanged.connect(self.update_delete_button_state)
        self.local_file_list.itemSelectionChanged.connect(self.update_delete_button_state)

    def create_context_menus(self):
        """Creates custom context menus for widgets."""
        self.verbose_log_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.verbose_log_widget.customContextMenuRequested.connect(self.show_log_context_menu)

    def show_log_context_menu(self, position):
        """Shows the context menu for the verbose log."""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction

        context_menu = QMenu(self)
        clear_action = QAction("Clear Log", self)
        clear_action.triggered.connect(self.clear_logs)
        context_menu.addAction(clear_action)
        context_menu.exec(self.verbose_log_widget.mapToGlobal(position))

    def get_crawler_config(self, output_dir):
        """Validate and create crawler configuration. Raises ValueError on invalid input."""
        start_url = self.start_url_widget.text().strip()
        if not start_url:
            raise ValueError("Start URL is required")

        max_pages_text = self.max_pages_ctrl.text().strip()
        if not max_pages_text:
            raise ValueError("Max pages is required")
        max_pages = int(max_pages_text)
        if max_pages <= 0:
            raise ValueError("Max pages must be greater than 0")

        min_pause_text = self.min_pause_ctrl.text().strip()
        if not min_pause_text:
            raise ValueError("Min pause is required")
        min_pause = int(min_pause_text)
        if min_pause < 0:
            raise ValueError("Min pause cannot be negative")

        max_pause_text = self.max_pause_ctrl.text().strip()
        if not max_pause_text:
            raise ValueError("Max pause is required")
        max_pause = int(max_pause_text)
        if max_pause < 0:
            raise ValueError("Max pause cannot be negative")

        if min_pause > max_pause:
            raise ValueError("Min pause cannot be greater than max pause")

        return CrawlerConfig(
            start_url=start_url,
            output_dir=output_dir,
            max_pages=max_pages,
            min_pause=min_pause / 1000.0,
            max_pause=max_pause / 1000.0,
            crawl_depth=self.crawl_depth_ctrl.value(),
            include_paths=[p.strip() for p in self.include_paths_widget.toPlainText().splitlines() if p.strip()],
            exclude_paths=[p.strip() for p in self.exclude_paths_widget.toPlainText().splitlines() if p.strip()],
            stay_on_subdomain=self.stay_on_subdomain_check.isChecked(),
            ignore_queries=self.ignore_queries_check.isChecked(),
            user_agent=self.user_agent_widget.currentText(),
        )

    def on_toggle_log_mode(self, checked):
        pass

    def toggle_output_view(self, is_web_mode):
        self.local_file_list.setVisible(not is_web_mode)
        self.standard_log_list.setVisible(is_web_mode)

        self.progress_gauge.setValue(0)
        self.progress_gauge.setVisible(is_web_mode)

        self.update_delete_button_state()
        self.update_file_count()

    def add_scraped_files_batch(self, files_data):
        """Optimized batch file addition to prevent UI blocking."""
        if not files_data:
            return

        # Disable sorting temporarily for better performance
        self.standard_log_list.setSortingEnabled(False)

        # Block signals during bulk operations to prevent excessive updates
        self.standard_log_list.blockSignals(True)

        try:
            # Pre-allocate rows for better performance
            start_row = self.standard_log_list.rowCount()
            self.standard_log_list.setRowCount(start_row + len(files_data))

            # Bulk add files
            for i, file_data in enumerate(files_data):
                row = start_row + i
                self.scraped_files.append(file_data)
                self.standard_log_list.setItem(row, 0, QTableWidgetItem(file_data["url"]))
                self.standard_log_list.setItem(row, 1, QTableWidgetItem(file_data["filename"]))
        finally:
            # Re-enable signals and sorting
            self.standard_log_list.blockSignals(False)
            self.standard_log_list.setSortingEnabled(True)

        self.update_file_count()

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
        self.update_file_count()

    def on_delete_selected_item(self):
        is_web_mode = self.web_crawl_radio.isChecked()
        list_widget = self.standard_log_list if is_web_mode else self.local_file_list
        selected_rows = sorted([index.row() for index in list_widget.selectionModel().selectedRows()], reverse=True)
        if not selected_rows:
            return

        for row in selected_rows:
            if is_web_mode:
                item_data = self.scraped_files.pop(row)
                self.app.delete_scraped_file(item_data["path"])
            else:
                item = list_widget.item(row, 0)
                if not item:
                    continue
                name = item.text()
                item_data = next((f for f in self.local_files if f["name"] == name), None)
                if item_data:
                    self.app.remove_local_file_from_package(item_data["rel_path"])
                    self.local_files.remove(item_data)
            list_widget.removeRow(row)

        self.update_delete_button_state()
        self.update_file_count()
        self.app._update_button_states()

    def update_delete_button_state(self):
        list_widget = None
        if self.standard_log_list.isVisible():
            list_widget = self.standard_log_list
        elif self.local_file_list.isVisible():
            list_widget = self.local_file_list
        is_enabled = list_widget.selectionModel().hasSelection() if list_widget else False
        self.delete_button.setEnabled(is_enabled)

    def clear_logs(self):
        self.verbose_log_widget.clear()
        self.log_line_count = 0  # Reset line counter
        self.standard_log_list.setRowCount(0)
        self.scraped_files.clear()
        self.discovered_url_count = 0
        self.update_delete_button_state()
        self.update_file_count()

    def _manage_log_size(self):
        """Manage verbose log size to prevent memory bloat."""
        if self.log_line_count > self.max_log_lines:
            # Remove oldest lines to stay within limit
            cursor = self.verbose_log_widget.textCursor()

            # Calculate how many lines to remove (remove 25% when limit exceeded)
            lines_to_remove = self.log_line_count // 4

            # Move to beginning and remove lines
            cursor.movePosition(cursor.MoveOperation.Start)
            for _ in range(lines_to_remove):
                cursor.select(cursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # Remove newline

            self.log_line_count -= lines_to_remove

    def update_discovered_count(self, count):
        self.discovered_url_count = count
        self.update_file_count()

    def update_file_count(self):
        label = ""
        if self.standard_log_list.isVisible():
            saved_count = len(self.scraped_files)
            total_known = saved_count + self.discovered_url_count
            if total_known > 0:
                label = f"{saved_count} saved / {total_known} discovered"
        elif self.local_file_list.isVisible():
            count = len(self.local_files)
            if count > 0:
                label = f"{count} item(s)"
        self.file_count_label.setText(label)

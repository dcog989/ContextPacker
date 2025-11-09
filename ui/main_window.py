from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QLabel, QLineEdit, QRadioButton, QComboBox, QSpinBox, QTextEdit, QCheckBox, QPushButton, QTableWidget, QFormLayout, QProgressBar, QTableWidgetItem, QHeaderView, QDialog, QSizePolicy
from PySide6.QtGui import QPixmap, QIcon, QFont, QCursor
from PySide6.QtCore import Qt, QByteArray

from core.packager import resource_path
from core.config import CrawlerConfig
from core.config_manager import get_config

config = get_config()


class AboutDialog(QDialog):
    def __init__(self, parent, version):
        super().__init__(parent)
        self.setWindowTitle("About ContextPacker")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = resource_path("assets/icons/ContextPacker-x128.png")
        pixmap = QPixmap(str(logo_path))
        logo_label = QLabel()
        logo_label.setPixmap(pixmap)
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("ContextPacker")
        title_font = QFont("Source Code Pro", 22, QFont.Weight.Bold)
        title_label.setFont(title_font)
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)

        desc = QLabel("Scrape websites or select local files, then package into a single file, optimized for LLMs.")
        desc.setWordWrap(True)
        layout.addWidget(desc, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(15)

        milkshake = QLabel('"I drink your milkshake! I drink it up!"')
        milkshake_font = QFont("Source Code Pro", 12, QFont.Weight.Normal, italic=True)
        milkshake.setFont(milkshake_font)
        layout.addWidget(milkshake, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)

        version_label = QLabel(f"Version {version}")
        layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignCenter)

        url = "https://github.com/dcog989/ContextPacker"
        link_label = QLabel(f'<a href="{url}" style="color: #66B2FF;">{url}</a>')
        link_label.setOpenExternalLinks(True)
        layout.addWidget(link_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(20)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)


class MainWindow(QWidget):
    def __init__(self, parent_app):
        super().__init__()
        self.app = parent_app
        self.scraped_files = []
        self.local_files = []
        self.discovered_url_count = 0

        self.create_widgets()
        self.create_layout()
        self.create_connections()
        self.toggle_output_view(is_web_mode=True)

    def create_widgets(self):
        self.input_group = QGroupBox("Input")
        self.web_crawl_radio = QRadioButton("Web Crawl")
        self.local_dir_radio = QRadioButton("Local Directory")
        self.web_crawl_radio.setChecked(True)

        self.crawler_panel = self._create_crawler_panel()
        self.local_panel = self._create_local_panel()

        self.list_group = QGroupBox("List")
        self.log_mode_web_panel = QWidget()
        self.standard_log_radio = QRadioButton("Files")
        self.verbose_log_radio = QRadioButton("Log")
        self.standard_log_radio.setChecked(True)

        self.standard_log_list = QTableWidget(0, 2)
        self.standard_log_list.setHorizontalHeaderLabels(["URL", "Saved Filename"])
        self.standard_log_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.standard_log_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.standard_log_list.verticalHeader().setVisible(False)

        self.verbose_log_ctrl = QTextEdit()
        self.verbose_log_ctrl.setReadOnly(True)
        self.verbose_log_ctrl.setFont(QFont("Consolas", 11))

        self.local_file_list = QTableWidget(0, 3)
        self.local_file_list.setHorizontalHeaderLabels(["Name", "Type", "Size"])
        self.local_file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.local_file_list.horizontalHeader().setSortIndicatorShown(True)
        self.local_file_list.setSortingEnabled(True)
        self.local_file_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.local_file_list.verticalHeader().setVisible(False)

        self.progress_gauge = QProgressBar()
        self.file_count_label = QLabel("")
        self.delete_button = QPushButton("Delete Selected")

        self.output_group = QGroupBox("Output")
        self.output_filename_ctrl = QLineEdit("ContextPacker-package")
        self.output_timestamp_label = QLabel("")
        self.output_format_choice = QComboBox()
        self.output_format_choice.addItems([".md", ".txt", ".xml"])
        default_format = config.get("default_output_format", ".md")
        self.output_format_choice.setCurrentText(default_format)

        self.package_button = QPushButton("Package")
        copy_icon_path = resource_path("assets/icons/copy.png")
        self.copy_button = QPushButton()
        self.copy_button.setIcon(QIcon(str(copy_icon_path)))
        self.copy_button.setFixedSize(self.package_button.sizeHint().height(), self.package_button.sizeHint().height())
        self.copy_button.setToolTip("Copy final package contents to clipboard")
        self.copy_button.setEnabled(False)

    def _create_crawler_panel(self):
        panel = QWidget()
        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(10, 15, 10, 10)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.start_url_ctrl = QLineEdit()
        user_agents = config.get("user_agents", [])
        self.user_agent_combo = QComboBox()
        self.user_agent_combo.addItems(user_agents)
        self.user_agent_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.user_agent_combo.setMinimumContentsLength(20)
        self.max_pages_ctrl = QLineEdit("5")
        self.max_pages_ctrl.setFixedWidth(60)
        self.crawl_depth_ctrl = QSpinBox()
        self.crawl_depth_ctrl.setValue(1)
        self.crawl_depth_ctrl.setRange(0, 99)
        self.min_pause_ctrl = QLineEdit("212")
        self.min_pause_ctrl.setFixedWidth(60)
        self.max_pause_ctrl = QLineEdit("2200")
        self.max_pause_ctrl.setFixedWidth(60)

        numerical_layout = QHBoxLayout()
        numerical_layout.addWidget(self.max_pages_ctrl)
        numerical_layout.addSpacing(15)
        numerical_layout.addWidget(QLabel("Crawl Depth:"))
        numerical_layout.addWidget(self.crawl_depth_ctrl)
        numerical_layout.addStretch()

        pause_layout = QHBoxLayout()
        pause_layout.addWidget(self.min_pause_ctrl)
        pause_layout.addWidget(QLabel(" to "))
        pause_layout.addWidget(self.max_pause_ctrl)
        pause_layout.addStretch()

        self.include_paths_ctrl = QTextEdit()
        self.exclude_paths_ctrl = QTextEdit()
        self.include_paths_ctrl.setFixedHeight(80)
        self.exclude_paths_ctrl.setFixedHeight(80)

        self.stay_on_subdomain_check = QCheckBox("Stay on start URL's subdomain")
        self.stay_on_subdomain_check.setChecked(True)
        self.ignore_queries_check = QCheckBox("Ignore URL query parameters (?...)")
        self.ignore_queries_check.setChecked(True)
        self.download_button = QPushButton("Download & Convert")

        form_layout.addRow("Start URL:", self.start_url_ctrl)
        form_layout.addRow("User-Agent:", self.user_agent_combo)
        form_layout.addRow("Max Pages:", numerical_layout)
        form_layout.addRow("Pause (ms):", pause_layout)
        form_layout.addRow("Include Paths:", self.include_paths_ctrl)
        form_layout.addRow("Exclude Paths:", self.exclude_paths_ctrl)

        options_layout = QVBoxLayout()
        options_layout.addWidget(self.stay_on_subdomain_check)
        options_layout.addWidget(self.ignore_queries_check)
        form_layout.addRow("", options_layout)
        form_layout.addRow("", self.download_button)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        logo_path = resource_path("assets/icons/ContextPacker-x64.png")
        self.about_logo = QLabel()
        self.about_logo.setPixmap(QPixmap(str(logo_path)))
        self.about_logo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.about_text = QLabel("ContextPacker")
        self.about_text.setFont(QFont("Source Code Pro", 20, QFont.Weight.Bold))
        self.about_text.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.version_text = QLabel(f"v{self.app.version}")

        about_layout = QHBoxLayout()
        about_layout.addStretch()
        about_layout.addWidget(self.about_logo)
        about_text_layout = QVBoxLayout()
        about_text_layout.addWidget(self.about_text)
        about_text_layout.addWidget(self.version_text)
        about_layout.addLayout(about_text_layout)
        about_layout.addStretch()
        main_layout.addLayout(about_layout)

        return panel

    def _create_local_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 15, 10, 10)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        dir_layout = QHBoxLayout()
        self.local_dir_ctrl = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        dir_layout.addWidget(self.local_dir_ctrl)
        dir_layout.addWidget(self.browse_button)
        form_layout.addRow("Input Directory:", dir_layout)

        self.local_exclude_ctrl = QTextEdit("\n".join(config.get("default_local_excludes", [])))
        self.local_exclude_ctrl.setFixedHeight(120)
        form_layout.addRow("Excludes:", self.local_exclude_ctrl)

        self.use_gitignore_check = QCheckBox("Use .gitignore")
        self.use_gitignore_check.setChecked(True)
        self.hide_binaries_check = QCheckBox("Hide Images + Binaries")
        self.hide_binaries_check.setChecked(True)
        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(self.use_gitignore_check)
        checkbox_layout.addWidget(self.hide_binaries_check)
        form_layout.addRow("", checkbox_layout)

        self.dir_level_ctrl = QSpinBox()
        self.dir_level_ctrl.setValue(9)
        self.dir_level_ctrl.setRange(0, 9)
        form_layout.addRow("Directory Depth:", self.dir_level_ctrl)

        layout.addLayout(form_layout)
        layout.addStretch()
        return panel

    def create_layout(self):
        main_layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)

        sash_state_b64 = config.get("sash_state")
        if sash_state_b64:
            self.splitter.restoreState(QByteArray.fromBase64(sash_state_b64.encode("utf-8")))
        else:
            self.splitter.setSizes([650, 800])

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(self.input_group)
        self.splitter.addWidget(left_widget)

        input_layout = QVBoxLayout(self.input_group)
        radio_layout = QHBoxLayout()
        radio_layout.setContentsMargins(10, 10, 0, 0)
        radio_layout.addWidget(self.web_crawl_radio)
        radio_layout.addWidget(self.local_dir_radio)
        radio_layout.addStretch()
        input_layout.addLayout(radio_layout)
        input_layout.addWidget(self.crawler_panel)
        input_layout.addWidget(self.local_panel)
        self.local_panel.hide()

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(self.list_group)
        right_layout.addWidget(self.output_group)
        self.splitter.addWidget(right_widget)

        list_layout = QVBoxLayout(self.list_group)
        log_mode_layout = QHBoxLayout(self.log_mode_web_panel)
        log_mode_layout.addWidget(self.standard_log_radio)
        log_mode_layout.addWidget(self.verbose_log_radio)
        log_mode_layout.addStretch()
        list_layout.addWidget(self.log_mode_web_panel)
        list_stack = QWidget()
        self.list_stack_layout = QVBoxLayout(list_stack)
        self.list_stack_layout.setContentsMargins(0, 0, 0, 0)
        self.list_stack_layout.addWidget(self.standard_log_list)
        self.list_stack_layout.addWidget(self.verbose_log_ctrl)
        self.list_stack_layout.addWidget(self.local_file_list)
        list_layout.addWidget(list_stack)

        list_layout.addWidget(self.progress_gauge)
        bottom_bar_layout = QHBoxLayout()
        bottom_bar_layout.addWidget(self.file_count_label)
        bottom_bar_layout.addStretch()
        bottom_bar_layout.addWidget(self.delete_button)
        list_layout.addLayout(bottom_bar_layout)

        output_layout = QVBoxLayout(self.output_group)
        filename_layout = QHBoxLayout()
        filename_layout.addWidget(self.output_filename_ctrl)
        filename_layout.addWidget(self.output_timestamp_label)
        filename_layout.addWidget(self.output_format_choice)
        filename_layout.addWidget(self.package_button)
        filename_layout.addWidget(self.copy_button)
        output_layout.addLayout(filename_layout)

    def create_connections(self):
        self.web_crawl_radio.toggled.connect(self.app.on_toggle_input_mode)
        self.browse_button.clicked.connect(self.app.on_browse)
        self.download_button.clicked.connect(self.app.on_download_button_click)
        self.package_button.clicked.connect(self.app.on_package_button_click)
        self.copy_button.clicked.connect(self.app.on_copy_to_clipboard)
        self.delete_button.clicked.connect(self.on_delete_selected_item)
        self.about_logo.mousePressEvent = self.app.on_show_about_dialog
        self.about_text.mousePressEvent = self.app.on_show_about_dialog
        self.use_gitignore_check.stateChanged.connect(self.app.on_local_filters_changed)
        self.hide_binaries_check.stateChanged.connect(self.app.on_local_filters_changed)
        self.dir_level_ctrl.valueChanged.connect(self.app.on_exclude_text_update)
        self.local_exclude_ctrl.textChanged.connect(self.app.on_exclude_text_update)
        self.standard_log_radio.toggled.connect(self.on_toggle_log_mode)
        self.standard_log_list.itemSelectionChanged.connect(self.update_delete_button_state)
        self.local_file_list.itemSelectionChanged.connect(self.update_delete_button_state)

    def get_crawler_config(self, output_dir):
        return CrawlerConfig(
            start_url=self.start_url_ctrl.text(),
            output_dir=output_dir,
            max_pages=int(self.max_pages_ctrl.text()),
            min_pause=int(self.min_pause_ctrl.text()) / 1000.0,
            max_pause=int(self.max_pause_ctrl.text()) / 1000.0,
            crawl_depth=self.crawl_depth_ctrl.value(),
            include_paths=[p.strip() for p in self.include_paths_ctrl.toPlainText().splitlines() if p.strip()],
            exclude_paths=[p.strip() for p in self.exclude_paths_ctrl.toPlainText().splitlines() if p.strip()],
            stay_on_subdomain=self.stay_on_subdomain_check.isChecked(),
            ignore_queries=self.ignore_queries_check.isChecked(),
            user_agent=self.user_agent_combo.currentText(),
        )

    def on_toggle_log_mode(self, checked):
        if self.log_mode_web_panel.isVisible():
            is_files_mode = self.standard_log_radio.isChecked()
            self.standard_log_list.setVisible(is_files_mode)
            self.verbose_log_ctrl.setVisible(not is_files_mode)
            self.delete_button.setVisible(is_files_mode)
            if not is_files_mode:
                self.verbose_log_ctrl.verticalScrollBar().setValue(self.verbose_log_ctrl.verticalScrollBar().maximum())
            self.update_delete_button_state()

    def toggle_output_view(self, is_web_mode):
        self.log_mode_web_panel.setVisible(is_web_mode)
        self.local_file_list.setVisible(not is_web_mode)
        self.progress_gauge.setValue(0)
        self.progress_gauge.setVisible(is_web_mode)
        if is_web_mode:
            self.on_toggle_log_mode(True)
        else:
            self.standard_log_list.hide()
            self.verbose_log_ctrl.hide()
            self.delete_button.show()
        self.update_delete_button_state()
        self.update_file_count()

    def add_scraped_files_batch(self, files_data):
        self.standard_log_list.setSortingEnabled(False)
        for file_data in files_data:
            self.scraped_files.append(file_data)
            row = self.standard_log_list.rowCount()
            self.standard_log_list.insertRow(row)
            self.standard_log_list.setItem(row, 0, QTableWidgetItem(file_data["url"]))
            self.standard_log_list.setItem(row, 1, QTableWidgetItem(file_data["filename"]))
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
        self.verbose_log_ctrl.clear()
        self.standard_log_list.setRowCount(0)
        self.scraped_files.clear()
        self.discovered_url_count = 0
        self.update_delete_button_state()
        self.update_file_count()

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

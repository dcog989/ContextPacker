from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QComboBox, QTextEdit, QPushButton, QTableWidget, QProgressBar, QHeaderView
from PySide6.QtGui import QIcon, QFont
from PySide6.QtCore import Qt
from core.utils import resource_path
from core.config_manager import get_config

config = get_config()


class OutputPanelFactory:
    """
    Factory class to create and configure the various output/list panels,
    returning a dictionary of initialized widgets.
    """

    def __init__(self, parent_window):
        self.parent = parent_window

    def create_list_log_widgets(self):
        """
        Creates the List and Log QGroupBoxes and initializes their internal widgets.
        Returns a dictionary containing the two groups and all control widgets.
        """
        widgets = {}

        # --- List Group (Top Half of Right Panel) ---
        list_group = QGroupBox("List")
        list_panel_layout = QVBoxLayout(list_group)
        list_panel_layout.setContentsMargins(10, 20, 10, 10)
        widgets["list_group"] = list_group

        standard_log_list = QTableWidget(0, 2)
        standard_log_list.setHorizontalHeaderLabels(["URL", "Saved Filename"])
        standard_log_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        standard_log_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        standard_log_list.verticalHeader().setVisible(False)

        local_file_list = QTableWidget(0, 3)
        local_file_list.setHorizontalHeaderLabels(["Name", "Type", "Size"])
        local_file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        local_file_list.horizontalHeader().setSortIndicatorShown(True)
        local_file_list.setSortingEnabled(True)
        local_file_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        local_file_list.verticalHeader().setVisible(False)

        # Stack for web/local lists
        list_stack = QWidget()
        list_stack_layout = QVBoxLayout(list_stack)
        list_stack_layout.setContentsMargins(0, 0, 0, 0)
        list_stack_layout.addWidget(standard_log_list)
        list_stack_layout.addWidget(local_file_list)
        list_panel_layout.addWidget(list_stack)
        widgets["list_stack_layout"] = list_stack_layout  # Needed for toggle_output_view

        # Bottom Bar: Count, Progress, and Delete Button
        progress_gauge = QProgressBar()
        file_count_label = QLabel("")
        delete_button = QPushButton("Delete Selected")
        delete_button.setObjectName("PrimaryButton")

        bottom_bar_layout = QHBoxLayout()
        bottom_bar_layout.addWidget(file_count_label)
        bottom_bar_layout.addStretch()
        bottom_bar_layout.addWidget(progress_gauge)
        bottom_bar_layout.addWidget(delete_button)
        list_panel_layout.addLayout(bottom_bar_layout)

        widgets.update(
            {
                "standard_log_list": standard_log_list,
                "local_file_list": local_file_list,
                "progress_gauge": progress_gauge,
                "file_count_label": file_count_label,
                "delete_button": delete_button,
            }
        )

        # --- Log Group (Bottom Half of Right Panel) ---
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 20, 10, 10)
        widgets["log_group"] = log_group

        verbose_log_widget = QTextEdit()
        verbose_log_widget.setReadOnly(True)
        verbose_log_widget.setFont(QFont("Consolas", 11))
        log_layout.addWidget(verbose_log_widget)
        widgets["verbose_log_widget"] = verbose_log_widget

        return widgets

    def create_output_group(self):
        """Creates and configures the Output QGroupBox, returning the group and its controls."""
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(10, 20, 10, 10)
        widgets = {"output_group": output_group}

        output_filename_ctrl = QLineEdit("ContextPacker-package")
        output_timestamp_label = QLabel("")

        output_format_choice = QComboBox()
        output_format_choice.addItems([".md", ".txt", ".xml"])
        default_format = config.get("default_output_format", ".md")
        output_format_choice.setCurrentText(default_format)

        package_button = QPushButton("Package")
        package_button.setObjectName("PrimaryButton")
        # The icon is set dynamically in app.py to respect theme
        copy_button = QPushButton()
        copy_button.setFixedSize(package_button.sizeHint().height(), package_button.sizeHint().height())
        copy_button.setToolTip("Copy final package contents to clipboard")
        copy_button.setEnabled(False)

        filename_layout = QHBoxLayout()
        filename_layout.addWidget(output_filename_ctrl)
        filename_layout.addWidget(output_timestamp_label)
        filename_layout.addWidget(output_format_choice)
        filename_layout.addWidget(package_button)
        filename_layout.addWidget(copy_button)
        output_layout.addLayout(filename_layout)

        widgets.update(
            {
                "output_filename_ctrl": output_filename_ctrl,
                "output_timestamp_label": output_timestamp_label,
                "output_format_choice": output_format_choice,
                "package_button": package_button,
                "copy_button": copy_button,
            }
        )

        return widgets

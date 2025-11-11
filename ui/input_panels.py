from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QComboBox, QSpinBox, QTextEdit, QCheckBox, QPushButton, QFormLayout, QSizePolicy
from PySide6.QtGui import QPixmap, QFont, QCursor, QIntValidator
from PySide6.QtCore import Qt
from core.utils import resource_path
from core.constants import DEFAULT_MIN_PAUSE_MS, DEFAULT_MAX_PAUSE_MS, UNLIMITED_DEPTH_VALUE
from core.config_manager import get_config

config = get_config()


class InputPanelFactory:
    """
    Factory class to create and configure the various input panels,
    returning a dictionary of initialized widgets.
    """

    def __init__(self, parent_window):
        # We store parent for access to properties like parent_window.app.version
        self.parent = parent_window

    def create_system_panel(self):
        """Creates and configures the System QGroupBox, returning the group and its controls."""
        system_group = QGroupBox("System")
        layout = QHBoxLayout(system_group)
        layout.setContentsMargins(10, 15, 10, 10)

        # Logo and Title
        logo_path = resource_path("assets/icons/ContextPacker-x64.png")
        about_logo = QLabel()
        about_logo.setPixmap(QPixmap(str(logo_path)))
        about_logo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        about_logo.setFixedSize(48, 48)
        about_logo.setScaledContents(True)

        about_text = QLabel("ContextPacker")
        about_text.setFont(QFont("Source Code Pro", 18, QFont.Weight.Bold))
        about_text.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        version_text = QLabel(f"v{self.parent.app.version}")
        version_text.setFont(QFont("Source Code Pro", 10))

        text_layout = QVBoxLayout()
        text_layout.addWidget(about_text)
        text_layout.addWidget(version_text)
        text_layout.setSpacing(0)

        layout.addWidget(about_logo)
        layout.addLayout(text_layout)
        layout.addStretch()

        # Theme Switch
        theme_switch_button = QPushButton()
        theme_switch_button.setObjectName("ThemeSwitchButton")
        theme_switch_button.setFixedSize(32, 32)
        layout.addWidget(theme_switch_button)

        widgets = {
            "system_panel": system_group,
            "about_logo": about_logo,
            "about_text": about_text,
            "theme_switch_button": theme_switch_button,
        }
        return widgets

    def create_crawler_panel(self):
        """Creates and configures the Web Crawl input panel, returning the panel and its controls."""
        panel = QWidget()
        main_layout = QVBoxLayout(panel)
        main_layout.setContentsMargins(10, 15, 10, 10)
        main_layout.setSpacing(0)  # Remove extra spacing from main layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        # Fix row spacing to be consistent
        form_layout.setVerticalSpacing(8)
        form_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins from form
        widgets = {"crawler_panel": panel}

        start_url_widget = QLineEdit()
        user_agents = config.get("user_agents", [])
        user_agent_widget = QComboBox()
        user_agent_widget.addItems(user_agents)
        user_agent_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        user_agent_widget.setMinimumContentsLength(20)

        # Numerical inputs
        max_pages_ctrl = QLineEdit("5")
        max_pages_ctrl.setValidator(QIntValidator(1, 9999))
        max_pages_ctrl.setFixedWidth(60)

        crawl_depth_ctrl = QSpinBox()
        crawl_depth_ctrl.setValue(1)
        crawl_depth_ctrl.setRange(0, 99)
        crawl_depth_ctrl.setFixedWidth(60)

        min_pause_ctrl = QLineEdit(str(DEFAULT_MIN_PAUSE_MS))
        min_pause_ctrl.setValidator(QIntValidator(0, 99999))
        min_pause_ctrl.setFixedWidth(60)

        max_pause_ctrl = QLineEdit(str(DEFAULT_MAX_PAUSE_MS))
        max_pause_ctrl.setValidator(QIntValidator(0, 99999))
        max_pause_ctrl.setFixedWidth(60)

        # Combine numerical inputs into layouts for the form
        max_pages_layout = QHBoxLayout()
        max_pages_layout.addWidget(max_pages_ctrl)
        max_pages_layout.addStretch()
        max_pages_layout.setContentsMargins(0, 0, 0, 0)

        depth_layout = QHBoxLayout()
        depth_layout.addWidget(crawl_depth_ctrl)
        depth_layout.addStretch()
        depth_layout.setContentsMargins(0, 0, 0, 0)

        pause_layout = QHBoxLayout()
        pause_layout.addWidget(min_pause_ctrl)
        pause_layout.addWidget(QLabel(" to "))
        pause_layout.addWidget(max_pause_ctrl)
        pause_layout.addStretch()
        pause_layout.setContentsMargins(0, 0, 0, 0)

        include_paths_widget = QTextEdit()
        exclude_paths_widget = QTextEdit()
        include_paths_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        exclude_paths_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        include_paths_widget.setMinimumHeight(60)
        exclude_paths_widget.setMinimumHeight(60)

        stay_on_subdomain_check = QCheckBox("Stay on start URL's subdomain")
        stay_on_subdomain_check.setChecked(True)
        ignore_queries_check = QCheckBox("Ignore URL query parameters (?...)")
        ignore_queries_check.setChecked(True)

        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(stay_on_subdomain_check)
        checkbox_layout.addWidget(ignore_queries_check)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        download_button = QPushButton("Download && Convert")
        download_button.setObjectName("PrimaryButton")

        form_layout.addRow("Start URL:", start_url_widget)
        form_layout.addRow("User-Agent:", user_agent_widget)
        form_layout.addRow("Max Pages:", max_pages_layout)
        form_layout.addRow("Crawl Depth:", depth_layout)
        form_layout.addRow("Pause (ms):", pause_layout)
        form_layout.addRow("Include Paths:", include_paths_widget)
        form_layout.addRow("Exclude Paths:", exclude_paths_widget)

        form_layout.addRow("", checkbox_layout)

        # Button layout at the bottom
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(download_button)

        main_layout.addLayout(form_layout)
        # Button layout at the bottom
        main_layout.addLayout(button_layout)

        widgets["start_url_widget"] = start_url_widget
        widgets["user_agent_widget"] = user_agent_widget
        widgets["max_pages_ctrl"] = max_pages_ctrl
        widgets["crawl_depth_ctrl"] = crawl_depth_ctrl
        widgets["min_pause_ctrl"] = min_pause_ctrl
        widgets["max_pause_ctrl"] = max_pause_ctrl
        widgets["include_paths_widget"] = include_paths_widget
        widgets["exclude_paths_widget"] = exclude_paths_widget
        widgets["stay_on_subdomain_check"] = stay_on_subdomain_check
        widgets["ignore_queries_check"] = ignore_queries_check
        widgets["download_button"] = download_button

        return widgets

    def create_local_panel(self):
        """Creates and configures the Local Directory input panel, returning the panel and its controls."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(0)  # Remove extra spacing from main layout
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        # Fix row spacing to match crawler panel exactly
        form_layout.setVerticalSpacing(8)
        form_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins from form
        widgets = {"local_panel": panel}

        dir_layout = QHBoxLayout()
        local_dir_ctrl = QLineEdit()
        browse_button = QPushButton("Browse...")
        dir_layout.addWidget(local_dir_ctrl)
        dir_layout.addWidget(browse_button)
        dir_layout.setContentsMargins(0, 0, 0, 0)
        dir_layout.setSpacing(6)
        form_layout.addRow("Input Directory:", dir_layout)

        # Fix: Ensure excludes are displayed on separate lines
        default_excludes = config.get("default_local_excludes", [])
        local_exclude_ctrl = QTextEdit()
        local_exclude_ctrl.setPlainText("\n".join(default_excludes))  # Use setPlainText instead of constructor
        local_exclude_ctrl.setMinimumHeight(80)  # Minimum height, but allow it to grow
        local_exclude_ctrl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        form_layout.addRow("Excludes:", local_exclude_ctrl)

        use_gitignore_check = QCheckBox("Use .gitignore")
        use_gitignore_check.setChecked(True)
        hide_binaries_check = QCheckBox("Hide Images + Binaries")
        hide_binaries_check.setChecked(True)
        checkbox_layout = QHBoxLayout()  # Changed to horizontal layout
        checkbox_layout.addWidget(use_gitignore_check)
        checkbox_layout.addWidget(hide_binaries_check)
        checkbox_layout.addStretch()
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(15)
        form_layout.addRow("", checkbox_layout)

        dir_level_ctrl = QSpinBox()
        dir_level_ctrl.setValue(UNLIMITED_DEPTH_VALUE)
        dir_level_ctrl.setRange(0, UNLIMITED_DEPTH_VALUE)
        dir_level_ctrl.setSpecialValueText("Unlimited")
        dir_level_ctrl.setFixedWidth(100)

        dir_level_layout = QHBoxLayout()
        dir_level_layout.addWidget(dir_level_ctrl)
        dir_level_layout.addStretch()
        dir_level_layout.setContentsMargins(0, 0, 0, 0)
        dir_level_layout.setSpacing(6)
        form_layout.addRow("Directory Depth:", dir_level_layout)

        layout.addLayout(form_layout)
        # Don't add stretch to prevent pushing form layout content apart
        # layout.addStretch()  # REMOVED

        widgets.update(
            {
                "local_dir_ctrl": local_dir_ctrl,
                "browse_button": browse_button,
                "local_exclude_ctrl": local_exclude_ctrl,
                "use_gitignore_check": use_gitignore_check,
                "hide_binaries_check": hide_binaries_check,
                "dir_level_ctrl": dir_level_ctrl,
            }
        )

        return widgets

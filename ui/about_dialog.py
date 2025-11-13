from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QSize
from core.utils import resource_path
from core.icon_utils import render_svg_to_pixmap


class AboutDialog(QDialog):
    def __init__(self, parent, version):
        super().__init__(parent)
        self.setWindowTitle("About ContextPacker")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)

        # Don't set any custom fonts - let the dialog inherit from the application stylesheet

        logo_path = resource_path("assets/icons/ContextPacker.svg")
        svg_bytes = logo_path.read_bytes()
        pixmap = render_svg_to_pixmap(svg_bytes, QSize(128, 128))
        logo_label = QLabel()
        logo_label.setPixmap(pixmap)
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("ContextPacker")
        title_label.setObjectName("AppNameLabel")  # this should use 'Source Code Pro' bold
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)

        desc = QLabel("Scrape websites or import local files, then package into a single, optimized file for LLMs.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(15)

        milkshake = QLabel('"I drink your milkshake! I drink it up!"')  # this should use 'Source Code Pro' italic
        milkshake.setObjectName("MilkshakeLabel")
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
        ok_button.setObjectName("PrimaryButton")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.adjustSize()

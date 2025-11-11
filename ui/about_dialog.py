from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt
from core.utils import resource_path


class AboutDialog(QDialog):
    def __init__(self, parent, version):
        super().__init__(parent)
        self.setWindowTitle("About ContextPacker")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)

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

        desc = QLabel("Scrape websites or import local files, then package into a single, optimized file for LLMs.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addSpacing(15)

        milkshake = QLabel('"I drink your milkshake! I drink it up!"')
        milkshake_font = QFont("Source Code Pro", 11, QFont.Weight.Normal, italic=True)
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
        ok_button.setObjectName("PrimaryButton")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.adjustSize()

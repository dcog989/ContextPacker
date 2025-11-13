import re
from pathlib import Path
from typing import Optional

from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter, QIcon
from PySide6.QtCore import QByteArray, QSize, Qt


def colorize_svg(svg_path: Path, color: str) -> bytes:
    """
    Reads an SVG file, replaces its standardized placeholder fill color,
    and returns the modified content as bytes.
    """
    try:
        content = svg_path.read_text(encoding="utf-8")
        # Replace a standardized placeholder fill color
        modified_content = content.replace('fill="#000000"', f'fill="{color}"')
        return modified_content.encode("utf-8")
    except Exception:
        return b""


def render_svg_to_pixmap(svg_bytes: bytes, size: QSize) -> QPixmap:
    """Renders SVG byte data to a QPixmap of a given size."""
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)  # Transparent background
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def create_themed_svg_icon(svg_path: Path, color: str, size: Optional[QSize] = None) -> QIcon:
    """Creates a QIcon from an SVG file, dynamically recoloring it."""
    modified_svg_bytes = colorize_svg(svg_path, color)
    if not modified_svg_bytes:
        return QIcon()

    renderer = QSvgRenderer(QByteArray(modified_svg_bytes))

    if size is None:
        # If no size is provided, use the default size from the SVG
        size = renderer.defaultSize()

    pixmap = render_svg_to_pixmap(modified_svg_bytes, size)
    return QIcon(pixmap)

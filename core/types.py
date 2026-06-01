"""
Type definitions for ContextPacker to improve type safety.

This module provides dataclasses and enums to replace dictionary-based
message passing and function parameters throughout the application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class StatusType(Enum):
    """Enumeration of status types."""

    ERROR = "error"
    CANCELLED = "cancelled"
    SOURCE_COMPLETE = "source_complete"
    PACKAGE_COMPLETE = "package_complete"
    CLONE_COMPLETE = "clone_complete"


class AppState(Enum):
    """Enumeration of application states."""

    IDLE = "idle"
    TASK_RUNNING = "task_running"
    TASK_STOPPING = "task_stopping"


class FileType(Enum):
    """Enumeration of file types."""

    FILE = "File"
    FOLDER = "Folder"


@dataclass
class LogMessage:
    """Structured log message."""

    message: str = ""


@dataclass
class StatusMessage:
    """Structured status message."""

    status: StatusType = StatusType.ERROR
    message: str = ""


@dataclass
class ProgressMessage:
    """Structured progress message."""

    value: int = 0
    max_value: int = 100


@dataclass
class FileSavedMessage:
    """Structured file saved message."""

    url: str = ""
    filename: str = ""
    path: str = ""
    pages_saved: int = 0
    max_pages: int = 0
    queue_size: int = 0


@dataclass
class GitCloneDoneMessage:
    """Structured git clone completion message."""

    path: str = ""


@dataclass
class LocalScanCompleteMessage:
    """Structured local scan completion message."""

    results: Optional[tuple[list[dict[str, Any]], set]] = None


@dataclass
class FileInfo:
    """Structured file information."""

    name: str
    type: FileType
    size: int = 0
    size_str: str = ""
    rel_path: str = ""


# Type alias for union of all message types
Message = LogMessage | StatusMessage | ProgressMessage | FileSavedMessage | GitCloneDoneMessage | LocalScanCompleteMessage


def file_info_to_dict(file_info: FileInfo) -> dict[str, Any]:
    """Convert FileInfo to dictionary for backward compatibility."""
    return {"name": file_info.name, "type": file_info.type.value, "size": file_info.size, "size_str": file_info.size_str, "rel_path": file_info.rel_path}


def dict_to_file_info(data: dict[str, Any]) -> FileInfo:
    """Convert dictionary to FileInfo."""
    type_str = data.get("type", "File")
    try:
        file_type = FileType(type_str)
    except ValueError:
        file_type = FileType.FILE

    return FileInfo(name=data.get("name", ""), type=file_type, size=data.get("size", 0), size_str=data.get("size_str", ""), rel_path=data.get("rel_path", ""))

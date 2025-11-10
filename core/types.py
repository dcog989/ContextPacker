"""
Type definitions for ContextPacker to improve type safety.

This module provides dataclasses and enums to replace dictionary-based
message passing and function parameters throughout the application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple


class MessageType(Enum):
    """Enumeration of all possible message types in the system."""

    LOG = "log"
    STATUS = "status"
    PROGRESS = "progress"
    FILE_SAVED = "file_saved"
    UI_TASK_START = "ui_task_start"
    UI_TASK_STOP = "ui_task_stop"
    UI_TASK_STOPPING = "ui_task_stopping"
    GIT_CLONE_DONE = "git_clone_done"
    LOCAL_SCAN_COMPLETE = "local_scan_complete"


class TaskType(Enum):
    """Enumeration of task types."""

    DOWNLOAD = "download"
    PACKAGE = "package"


class StatusType(Enum):
    """Enumeration of status types."""

    ERROR = "error"
    CANCELLED = "cancelled"
    SOURCE_COMPLETE = "source_complete"
    PACKAGE_COMPLETE = "package_complete"
    CLONE_COMPLETE = "clone_complete"


class FileType(Enum):
    """Enumeration of file types."""

    FILE = "File"
    FOLDER = "Folder"


@dataclass
class LogMessage:
    """Structured log message."""

    type: MessageType = MessageType.LOG
    message: str = ""


@dataclass
class StatusMessage:
    """Structured status message."""

    type: MessageType = MessageType.STATUS
    status: StatusType = StatusType.ERROR
    message: str = ""
    path: Optional[str] = None


@dataclass
class ProgressMessage:
    """Structured progress message."""

    type: MessageType = MessageType.PROGRESS
    value: int = 0
    max_value: int = 100


@dataclass
class FileSavedMessage:
    """Structured file saved message."""

    type: MessageType = MessageType.FILE_SAVED
    url: str = ""
    filename: str = ""
    path: str = ""
    pages_saved: int = 0
    max_pages: int = 0
    queue_size: int = 0


@dataclass
class UITaskMessage:
    """Structured UI task message."""

    type: MessageType = MessageType.UI_TASK_START
    task: TaskType = TaskType.DOWNLOAD


@dataclass
class UITaskStopMessage:
    """Structured UI task stop message."""

    type: MessageType = MessageType.UI_TASK_STOP
    was_cancelled: bool = False


@dataclass
class UITaskStoppingMessage:
    """Structured UI task stopping message."""

    type: MessageType = MessageType.UI_TASK_STOPPING


@dataclass
class GitCloneDoneMessage:
    """Structured git clone completion message."""

    type: MessageType = MessageType.GIT_CLONE_DONE
    path: str = ""


@dataclass
class LocalScanCompleteMessage:
    """Structured local scan completion message."""

    type: MessageType = MessageType.LOCAL_SCAN_COMPLETE
    results: Optional[Tuple[List[Dict[str, Any]], set]] = None


@dataclass
class FileInfo:
    """Structured file information."""

    name: str
    type: FileType
    size: int = 0
    size_str: str = ""
    rel_path: str = ""
    url: Optional[str] = None  # For web-crawled files
    path: Optional[str] = None  # For web-crawled files


@dataclass
class CrawlerConfigData:
    """Structured crawler configuration data."""

    start_url: str
    output_dir: str
    max_pages: int
    min_pause: float
    max_pause: float
    crawl_depth: int
    include_paths: List[str]
    exclude_paths: List[str]
    stay_on_subdomain: bool
    ignore_queries: bool
    user_agent: str


# Type alias for union of all message types
Message = LogMessage | StatusMessage | ProgressMessage | FileSavedMessage | UITaskMessage | UITaskStopMessage | UITaskStoppingMessage | GitCloneDoneMessage | LocalScanCompleteMessage


def message_to_dict(message: Message) -> Dict[str, Any]:
    """Convert a typed message to a dictionary for backward compatibility."""
    if isinstance(message, LogMessage):
        return {"type": message.type.value, "message": message.message}
    elif isinstance(message, StatusMessage):
        result = {"type": message.type.value, "status": message.status.value, "message": message.message}
        if message.path:
            result["path"] = message.path
        return result
    elif isinstance(message, ProgressMessage):
        return {"type": message.type.value, "value": message.value, "max_value": message.max_value}
    elif isinstance(message, FileSavedMessage):
        return {"type": message.type.value, "url": message.url, "filename": message.filename, "path": message.path, "pages_saved": message.pages_saved, "max_pages": message.max_pages, "queue_size": message.queue_size}
    elif isinstance(message, UITaskMessage):
        return {"type": message.type.value, "task": message.task.value}
    elif isinstance(message, UITaskStopMessage):
        return {"type": message.type.value, "was_cancelled": message.was_cancelled}
    elif isinstance(message, UITaskStoppingMessage):
        return {"type": message.type.value}
    elif isinstance(message, GitCloneDoneMessage):
        return {"type": message.type.value, "path": message.path}
    elif isinstance(message, LocalScanCompleteMessage):
        return {"type": message.type.value, "results": message.results}
    else:
        raise ValueError(f"Unknown message type: {type(message)}")


def dict_to_message(data: Dict[str, Any]) -> Message:
    """Convert a dictionary to a typed message."""
    msg_type_str = data.get("type", "")
    try:
        msg_type = MessageType(msg_type_str)
    except ValueError:
        # Fallback for unknown message types
        return LogMessage(message=str(data))

    if msg_type == MessageType.LOG:
        return LogMessage(message=data.get("message", ""))
    elif msg_type == MessageType.STATUS:
        status_str = data.get("status", "")
        try:
            status = StatusType(status_str)
        except ValueError:
            status = StatusType.ERROR
        return StatusMessage(status=status, message=data.get("message", ""), path=data.get("path"))
    elif msg_type == MessageType.PROGRESS:
        return ProgressMessage(value=data.get("value", 0), max_value=data.get("max_value", 100))
    elif msg_type == MessageType.FILE_SAVED:
        return FileSavedMessage(url=data.get("url", ""), filename=data.get("filename", ""), path=data.get("path", ""), pages_saved=data.get("pages_saved", 0), max_pages=data.get("max_pages", 0), queue_size=data.get("queue_size", 0))
    elif msg_type == MessageType.UI_TASK_START:
        task_str = data.get("task", "")
        try:
            task = TaskType(task_str)
        except ValueError:
            task = TaskType.DOWNLOAD
        return UITaskMessage(task=task)
    elif msg_type == MessageType.UI_TASK_STOP:
        return UITaskStopMessage(was_cancelled=data.get("was_cancelled", False))
    elif msg_type == MessageType.UI_TASK_STOPPING:
        return UITaskStoppingMessage()
    elif msg_type == MessageType.GIT_CLONE_DONE:
        return GitCloneDoneMessage(path=data.get("path", ""))
    elif msg_type == MessageType.LOCAL_SCAN_COMPLETE:
        return LocalScanCompleteMessage(results=data.get("results"))
    else:
        return LogMessage(message=str(data))


def file_info_to_dict(file_info: FileInfo) -> Dict[str, Any]:
    """Convert FileInfo to dictionary for backward compatibility."""
    result = {"name": file_info.name, "type": file_info.type.value, "size": file_info.size, "size_str": file_info.size_str, "rel_path": file_info.rel_path}
    if file_info.url:
        result["url"] = file_info.url
    if file_info.path:
        result["path"] = file_info.path
    return result


def dict_to_file_info(data: Dict[str, Any]) -> FileInfo:
    """Convert dictionary to FileInfo."""
    type_str = data.get("type", "File")
    try:
        file_type = FileType(type_str)
    except ValueError:
        file_type = FileType.FILE

    return FileInfo(name=data.get("name", ""), type=file_type, size=data.get("size", 0), size_str=data.get("size_str", ""), rel_path=data.get("rel_path", ""), url=data.get("url"), path=data.get("path"))

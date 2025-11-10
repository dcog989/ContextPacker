"""
Centralized error handling utilities to eliminate code duplication.
Provides standardized error handling patterns for worker functions.
"""

import shutil
import subprocess
import traceback
from typing import Optional, Dict, Any

from .types import StatusMessage, LogMessage, StatusType, message_to_dict


class WorkerErrorHandler:
    """Centralized error handling for worker functions."""

    def __init__(self, log_queue, shutdown_event):
        self.log_queue = log_queue
        self.shutdown_event = shutdown_event

    def log_message(self, message: str, message_type: str = "log"):
        """Safely log a message if not shutting down."""
        if not self.shutdown_event.is_set():
            if message_type == "log":
                msg = LogMessage(message=message)
            else:
                msg = StatusMessage(status=StatusType.ERROR, message=message)
            self.log_queue.put(message_to_dict(msg))

    def handle_worker_exception(self, exception: Exception, context: str) -> Dict[str, Any]:
        """
        Standardized exception handling for worker functions.

        Args:
            exception: The exception that occurred
            context: Context description for where the error occurred

        Returns:
            Dictionary with error status and message
        """
        error_msg = f"An error occurred in {context}: {str(exception)}"
        tb_str = traceback.format_exc()

        self.log_message(f"  -> ERROR in {context}: {str(exception)}")
        self.log_message(f"  -> Traceback: {tb_str}")

        status_msg = StatusMessage(status=StatusType.ERROR, message=error_msg)
        return message_to_dict(status_msg)

    def handle_process_cleanup(self, process, timeout: int = 2) -> bool:
        """
        Standardized process cleanup with timeout and error handling.

        Args:
            process: subprocess.Popen instance to clean up
            timeout: Timeout for graceful termination

        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=timeout)
                    self.log_message("Process terminated gracefully.")
                    return True
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
                    self.log_message("Process killed forcefully.")
                    return True
        except Exception as e:
            self.log_message(f"Warning during process cleanup: {e}")
            return False

        return True

    def handle_stream_cleanup(self, process) -> None:
        """
        Standardized stream cleanup for subprocess objects.

        Args:
            process: subprocess.Popen instance with streams to close
        """
        stream_names = ["stdout", "stderr", "stdin"]
        for stream_name in stream_names:
            try:
                stream = getattr(process, stream_name, None)
                if stream:
                    stream.close()
            except Exception:
                pass  # Stream might already be closed or invalid


def create_process_with_flags(command, creation_flags: Optional[int] = None):
    """
    Create a subprocess with standardized creation flags for the platform.

    Args:
        command: Command list to execute
        creation_flags: Optional custom creation flags

    Returns:
        subprocess.Popen instance
    """
    from .platform_detection import get_process_creation_flags

    if creation_flags is None:
        creation_flags = get_process_creation_flags()

    return subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,  # Remove text encoding for binary-heavy repos
        creationflags=creation_flags,
    )


def safe_stream_enqueue(stream, queue, shutdown_event):
    """
    Safely read from a stream and enqueue messages with error handling.

    Args:
        stream: Input stream to read from
        queue: Queue to put messages into
        shutdown_event: Event to check for shutdown
    """
    try:
        for line in iter(stream.readline, b""):
            # Decode binary line to text for logging
            try:
                decoded_line = line.decode("utf-8", errors="replace").rstrip()
                if not shutdown_event.is_set():
                    queue.put(decoded_line)
            except (UnicodeDecodeError, AttributeError):
                # Fallback for problematic binary data
                if not shutdown_event.is_set():
                    queue.put(f"[Binary data: {len(line)} bytes]")
    finally:
        # Ensure stream is always closed, even if an exception occurs
        try:
            stream.close()
        except Exception:
            pass  # The stream might already be closed or invalid


def validate_tool_availability(tool_name: str) -> bool:
    """
    Check if a required tool is available in the system PATH.

    Args:
        tool_name: Name of the tool to check

    Returns:
        True if tool is available, False otherwise
    """
    return shutil.which(tool_name) is not None


def create_tool_missing_error(tool_name: str) -> Dict[str, Any]:
    """
    Create a standardized error message for missing tools.

    Args:
        tool_name: Name of the missing tool

    Returns:
        Dictionary with error status and message
    """
    error_msg = f"ERROR: {tool_name} is not installed or not found in your system's PATH. Please install {tool_name} to use this feature."
    status_msg = StatusMessage(status=StatusType.ERROR, message=error_msg)
    return message_to_dict(status_msg)

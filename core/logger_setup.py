import logging
import sys
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QObject, Signal

from .utils import get_app_data_dir


class QtLogEmitter(QObject):
    """
    A QObject that holds the signal for logging.
    This is necessary to avoid method name collisions between QObject.emit and logging.Handler.emit.
    """

    log_received = Signal(str)


class QtLogHandler(logging.Handler):
    """
    A custom logging handler that calls a signal on a QtLogEmitter for each log record.
    """

    def __init__(self, emitter: QtLogEmitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record):
        """
        Formats the log record and emits the signal via the emitter.
        """
        msg = self.format(record)
        self.emitter.log_received.emit(msg)


def setup_logging(log_level_str: str, log_max_size_mb: int, log_backup_count: int):
    """
    Configures the root logger for the application.

    Args:
        log_level_str: The desired logging level as a string (e.g., "DEBUG", "INFO").
        log_max_size_mb: The max size of a log file in megabytes.
        log_backup_count: The number of backup log files to keep.

    Returns:
        The QtLogEmitter instance whose signal can be connected to the UI.
    """
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    log_formatter = logging.Formatter("[%(asctime)s] [%(levelname)-8s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # --- File Handler ---
    app_data_dir = get_app_data_dir()
    log_dir = app_data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / "app.log"
    # Use RotatingFileHandler to prevent log files from growing indefinitely
    file_handler = RotatingFileHandler(log_file_path, maxBytes=log_max_size_mb * 1024 * 1024, backupCount=log_backup_count, encoding="utf-8")
    file_handler.setFormatter(log_formatter)

    # --- UI Emitter and Handler ---
    qt_log_emitter = QtLogEmitter()
    qt_handler = QtLogHandler(qt_log_emitter)
    qt_handler.setFormatter(log_formatter)

    # --- Root Logger Configuration ---
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(qt_handler)

    # Redirect stdout/stderr to the logging system
    sys.stdout = StreamToLogger(root_logger, logging.INFO)
    sys.stderr = StreamToLogger(root_logger, logging.ERROR)

    logging.info(f"--- Logging started at level {log_level_str} ---")
    logging.info(f"Log file located at: {log_file_path}")

    return qt_log_emitter


class StreamToLogger:
    """
    A helper class to redirect stdout and stderr to the logging framework.
    """

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

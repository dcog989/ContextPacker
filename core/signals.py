from PySide6.QtCore import QObject, Signal
from .types import AppState, StatusMessage, ProgressMessage, FileSavedMessage, GitCloneDoneMessage, LocalScanCompleteMessage


class AppSignals(QObject):
    """
    Centralized signals for the application.
    Services emit these signals, and the UI controller listens to them.
    """

    # State Service Signals
    state_changed = Signal(AppState)

    # Task Service Signals
    task_status = Signal(StatusMessage)
    task_progress = Signal(ProgressMessage)
    file_saved = Signal(FileSavedMessage)
    git_clone_done = Signal(GitCloneDoneMessage)
    local_scan_complete = Signal(LocalScanCompleteMessage)
    task_shutdown_finished = Signal()


# Global instance to be shared across services and UI controller
app_signals = AppSignals()

from PySide6.QtCore import QObject, Signal


class WorkerSignals(QObject):
    """
    Defines signals for communication between worker threads and the main GUI thread.
    """

    # Signal to transmit a dataclass-formatted message from the worker queue
    message = Signal(object)

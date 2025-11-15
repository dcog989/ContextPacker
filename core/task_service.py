import concurrent.futures
import threading
import queue
import os
import logging

from .signals import app_signals
from .types import Message, LogMessage, StatusMessage, ProgressMessage, FileSavedMessage, GitCloneDoneMessage, LocalScanCompleteMessage


class TaskService:
    """Manages the lifecycle of background tasks using a thread pool."""

    def __init__(self):
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count())
        self._current_future: concurrent.futures.Future | None = None
        self._cancel_event: threading.Event | None = None

        self._message_queue = queue.Queue()
        self._queue_watcher_thread = threading.Thread(target=self._watch_queue, daemon=True, name="QueueWatcherThread")
        self._is_shutting_down = False
        self._queue_watcher_thread.start()
        logging.debug(f"[{threading.current_thread().name}] TaskService initialized.")

    def submit_task(self, task_fn, *args, **kwargs):
        """Submits a task to the thread pool and monitors it."""
        if self._current_future and not self._current_future.done():
            logging.error("Another task is already running.")
            return

        self._cancel_event = threading.Event()
        kwargs["message_queue"] = self._message_queue
        kwargs["cancel_event"] = self._cancel_event

        self._current_future = self._executor.submit(task_fn, *args, **kwargs)

    def cancel_current_task(self):
        """Signals the current task to cancel."""
        if self._cancel_event:
            self._cancel_event.set()

    def is_task_running(self) -> bool:
        """Checks if a task is currently active."""
        return bool(self._current_future and not self._current_future.done())

    def _watch_queue(self):
        """
        Worker thread that continuously reads from the message queue
        and emits corresponding signals.
        """
        while not self._is_shutting_down:
            try:
                message: Message | None = self._message_queue.get(timeout=1)

                if message is None:
                    continue

                if isinstance(message, StatusMessage):
                    app_signals.task_status.emit(message)
                elif isinstance(message, ProgressMessage):
                    app_signals.task_progress.emit(message)
                elif isinstance(message, FileSavedMessage):
                    app_signals.file_saved.emit(message)
                elif isinstance(message, GitCloneDoneMessage):
                    app_signals.git_clone_done.emit(message)
                elif isinstance(message, LocalScanCompleteMessage):
                    app_signals.local_scan_complete.emit(message)
                elif isinstance(message, LogMessage):
                    logging.info(message.message)
                else:
                    logging.warning(f"Unknown message type received: {type(message)}")

                self._message_queue.task_done()
            except queue.Empty:
                continue
        logging.debug(f"[{threading.current_thread().name}] Queue watcher loop finished.")

    def shutdown(self):
        """
        Initiates a non-blocking shutdown. A daemon waiter thread will signal
        the main application when it's safe to quit.
        """
        if self._is_shutting_down:
            return
        logging.debug(f"[{threading.current_thread().name}] TaskService shutdown initiated.")
        self._is_shutting_down = True
        self.cancel_current_task()

        shutdown_waiter = threading.Thread(target=self._wait_for_shutdown, daemon=True, name="ShutdownWaiterThread")
        shutdown_waiter.start()

    def _wait_for_shutdown(self):
        """
        Runs in a daemon thread. Blocks until the executor is shut down,
        then signals the main application that it is safe to quit.
        """
        logging.debug(f"[{threading.current_thread().name}] Waiting for thread pool to shut down...")
        self._executor.shutdown(wait=True)
        logging.debug(f"[{threading.current_thread().name}] Thread pool shut down.")

        logging.debug(f"[{threading.current_thread().name}] Finalizing queue watcher...")
        self._message_queue.put(None)
        if self._queue_watcher_thread.is_alive():
            self._queue_watcher_thread.join()
        logging.debug(f"[{threading.current_thread().name}] Queue watcher finished.")

        logging.debug(f"[{threading.current_thread().name}] Emitting task_shutdown_finished signal.")
        app_signals.task_shutdown_finished.emit()

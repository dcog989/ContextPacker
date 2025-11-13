# File: core/app_worker_manager.py
import threading
import queue
import concurrent.futures
import os


class WorkerManager:
    """Handles thread, queue, and executor management for the main application."""

    def __init__(self, app_instance):
        self.app = app_instance
        self.log_queue = queue.Queue()
        self.queue_listener_shutdown = threading.Event()
        self.shutdown_event = threading.Event()
        self.queue_listener_thread = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count())
        # FIXED: Track if we're in the middle of draining to prevent recursion
        self._draining = False
        self._drain_lock = threading.Lock()

    def start_queue_listener(self):
        """Start the queue listener thread if not already running."""
        if self.queue_listener_thread is None or not self.queue_listener_thread.is_alive():
            self.queue_listener_shutdown.clear()
            self.queue_listener_thread = threading.Thread(target=self._queue_listener_worker, daemon=True)
            self.queue_listener_thread.start()

    def stop_queue_listener(self, timeout=5.0):
        """
        Safely stop the queue listener thread.
        Returns: True if stopped cleanly, False if timeout occurred
        """
        if self.queue_listener_thread is None or not self.queue_listener_thread.is_alive():
            return True

        self.queue_listener_shutdown.set()

        try:
            # Put sentinel to unblock the thread waiting on get()
            self.log_queue.put(None, timeout=1.0)
        except queue.Full:
            pass

        self.queue_listener_thread.join(timeout=timeout)

        if self.queue_listener_thread.is_alive():
            self._drain_queue()
            return False

        self.queue_listener_thread = None
        return True

    def _queue_listener_worker(self):
        """Worker thread that processes messages from log_queue."""
        # Use a longer timeout to reduce unnecessary CPU usage when idle
        while not self.queue_listener_shutdown.is_set():
            try:
                # Issue 14: Increased timeout from 0.5 to 5.0 seconds
                msg_obj = self.log_queue.get(timeout=5.0)

                if msg_obj is None:
                    break

                self.app.signals.message.emit(msg_obj)
                self.log_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing queue message: {e}")
                continue

        self._drain_queue()

    def _drain_queue(self):
        """Process remaining messages with proper guards against recursion and hangs. (Uses max_drain_attempts to prevent infinite loop)."""
        # Prevent recursive calls
        with self._drain_lock:
            if self._draining:
                return
            self._draining = True

        try:
            # Safety limit to prevent infinite loops
            max_drain_attempts = 1000
            attempts = 0

            while attempts < max_drain_attempts:
                try:
                    msg_obj = self.log_queue.get_nowait()
                    if msg_obj is not None:
                        # Only emit if not shutting down and signal still exists
                        if not self.shutdown_event.is_set():
                            if hasattr(self.app, "signals") and hasattr(self.app.signals, "message"):
                                try:
                                    self.app.signals.message.emit(msg_obj)
                                except RuntimeError:
                                    # Signal may have been disconnected during shutdown
                                    pass
                        self.log_queue.task_done()
                    attempts += 1
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"Error draining queue: {e}")
                    attempts += 1
                    continue

            if attempts >= max_drain_attempts:
                print(f"Warning: Stopped draining queue after {max_drain_attempts} attempts")

        finally:
            self._draining = False

    def cleanup_workers(self):
        """
        Sends cancel signal to any running worker tasks and attempts to check their status.
        Returns: True if any worker is still running and the shutdown is deferred.
        """
        is_worker_running = False

        if self.app.worker_future and not self.app.worker_future.done():
            if not self.shutdown_event.is_set():
                # Don't set shutdown_event here - that's done in closeEvent after cleanup
                self.app.log_verbose("Waiting for main task to terminate...")
                if self.app.cancel_event:
                    self.app.cancel_event.set()
                self.app._toggle_ui_controls(False)
            is_worker_running = True

        if self.app.local_scan_future and not self.app.local_scan_future.done():
            if not self.shutdown_event.is_set():
                self.app.log_verbose("Waiting for file scanner to terminate...")

            if self.app.local_scan_cancel_event:
                self.app.local_scan_cancel_event.set()

            is_worker_running = True

        return is_worker_running

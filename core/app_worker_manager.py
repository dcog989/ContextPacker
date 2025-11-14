import threading
import queue
import concurrent.futures
import os
from .constants import QUEUE_LISTENER_STOP_TIMEOUT_SECONDS, QUEUE_GET_TIMEOUT_SECONDS, MAX_QUEUE_DRAIN_ATTEMPTS


class WorkerManager:
    """Handles thread, queue, and executor management for the main application."""

    def __init__(self, app_instance):
        self.app = app_instance
        self.log_queue = queue.Queue()
        self.queue_listener_shutdown = threading.Event()
        self.shutdown_event = threading.Event()
        self.queue_listener_thread = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count())
        self._draining = False
        self._drain_lock = threading.Lock()

    def start_queue_listener(self):
        """Start the queue listener thread if not already running."""
        if self.queue_listener_thread is None or not self.queue_listener_thread.is_alive():
            self.queue_listener_shutdown.clear()
            self.queue_listener_thread = threading.Thread(target=self._queue_listener_worker, daemon=True)
            self.queue_listener_thread.start()

    def stop_queue_listener(self, timeout=QUEUE_LISTENER_STOP_TIMEOUT_SECONDS):
        """
        Safely stop the queue listener thread.
        Returns: True if stopped cleanly, False if timeout occurred
        """
        if self.queue_listener_thread is None or not self.queue_listener_thread.is_alive():
            return True

        self.queue_listener_shutdown.set()

        try:
            # Put sentinel to unblock the thread waiting on get().
            self.log_queue.put_nowait(None)
        except Exception:
            pass

        self.queue_listener_thread.join(timeout=timeout)

        if self.queue_listener_thread.is_alive():
            return False

        self.queue_listener_thread = None
        return True

    def _queue_listener_worker(self):
        """Worker thread that processes messages from log_queue."""
        while not self.queue_listener_shutdown.is_set():
            try:
                # Check for shutdown before getting from queue to exit faster
                if self.shutdown_event.is_set():
                    break

                msg_obj = self.log_queue.get(timeout=QUEUE_GET_TIMEOUT_SECONDS)

                if msg_obj is None:
                    # Sentinel received, break the loop and proceed to drain/exit
                    break

                # Only emit if not shutting down AND the app is still alive
                if not self.shutdown_event.is_set() and not self.app._is_closing:
                    try:
                        self.app.signals.message.emit(msg_obj)
                    except (RuntimeError, AttributeError):
                        # Widget/signal was destroyed, ignore
                        pass

                self.log_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                if not self.shutdown_event.is_set():
                    print(f"Error processing queue message: {e}")
                continue

        # Only drain if not already shutting down
        if not self.shutdown_event.is_set():
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
            max_drain_attempts = MAX_QUEUE_DRAIN_ATTEMPTS
            attempts = 0

            while attempts < max_drain_attempts:
                try:
                    msg_obj = self.log_queue.get_nowait()
                    if msg_obj is not None:
                        # We are draining during shutdown; do not emit signals to the UI to prevent main thread event loop hang.
                        self.log_queue.task_done()
                    attempts += 1
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"Error draining queue: {e}")
                    attempts += 1
                    continue

            if attempts >= max_drain_attempts:
                print(f"Warning: Stopped draining queue after {MAX_QUEUE_DRAIN_ATTEMPTS} attempts")

        finally:
            self._draining = False

    def cleanup_workers(self):
        """
        Sends cancel signal to any running worker tasks and attempts to check their status.
        Returns: True if any worker is still running and the shutdown is deferred.
        """
        is_worker_running = False

        if self.app.state.worker_future and not self.app.state.worker_future.done():
            if not self.shutdown_event.is_set():
                # Don't set shutdown_event here - that's done in closeEvent after cleanup
                self.app.log_verbose("Waiting for main task to terminate...")
                if self.app.state.cancel_event:
                    self.app.state.cancel_event.set()
                self.app._toggle_ui_controls(False)
            is_worker_running = True

        if self.app.state.local_scan_future and not self.app.state.local_scan_future.done():
            if not self.shutdown_event.is_set():
                self.app.log_verbose("Waiting for file scanner to terminate...")

            if self.app.state.local_scan_cancel_event:
                self.app.state.local_scan_cancel_event.set()

            is_worker_running = True

        # FIXED: Don't clear shutdown event - let caller manage it
        return is_worker_running

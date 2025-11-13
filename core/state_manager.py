import threading


class StateManager:
    """Manages the application's runtime state."""

    def __init__(self):
        self.is_task_running: bool = False
        self.temp_dir: str | None = None
        self.final_output_path: str | None = None
        self.local_files_to_exclude: set = set()
        self.local_depth_excludes: set = set()
        self.gitignore_cache: dict = {}
        self.gitignore_cache_lock: threading.Lock = threading.Lock()
        self.worker_future = None
        self.cancel_event: threading.Event | None = None
        self.local_scan_future = None
        self.local_scan_cancel_event: threading.Event | None = None

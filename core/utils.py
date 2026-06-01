from pathlib import Path
import shutil
from datetime import datetime, timedelta
import sys


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        meipass_path = getattr(sys, "_MEIPASS", None)
        if meipass_path:
            base_path = Path(meipass_path)
        else:
            base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent.parent

    return base_path / relative_path


def get_app_data_dir():
    """Gets the Linux application data directory for persistent data."""
    return Path.home() / ".config" / "ContextPacker"


def cleanup_old_directories(base_dir, days_threshold):
    if not base_dir.is_dir():
        return

    cutoff = datetime.now() - timedelta(days=days_threshold)

    for subdir in base_dir.iterdir():
        if subdir.is_dir():
            try:
                dir_time = datetime.fromtimestamp(subdir.stat().st_mtime)
                parts = subdir.name.split("-")
                if len(parts) > 2:
                    try:
                        timestamp_str = f"{parts[-2]}-{parts[-1]}"
                        dir_time = datetime.strptime(timestamp_str, "%y%m%d-%H%M%S")
                    except ValueError:
                        pass
                if dir_time < cutoff:
                    shutil.rmtree(subdir, ignore_errors=True)
            except OSError, ValueError:
                continue


def open_folder(folder_path: str):
    """Opens a folder in the default file manager."""
    import subprocess

    path = Path(folder_path)
    if not path.is_dir():
        print(f"Error: Cannot open folder. Path is not a directory: {folder_path}")
        return

    try:
        subprocess.run(["xdg-open", str(path)], check=True)
    except Exception as e:
        print(f"Error: Could not open output folder: {e}")

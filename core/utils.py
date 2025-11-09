import platform
from pathlib import Path
import ctypes
import shutil
from datetime import datetime, timedelta


def get_app_data_dir():
    """Gets the platform-specific application data directory."""
    if platform.system() == "Windows":
        return Path.home() / "AppData" / "Local" / "ContextPacker"
    elif platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "ContextPacker"
    else:  # Linux
        return Path.home() / ".local" / "share" / "ContextPacker"


def cleanup_old_directories(base_dir, days_threshold):
    """Deletes subdirectories in base_dir older than a given number of days."""
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
            except (OSError, ValueError):
                continue


def set_title_bar_theme(window, is_dark):
    """Sets the title bar theme for a window on Windows."""
    if platform.system() != "Windows":
        return
    try:
        hwnd = window.winId()
        if hwnd:
            value = ctypes.c_int(1 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
    except Exception as e:
        print(f"Warning: Failed to set title bar theme: {e}")


def get_downloads_folder() -> str:
    if platform.system() == "Windows":
        try:
            from ctypes import wintypes, oledll

            class GUID(ctypes.Structure):
                _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", wintypes.BYTE * 8)]

            FOLDERID_Downloads = GUID(0x374DE290, 0x123F, 0x4565, (0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B))
            path_ptr = ctypes.c_wchar_p()
            oledll.ole32.CoInitialize(None)
            try:
                if oledll.shell32.SHGetKnownFolderPath(ctypes.byref(FOLDERID_Downloads), 0, None, ctypes.byref(path_ptr)) == 0:
                    path = path_ptr.value
                    if path:
                        return path
            finally:
                oledll.ole32.CoTaskMemFree(path_ptr)
                oledll.ole32.CoUninitialize()
        except Exception:
            # Fallback to the default if any Windows-specific API call fails
            pass
    return str(Path.home() / "Downloads")

import platform
import os
import winreg
from pathlib import Path


def _get_browser_binary_path_windows(browser_name):
    """
    Finds a browser's executable on Windows by checking registry keys
    and common file system locations.
    """
    search_config = {
        "chrome": {
            "reg_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
            ],
            "fs_paths": [r"Google\Chrome\Application\chrome.exe", r"Chromium\Application\chrome.exe"],
        },
        "msedge": {
            "reg_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
            ],
            "fs_paths": [r"Microsoft\Edge\Application\msedge.exe"],
        },
        "firefox": {
            "reg_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"),
            ],
            "fs_paths": [r"Mozilla Firefox\firefox.exe", r"Firefox Developer Edition\firefox.exe"],
        },
    }

    config = search_config.get(browser_name)
    if not config:
        return None

    for hive, subkey in config["reg_keys"]:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                path, _ = winreg.QueryValueEx(key, "")
                if Path(path).exists():
                    return path
        except FileNotFoundError:
            continue
        except Exception:
            continue

    base_paths = []
    for var in ["ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"]:
        path = os.environ.get(var)
        if path:
            base_paths.append(Path(path))
    if not os.environ.get("LOCALAPPDATA"):
        base_paths.append(Path.home() / "AppData" / "Local")

    for fs_path in config["fs_paths"]:
        for base in base_paths:
            full_path = base / fs_path
            if full_path.exists():
                return str(full_path)
    return None


def get_browser_binary_path(browser_name):
    """
    Finds the path to a browser's executable, checking common locations
    for the current operating system.
    """
    system = platform.system()
    if system == "Windows":
        return _get_browser_binary_path_windows(browser_name)

    paths_to_check = []
    if system == "Darwin":
        path_map = {
            "chrome": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
            "msedge": ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
            "firefox": ["/Applications/Firefox.app/Contents/MacOS/firefox"],
        }
        paths_to_check = path_map.get(browser_name, [])
    elif system == "Linux":
        path_map = {
            "chrome": ["/usr/bin/google-chrome", "/opt/google/chrome/chrome"],
            "msedge": ["/usr/bin/microsoft-edge"],
            "firefox": ["/usr/bin/firefox"],
        }
        paths_to_check = path_map.get(browser_name, [])

    if paths_to_check:
        for path in paths_to_check:
            if Path(path).exists():
                return path
    return None

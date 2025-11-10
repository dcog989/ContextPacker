"""
Centralized platform detection utilities to eliminate code duplication.
Provides standardized platform detection and configuration across the application.
"""

import platform
import os
from typing import Dict, Any, Union, List


class PlatformDetector:
    """Centralized platform detection and configuration."""

    _instance = None
    _platform_info = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_platform_info()
        return cls._instance

    def _initialize_platform_info(self) -> None:
        """Initialize platform information once and cache it."""
        self._platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "is_windows": platform.system() == "Windows",
            "is_macos": platform.system() == "Darwin",
            "is_linux": platform.system() == "Linux",
            "is_posix": os.name == "posix",
            "is_nt": os.name == "nt",
        }

    @property
    def system(self) -> str:
        """Get the system name (Windows, Darwin, Linux)."""
        return self._platform_info["system"]

    @property
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self._platform_info["is_windows"]

    @property
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self._platform_info["is_macos"]

    @property
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self._platform_info["is_linux"]

    @property
    def is_posix(self) -> bool:
        """Check if running on a POSIX system."""
        return self._platform_info["is_posix"]

    @property
    def is_nt(self) -> bool:
        """Check if running on an NT system (Windows)."""
        return self._platform_info["is_nt"]

    def get_process_creation_flags(self) -> int:
        """Get appropriate process creation flags for the current platform."""
        if self.is_windows:
            # Optimize Windows process creation to reduce overhead
            import subprocess

            return (
                subprocess.CREATE_NO_WINDOW  # 0x08000000 - No console window
                | 0x02000000  # DETACHED_PROCESS - Run in separate process group
                | 0x00000008  # CREATE_UNICODE_ENVIRONMENT - Unicode environment
            )
        return 0

    def get_environment_variables(self) -> Dict[str, str]:
        """Get platform-specific environment variables for paths."""
        env_vars = {}

        if self.is_windows:
            # Windows-specific environment variables
            env_vars.update(
                {
                    "PROGRAMFILES": os.environ.get("ProgramFiles", ""),
                    "PROGRAMFILES_X86": os.environ.get("ProgramFiles(x86)", ""),
                    "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", ""),
                    "APPDATA": os.environ.get("APPDATA", ""),
                    "USERPROFILE": os.environ.get("USERPROFILE", ""),
                }
            )
        else:
            # Unix-like systems environment variables
            env_vars.update(
                {
                    "HOME": os.environ.get("HOME", ""),
                    "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME", ""),
                    "XDG_DATA_HOME": os.environ.get("XDG_DATA_HOME", ""),
                    "XDG_CACHE_HOME": os.environ.get("XDG_CACHE_HOME", ""),
                }
            )

        return env_vars

    def get_common_paths(self) -> Dict[str, str]:
        """Get platform-specific common paths."""
        paths = {}

        if self.is_windows:
            # Windows paths
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))

            paths.update(
                {
                    "program_files": program_files,
                    "program_files_x86": program_files_x86,
                    "local_app_data": local_app_data,
                    "user_home": os.environ.get("USERPROFILE", os.path.expanduser("~")),
                }
            )
        else:
            # Unix-like paths
            home = os.environ.get("HOME", os.path.expanduser("~"))

            paths.update(
                {
                    "user_home": home,
                    "usr_bin": "/usr/bin",
                    "usr_local_bin": "/usr/local/bin",
                    "opt": "/opt",
                }
            )

        return paths

    def get_browser_paths(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """Get platform-specific browser installation paths."""
        if self.is_windows:
            return self._get_windows_browser_paths()
        elif self.is_macos:
            return self._get_macos_browser_paths()
        elif self.is_linux:
            return self._get_linux_browser_paths()
        else:
            return {}

    def _get_windows_browser_paths(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """Get Windows browser paths."""
        common_paths = self.get_common_paths()

        return {
            "chrome": {
                "paths": [
                    f"{common_paths['program_files']}\\Google\\Chrome\\Application\\chrome.exe",
                    f"{common_paths['program_files_x86']}\\Google\\Chrome\\Application\\chrome.exe",
                    f"{common_paths['local_app_data']}\\Google\\Chrome\\Application\\chrome.exe",
                ],
                "registry_keys": [
                    (r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                ],
            },
            "msedge": {
                "paths": [
                    f"{common_paths['program_files']}\\Microsoft\\Edge\\Application\\msedge.exe",
                    f"{common_paths['program_files_x86']}\\Microsoft\\Edge\\Application\\msedge.exe",
                ],
                "registry_keys": [
                    (r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                ],
            },
            "firefox": {
                "paths": [
                    f"{common_paths['program_files']}\\Mozilla Firefox\\firefox.exe",
                    f"{common_paths['program_files_x86']}\\Mozilla Firefox\\firefox.exe",
                    f"{common_paths['local_app_data']}\\Mozilla Firefox\\firefox.exe",
                ],
                "registry_keys": [
                    (r"Software\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"),
                ],
            },
        }

    def _get_macos_browser_paths(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """Get macOS browser paths."""
        return {
            "chrome": {
                "paths": [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                ],
            },
            "msedge": {
                "paths": [
                    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                ],
            },
            "firefox": {
                "paths": [
                    "/Applications/Firefox.app/Contents/MacOS/firefox",
                ],
            },
        }

    def _get_linux_browser_paths(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """Get Linux browser paths."""
        return {
            "chrome": {
                "paths": [
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable",
                    "/opt/google/chrome/chrome",
                ],
            },
            "msedge": {
                "paths": [
                    "/usr/bin/microsoft-edge",
                    "/usr/bin/microsoft-edge-stable",
                    "/opt/microsoft/msedge/msedge",
                ],
            },
            "firefox": {
                "paths": [
                    "/usr/bin/firefox",
                    "/usr/bin/firefox-esr",
                    "/usr/lib/firefox/firefox",
                ],
            },
        }

    def get_platform_info(self) -> Dict[str, Any]:
        """Get complete platform information."""
        return self._platform_info.copy()

    def __str__(self) -> str:
        """String representation of platform info."""
        return f"Platform: {self.system} (Release: {self._platform_info['release']})"


# Global instance for easy access
platform_detector = PlatformDetector()


def get_platform_detector() -> PlatformDetector:
    """Get the global platform detector instance."""
    return platform_detector


def is_windows() -> bool:
    """Convenience function to check if running on Windows."""
    return platform_detector.is_windows


def is_macos() -> bool:
    """Convenience function to check if running on macOS."""
    return platform_detector.is_macos


def is_linux() -> bool:
    """Convenience function to check if running on Linux."""
    return platform_detector.is_linux


def get_process_creation_flags() -> int:
    """Convenience function to get process creation flags."""
    return platform_detector.get_process_creation_flags()


def get_common_paths() -> Dict[str, str]:
    """Convenience function to get common paths."""
    return platform_detector.get_common_paths()


def get_browser_paths() -> Dict[str, Dict[str, Union[str, List[str]]]]:
    """Convenience function to get browser paths."""
    return platform_detector.get_browser_paths()

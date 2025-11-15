"""
Centralized platform detection utilities to eliminate code duplication.
Provides standardized platform detection and configuration across the application.
"""

import platform
import os
from typing import Dict, Any, Optional
import subprocess


class PlatformDetector:
    """Centralized platform detection and configuration."""

    _instance = None
    _platform_info: Optional[Dict[str, Any]] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_platform_info()
        return cls._instance

    def _initialize_platform_info(self):
        """Initialize platform information once and cache it."""
        if self._platform_info is not None:
            return
        self._platform_info = {
            "system": platform.system(),
            "is_windows": platform.system() == "Windows",
            "is_macos": platform.system() == "Darwin",
            "is_linux": platform.system() == "Linux",
        }

    @property
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        assert self._platform_info is not None
        return self._platform_info["is_windows"]

    @property
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        assert self._platform_info is not None
        return self._platform_info["is_macos"]

    @property
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        assert self._platform_info is not None
        return self._platform_info["is_linux"]

    def get_process_creation_flags(self) -> int:
        """Get appropriate process creation flags for the current platform."""
        if self.is_windows:
            # 0x08000000: CREATE_NO_WINDOW - No console window for subprocesses
            return subprocess.CREATE_NO_WINDOW
        return 0


# Global instance for easy access
platform_detector = PlatformDetector()


def is_windows() -> bool:
    """Convenience function to check if running on Windows."""
    return platform_detector.is_windows


def get_process_creation_flags() -> int:
    """Convenience function to get process creation flags."""
    return platform_detector.get_process_creation_flags()

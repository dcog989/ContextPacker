"""
Centralized platform detection utilities to eliminate code duplication.
Provides standardized platform detection and configuration across the application.
"""

import platform
from typing import Dict, Any, Optional


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
        if self._platform_info is not None:
            return
        self._platform_info = {
            "system": platform.system(),
            "is_linux": platform.system() == "Linux",
        }

    @property
    def is_linux(self) -> bool:
        assert self._platform_info is not None
        return self._platform_info["is_linux"]


# Global instance for easy access
platform_detector = PlatformDetector()

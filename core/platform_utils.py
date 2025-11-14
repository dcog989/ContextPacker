import platform
import os
from pathlib import Path


def get_browser_binary_path(browser_name):
    """
    Deprecated: ContextPacker now uses the 'requests' library and does not require external browsers.
    Kept for interface compatibility during migration.
    """
    return None

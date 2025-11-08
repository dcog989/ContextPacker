import sys
import os
from pathlib import Path
from selenium.webdriver.common.service import logger

# Get the base path for the PyInstaller bundle.
# We check for both _MEIPASS and _MEIPASS2 for compatibility with older versions.
base_path = getattr(sys, "_MEIPASS2", None) or getattr(sys, "_MEIPASS", None)

if base_path:
    # Construct the path to where selenium-manager should be inside the bundle.
    # The structure is preserved by `collect_data_files('selenium')`.
    sm_dir = Path(base_path) / "selenium" / "webdriver" / "common"

    if sys.platform == "win32":
        sm_path = sm_dir / "windows" / "selenium-manager.exe"
    elif sys.platform == "darwin":
        sm_path = sm_dir / "macos" / "selenium-manager"
    else:  # "linux"
        sm_path = sm_dir / "linux" / "selenium-manager"

    if sm_path.exists():
        logger.debug(f"Selenium Manager hook: Setting path to {sm_path}")
        os.environ["SE_MANAGER_PATH"] = str(sm_path)
    else:
        logger.warning(f"Selenium Manager hook: selenium-manager not found at expected path: {sm_path}")
else:
    # This block is for running from source and won't execute in a bundled app.
    logger.debug("Selenium Manager hook: Not running in a PyInstaller bundle.")

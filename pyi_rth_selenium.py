import sys
import os
from selenium.webdriver.common.service import logger

# This is the name of the folder where PyInstaller bundles data files
# for a one-file build. We check for both for compatibility.
wdm_path = getattr(sys, "_MEIPASS2", None) or getattr(sys, "_MEIPASS", None)

if wdm_path:
    logger.debug(f"Selenium Manager path set by hook: {wdm_path}")
    os.environ["SE_MANAGER_PATH"] = wdm_path
else:
    # Fallback when running from source (though this hook won't execute then)
    wdm_path = os.path.dirname(sys.executable)
    logger.debug(f"Selenium Manager path set to executable directory: {wdm_path}")
    os.environ["SE_MANAGER_PATH"] = wdm_path

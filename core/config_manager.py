import json
from pathlib import Path
import sys

CONFIG_FILENAME = "config.json"

DEFAULT_CONFIG = {
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.3351.121",
        "Mozilla/5.0 (iPhone17,1; CPU iPhone OS 18_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Mohegan Sun/4.7.4",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 7.0; SM-T827R4 Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.116 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
    ],
    "default_output_format": ".md",
    "default_local_excludes": [".archive/", ".git/", ".testing/", "*node_modules*", "build/", "dist/"],
    "binary_file_patterns": [
        "*.png",
        "*.jpg",
        "*.jpeg",
        "*.gif",
        "*.bmp",
        "*.ico",
        "*.svg",
        "*.zip",
        "*.rar",
        "*.7z",
        "*.tar",
        "*.gz",
        "*.pdf",
        "*.doc",
        "*.docx",
        "*.xls",
        "*.xlsx",
        "*.ppt",
        "*.pptx",
        "*.exe",
        "*.dll",
        "*.so",
        "*.dylib",
        "*.ai",
        "*.psd",
        "*.mp3",
        "*.wav",
        "*.flac",
        "*.mp4",
        "*.mov",
        "*.wmv",
        "*.eot",
        "*.ttf",
        "*.woff",
        "*.woff2",
    ],
    "max_build_logs": 21,
    "window_size": [-1, -1],
    "sash_position": 650,
}

_config = None


def get_base_path():
    """Gets the base path for data files, handling PyInstaller."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller bundle
        return Path(sys.executable).parent
    else:
        # Running from source (development)
        return Path(".")


def get_config():
    """Loads the config.json file, creating a default one if it doesn't exist."""
    global _config
    if _config is not None:
        return _config

    base_path = get_base_path()
    config_path = base_path / CONFIG_FILENAME
    if not config_path.exists():
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            _config = DEFAULT_CONFIG
        except Exception as e:
            print(f"Warning: Could not create default config file: {e}")
            _config = DEFAULT_CONFIG
        return _config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            loaded_config = json.load(f)
            # Ensure all default keys are present
            _config = DEFAULT_CONFIG.copy()
            _config.update(loaded_config)
    except Exception as e:
        print(f"Warning: Could not load config.json, using defaults: {e}")
        _config = DEFAULT_CONFIG

    return _config


def save_config(config_data):
    """Saves the provided configuration dictionary to config.json."""
    base_path = get_base_path()
    config_path = base_path / CONFIG_FILENAME
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print(f"Error: Could not save config file: {e}")

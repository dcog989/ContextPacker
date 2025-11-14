import json
from pathlib import Path
import sys

CONFIG_FILENAME = "config.json"

DEFAULT_CONFIG = {
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "python-requests/2.31.0",
        "ContextPacker-Bot/1.0",
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
    "max_age_logs": 21,
    "window_size": [-1, -1],
    "h_sash_state": None,
    "v_sash_state": None,
}

_config = None


def get_base_path():
    """Gets the base path for data files, handling PyInstaller."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
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

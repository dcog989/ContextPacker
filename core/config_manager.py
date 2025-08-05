import json
from pathlib import Path

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
}

_config = None


def get_config():
    """Loads the config.json file, creating a default one if it doesn't exist."""
    global _config
    if _config is not None:
        return _config

    config_path = Path(CONFIG_FILENAME)
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
            _config = json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config.json, using defaults: {e}")
        _config = DEFAULT_CONFIG

    return _config

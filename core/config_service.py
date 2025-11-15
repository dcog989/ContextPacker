import json
import sys
from pathlib import Path


class ConfigService:
    """Manages loading and saving of the application's configuration."""

    def __init__(self):
        self._config_filename = "settings.json"
        self._default_config = {
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
            "max_age_cache_days": 7,
            "window_size": [-1, -1],
            "window_pos": [-1, -1],
            "h_sash_state": None,
            "v_sash_state": None,
            "logging_level": "DEBUG",
            "log_max_size_mb": 3,
            "log_backup_count": 5,
        }
        self._config_dir = self._get_config_dir()
        self._config_path = self._config_dir / self._config_filename
        self.config = self._load_config()

    def _get_config_dir(self):
        """Gets the application data directory, ensuring it exists."""
        from .utils import get_app_data_dir

        app_dir = get_app_data_dir()
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    def _load_config(self):
        """Loads settings.json, creating a default one if it doesn't exist."""
        if not self._config_path.exists():
            try:
                with open(self._config_path, "w", encoding="utf-8") as f:
                    json.dump(self._default_config, f, indent=4)
                return self._default_config.copy()
            except IOError as e:
                print(f"Warning: Could not create default config file: {e}")
                return self._default_config.copy()

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
            # Merge loaded config with defaults to ensure all keys are present
            config = self._default_config.copy()
            config.update(loaded_config)
            return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config.json, using defaults: {e}")
            return self._default_config.copy()

    def get(self, key, default=None):
        """Gets a configuration value by key."""
        return self.config.get(key, default)

    def save_config(self):
        """Saves the current configuration dictionary to settings.json."""
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error: Could not save config file: {e}")

    def save_window_state(self, size, pos, h_splitter_state, v_splitter_state):
        """Saves window geometry and splitter states to the config."""
        self.config["window_size"] = [size.width(), size.height()]
        self.config["window_pos"] = [pos.x(), pos.y()]
        h_sash_qba = h_splitter_state.toBase64()
        v_sash_qba = v_splitter_state.toBase64()
        self.config["h_sash_state"] = bytes(h_sash_qba.data()).decode("utf-8")
        self.config["v_sash_state"] = bytes(v_sash_qba.data()).decode("utf-8")
        self.save_config()

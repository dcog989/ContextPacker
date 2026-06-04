import json
from pathlib import Path

from .utils import get_app_data_dir
from .types import Profile, profile_from_dict, profile_to_dict


PROFILES_DIR_NAME = "profiles"


class ConfigService:
    """Manages loading and saving of the application's configuration."""

    def __init__(self):
        self._config_filename = "settings.json"
        self._default_config = {
            "user_agents": [
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
                "python-requests/2.31.0",
                "ContextPacker-Bot/1.0",
            ],
            "default_output_format": ".md",
            "default_local_excludes": [
                ".archive/",
                ".git/",
                ".testing/",
                "__pycache__/",
                "*.pyc",
                ".venv/",
                ".env",
                ".idea/",
                ".DS_Store",
                "Thumbs.db",
                "*node_modules*",
                "build/",
                "dist/",
                "*.log",
            ],
            "binary_file_patterns": [
                "*.png",
                "*.jpg",
                "*.jpeg",
                "*.gif",
                "*.bmp",
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
            "logging_level": "INFO",
            "log_max_size_mb": 3,
            "log_backup_count": 5,
        }
        self._config_dir = self._get_config_dir()
        self._config_path = self._config_dir / self._config_filename

        # Separately store the mutable keys that the app changes
        self._mutable_keys = ["window_size", "window_pos", "h_sash_state", "v_sash_state"]
        # Separately store the user-editable keys that are not changed by the app at runtime
        self._static_keys = list(set(self._default_config.keys()) - set(self._mutable_keys))

        # Read/Write config. All keys are initialized from defaults, then overwritten by file.
        # This dict holds the runtime values.
        self.config = self._load_config()

        # Cache the static keys read from file so save_config(save_static=False)
        # doesn't need to re-read the file on every call.
        self._cached_static_config = {k: self.config[k] for k in self._static_keys}

    def _get_config_dir(self):
        """Gets the application data directory, ensuring it exists."""
        app_dir = get_app_data_dir()
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    def _load_config(self):
        """Loads settings.json, creating a default one if it doesn't exist."""
        # Use a copy of defaults for a foundation
        config = self._default_config.copy()

        if not self._config_path.exists():
            try:
                # Write only the static keys to the initial file, letting mutable keys use defaults
                initial_config_content = {k: v for k, v in self._default_config.items() if k in self._static_keys}
                with open(self._config_path, "w", encoding="utf-8") as f:
                    json.dump(initial_config_content, f, indent=4)
                # The runtime config remains the full default set (config.copy())
                return config
            except IOError as e:
                print(f"Warning: Could not create default config file: {e}")
                return config.copy()

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
            # Merge loaded config with defaults.
            # This ensures all keys are present and respects user's static config.
            config.update(loaded_config)
            return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config.json, using defaults: {e}")
            return config.copy()

    def get(self, key, default=None):
        """Gets a configuration value by key."""
        return self.config.get(key, default)

    def save_config(self, save_static=False):
        """
        Saves the current configuration dictionary to settings.json.

        Args:
            save_static (bool): If True, saves ALL keys (static and mutable).
                                If False (default), only saves the mutable keys,
                                merged with the cached static keys — no file read needed.
        """
        if save_static:
            config_to_save = self.config.copy()
            self._cached_static_config = {k: config_to_save[k] for k in self._static_keys}
        else:
            # Merge mutable keys into cached static config — avoids a file read.
            config_to_save = self._cached_static_config.copy()
            for key in self._mutable_keys:
                if key in self.config:
                    config_to_save[key] = self.config[key]

        # 3. Write the new content
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config_to_save, f, indent=4)
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

        # Only save mutable keys (window state)
        self.save_config(save_static=False)

    def _get_profiles_dir(self) -> Path:
        profiles_dir = self._config_dir / PROFILES_DIR_NAME
        profiles_dir.mkdir(parents=True, exist_ok=True)
        return profiles_dir

    def save_profile(self, profile: Profile) -> None:
        profiles_dir = self._get_profiles_dir()
        filepath = profiles_dir / f"{profile.name}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(profile_to_dict(profile), f, indent=2)

    def load_profile(self, name: str) -> Profile | None:
        profiles_dir = self._get_profiles_dir()
        filepath = profiles_dir / f"{name}.json"
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        try:
            return profile_from_dict(data)
        except Exception:
            return None

    def list_profile_names(self) -> list[str]:
        profiles_dir = self._get_profiles_dir()
        return sorted(f.stem for f in profiles_dir.glob("*.json") if f.suffix == ".json")

    def delete_profile(self, name: str) -> None:
        profiles_dir = self._get_profiles_dir()
        filepath = profiles_dir / f"{name}.json"
        if filepath.exists():
            filepath.unlink()

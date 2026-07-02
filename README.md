# ![ContextPacker logo](./assets/icons/ContextPacker.svg) ContextPacker

Desktop app to scrape websites, clone Git repos, or package local files into a single Markdown/TXT/XML file optimized for LLM consumption.

![ContextPacker screenshot](./assets/images/screen-1.png)

---

## Features

- **Web Crawl** — scrape pages, convert to Markdown, package into one file
- **Git Clone** — enter a Git URL to clone and automatically switch to local packaging mode
- **Local Packaging** — package a local directory (e.g. a codebase) into a single file
- **Smart Filtering** — respects `.gitignore`, hides binaries/images, custom exclude patterns
- **Multiple Outputs** — `.md`, `.txt`, or `.xml`
- **Dark/Light Theme** — auto-detects system theme
- **Settings File** — `~/.config/ContextPacker/settings.json` (user-agents, excludes, log config, etc.)

---

## Advanced Configuration (`settings.json`)

Created on first run at `~/.config/ContextPacker/settings.json`. User-managed keys:

| Key                      | Default                       | Notes |
| :---                     | :---                          | :---  |
| `logging_level`          | `"INFO"`                      | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `log_max_size_mb`        | `3`                           | Max log size before rotation |
| `log_backup_count`       | `5`                           | Rotated log files to keep |
| `user_agents`            | `[...]`                       | List the crawler cycles through |
| `default_output_format`  | `".md"`                       | `.md`, `.txt`, or `.xml` |
| `default_local_excludes` | `[".archive/", ".git/", ...]` | fnmatch patterns for directory scans |
| `binary_file_patterns`   | `[*.png, *.jpg, ...]`         | Toggled via "Hide Images + Binaries" checkbox |
| `max_age_cache_days`     | `7`                           | Auto-cleanup of old session dirs |

Window state keys (`window_size`, `h_sash_state`, etc.) are managed automatically on close.

---

## Installation

### Requirements

- **Git** — for cloning repos
- **Python 3.14+** and **uv** (`pip install uv` or [uv docs](https://docs.astral.sh/uv/))

### Run from Source

```sh
git clone <repo-url> && cd ContextPacker
uv sync
uv run python app.py
```

### Pre-built Binary (Linux)

```sh
7za x dist/ContextPacker-Linux-x64-v*.7z
sudo cp -r ContextPacker /opt/
sudo ln -s /opt/ContextPacker/ContextPacker /usr/local/bin/contextpacker
```

---

## Updating

```sh
uv pip list --outdated                       # check outdated
uv tree --outdated                           # check outdated in tree
uv sync --upgrade                            # bump all deps
uv lock --upgrade-package <name> && uv sync  # bump one package
```

---

## Usage

Two modes selected via radio buttons:

**Web Crawl** — Enter a URL. For websites, configure depth/pacing/path filters and click **Download & Convert**. For Git URLs, the app clones and auto-switches to local mode.

**Local Directory** — Pick a directory, configure excludes, toggle `.gitignore`/binary filtering, set depth, click **Package**. Output goes to `~/Downloads/`.

---

## Building

```sh
uv run nox -s build        # production build + compressed archive
uv run nox -s build_run    # debug build (console enabled) + launch
uv run nox -s clean        # remove build/ dist/ __pycache__
```

---

## Install to menu

```sh
uv run nox -s install      # writes ~/.local/share/applications/contextpacker.desktop
uv run nox -s uninstall    # removes it
```

The entry launches via `uv run`, so it always uses the latest source and syncs dependencies automatically. KDE Plasma picks up the new entry within a few seconds; if it does not appear, log out and back in.

---

## Development

```text
uv run ruff check           # lint
uv run ruff check --fix     # lint + auto-fix
uv run ruff format          # format
```

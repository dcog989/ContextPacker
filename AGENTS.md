# AGENTS.md

ContextPacker is a **PySide6 desktop application** (Python 3.14+) that scrapes websites, clones Git repos, or packages local files into a single Markdown/TXT/XML file optimized for LLM consumption. Uses repomix as a library for final packaging.

## Dev Environment

Linux CachyOS, KDE Plasma 6, Wayland, Btrfs, fish shell, Ghostty. `uv` package manager.

## Tech Stack

- **Python** `>=3.14, <3.15`, **PySide6** `>=6.10`, **uv** + `uv.lock`
- **Build**: hatchling, PyInstaller `>=6.16`, nox `>=2026.4`
- **Crawling**: requests, beautifulsoup4, lxml, markdownify
- **Validation**: pydantic `>=2.13`
- **Packaging**: repomix `>=0.5` (imported as Python library)
- **Linting**: ruff, line-length = 120
- **No test framework** — no test suite exists

## Architecture (MVC-like with Signal Bus)

```
UI (ui/)  --signals-->  UiController  --calls-->  Services (core/)
                        (app_ui_controller.py)     |-- StateService
                                                   |-- TaskService (thread pool + msg queue)
                                                   |-- ConfigService (settings.json)
                                                   |-- ThemeManager (dark/light)
                                                   |-- LoggerSetup (file + Qt signal)
                                                         |
                                                    worker functions
                                                    (core/actions.py, crawler.py, packager.py)
```

- **Signal bus**: `AppSignals(QObject)` in `core/signals.py` — all typed Qt signals flow through this
- **Message queue**: Workers enqueue typed dataclasses (`LogMessage`, `StatusMessage`, `ProgressMessage`, `FileSavedMessage`, `GitCloneDoneMessage`, `LocalScanCompleteMessage`) — daemon watcher thread dispatches them to the right signal
- **State machine**: `StateService` tracks `AppState.IDLE | TASK_RUNNING | TASK_STOPPING`
- **Thread pool**: `TaskService` wraps `ThreadPoolExecutor` + `threading.Event()` for cancellation
- **Factory pattern**: `InputPanelFactory`, `OutputPanelFactory` construct UI widget groups
- **Cooperative cancellation**: Workers check `cancel_event.is_set()`; subprocess cleanup uses terminate → kill → timeout escalation

## Entry Points

| Purpose | File/Command |
|---|---|
| Application | `app.py` — `App(QMainWindow)` bootstraps services, loads font, applies theme |
| CLI | `contextpacker = "app:main"` in pyproject.toml |
| Run directly | `uv run python app.py` |
| Nox run | `uv run nox -s run` |
| Nox build (prod) | `uv run nox -s build` |
| Nox build+run (debug) | `uv run nox -s build_run` |
| Nox clean | `uv run nox -s clean` |

Session names use underscores matching noxfile.py function names.

## Key Modules

### `core/actions.py` — Worker functions (run in thread pool)
- `clone_repo_worker()` — validates git, URL, path; runs `git clone --depth 1` via subprocess; path traversal protection
- `packaging_worker()` — wraps `run_repomix` with progress handler
- `get_local_files_worker()` — BFS directory scan with gitignore/mtime-cached patterns, fnmatch filtering
- `create_session_dir()` — creates `cache/session-YYMMDD-HHMMSS/`

### `core/crawler.py` — Web crawler
- `crawl_website()` — BFS crawl with requests.Session, depth tracking, URL normalization, markdownify conversion
- Politeness: `random.uniform(min_pause, max_pause)` ms between requests
- Filters: subdomain, include/exclude path patterns, max_pages limit

### `core/packager.py` — Repomix wrapper
- `run_repomix()` — configures `RepomixConfig`, creates `RepoProcessor`, calls `processor.process()`

### `core/config_service.py` — settings.json persistence
- `~/.config/ContextPacker/settings.json` — user-editable runtime config
- `_mutable_keys` (app-managed: window state, sash positions) vs `_static_keys` (user-managed: excludes, agents, log config)
- `save_config(save_static=False)` preserves static keys by default

### `core/state_service.py` — State machine
- `current_state` + `set_state()` emits `state_changed` signal

### `core/task_service.py` — Thread pool + message queue
- `submit_task(task_fn, ...)` — injects `message_queue` and `cancel_event`
- `cancel_current_task()` / `shutdown()` — cooperative + daemon waiter thread

### `core/types.py` — Enums, dataclasses, type alias
- `Message = LogMessage | StatusMessage | ProgressMessage | FileSavedMessage | GitCloneDoneMessage | LocalScanCompleteMessage`
- `file_info_to_dict()` / `dict_to_file_info()` for backward compat

### `core/constants.py` — All magic numbers
- Timer intervals: `BATCH_UPDATE_INTERVAL_MS=250`, `EXCLUDE_UPDATE_INTERVAL_MS=500`, `UI_UPDATE_INTERVAL_MS=1000`
- `UI_TABLE_INSERT_CHUNK_SIZE=50`, `UNLIMITED_DEPTH_VALUE=9`, `MAX_LOG_LINES=1000`
- Process cleanup: `PROCESS_CLEANUP_TIMEOUT_SECONDS=2`, `PROCESS_FORCE_KILL_WAIT_SECONDS=1`

### `core/error_handling.py` — Cleanup utilities
- `WorkerErrorHandler` — process cleanup (graceful → force kill → error), stream cleanup
- `safe_stream_enqueue()` — reads subprocess stdout binary, decodes, enqueues LogMessage
- `validate_tool_availability()` / `create_tool_missing_error()`

### `core/theme_manager.py` — Dark/light mode
- Detects system dark via `QPalette.Window.lightnessF() < 0.5`
- Dynamic SVG icons: `update_theme_icon()`, `update_copy_icon()` — recolors fill at runtime
- Accent color: green `#2E8B57`

### `core/icon_utils.py` — SVG utilities
- `colorize_svg()` — replaces `fill="#000000"` in SVG text
- `render_svg_to_pixmap()` — QSvgRenderer + QPainter (with cleanup)
- `create_themed_svg_icon()` — combined pipeline

### `core/logger_setup.py` — Logging
- RotatingFileHandler at `~/.config/ContextPacker/logs/app.log`
- `QtLogHandler` emits log records as Qt signals for UI display
- `StreamToLogger` captures stdout/stderr

### `core/utils.py` — General
- `resource_path()` — resolves assets for PyInstaller frozen builds (`sys._MEIPASS`) and dev
- `get_app_data_dir()` → `~/.config/ContextPacker`
- `cleanup_old_dirs()` — removes session dirs older than `max_age_cache_days`
- `open_folder()` — `xdg-open` (Linux-specific)

### `core/signals.py` — Signal bus
- `AppSignals(QObject)` — `state_changed`, `task_status`, `task_progress`, `file_saved`, `git_clone_done`, `local_scan_complete`, `task_shutdown_finished`

### `core/config.py` — Pydantic model
- `CrawlerConfig` — validated crawler settings with `check_pause_values()` validator

### `core/version.py` — Version
- `__version__` from `importlib.metadata.version("contextpacker")` fallback `"0.0.0-dev"`

### `ui/main_window.py` — MainWindow(QWidget)
- Horizontal QSplitter: input panels | (file list/log + output panels)
- 50+ widget attributes declared for static analysis
- `add_scraped_files_batch()` — chunked batch insertion via `QTimer.singleShot(0)`
- `populate_local_file_list()` — full table population
- `manage_log_size()` — trims first 25% when > 1000 lines
- Context menu: "Clear Log" on verbose log widget
- Splitter state restore from config on init

### `ui/input_panels.py` — InputPanelFactory
- `create_crawler_panel()` — URL, user-agent, max pages, depth, pause (ms), path filters, checkboxes, button
- `create_local_panel()` — directory, excludes, gitignore, hide-binaries, depth
- `create_system_panel()` — logo + theme switch button

### `ui/output_panels.py` — OutputPanelFactory
- `create_list_log_widgets()` — stacked QTableWidget (web/local), progress bar, file count, delete button; QTextEdit log
- `create_output_group()` — filename, timestamp, format dropdown, Package button, copy button

### `ui/styles.py` — AppTheme (300+ line Qt stylesheet)
- Dark/light color palettes with green accent
- `_setup_themed_icons()` — generates cached PNG icons in app data dir (up/down arrow, checkmark)
- Covers: QWidget, QSplitter, QGroupBox, QLabel, QTextEdit#VerboseLog, QLineEdit, QSpinBox, QComboBox, QPushButton, QPushButton#PrimaryButton, QPushButton#ThemeSwitchButton, QCheckBox, QRadioButton, QTableWidget, QHeaderView, QProgressBar, QScrollBar

### `ui/about_dialog.py` — AboutDialog(QDialog)
- Logo, title, description, "I drink your milkshake" quote, version, GitHub link

## Build Output

- **Development**: `uv run python app.py`
- **Debug build** (console enabled): `dist/ContextPacker/ContextPacker`
- **Production build**: `dist/ContextPacker/ContextPacker` + `dist/ContextPacker-Linux-x64-v{version}.7z` (via 7za, fallback .zip)

## File System Access

### Allowed
- `.agents/`, `.github/`, `.vscode/`
- `core/`, `ui/`, `assets/`, `scripts/`
- Root: `app.py`, `noxfile.py`, `pyproject.toml`, `ContextPacker.spec`, `config.json`, `README.md`, `AGENTS.md`, `.gitignore`, `ruff.config`
- App data: `~/.config/ContextPacker/`

### Disallowed
- `.ai/`, `.docs/`, `.git/`, `build/`, `dist/`, `node_modules/`, `logs/`
- `uv.lock`, `repomix.config.json`, `.repomixignore`

## Coding Principles

- Keep existing conventions when modifying
- KISS, DRY, YAGNI
- Self-documenting code via clear naming (not comments)
- Comments only for workarounds or non-obvious logic
- No magic numbers — use `core/constants.py`
- **Do NOT create docs files** unless explicitly instructed
- Batch UI updates (50-row chunks) to keep UI responsive
- All worker functions accept `message_queue` + `cancel_event` kwargs
- All typed messages go through the signal bus pattern

## Common Patterns

- **Message enqueue**: Worker calls `message_queue.put(StatusMessage(...))`, watcher thread routes to correct signal
- **Cancel check**: `if cancel_event.is_set(): return` at strategic points in workers
- **Subprocess safety**: `create_process_with_flags()` then `safe_stream_enqueue()` on reader thread; cleanup in `finally` block
- **Config access**: `ConfigService.get(key, default)` for runtime reads; `ConfigService.save_window_state()` on close
- **Theme SVG icons**: path stored in widget attr, recolored via `colorize_svg()` at theme toggle
- **Resource paths**: always use `resource_path("assets/...")` for assets
- **State guards**: `if state_service.current_state != AppState.IDLE: return` before starting tasks

## Key Workflows

### Web Crawl
1. User enters URL → UiController detects Git URL or regular URL
2. **Git URL**: `clone_repo_worker()` → `GitCloneDoneMessage` → switches to local file mode
3. **Regular URL**: `crawl_website()` with `CrawlerConfig` → BFS crawl → emits `FileSavedMessage` per page
4. UI batch-updates file list via 250ms timer
5. Completion: `StatusMessage(SOURCE_COMPLETE)` → state returns to IDLE

### Local Directory
1. User selects local dir → `get_local_files_worker()`
2. BFS scan with gitignore/binary/exclude filtering → `LocalScanCompleteMessage`
3. UI populates local file table

### Package
1. User clicks "Package" → `packaging_worker()` → `run_repomix()`
2. Repomix progress intercepted via log handler → `ProgressMessage` (batched every 10)
3. On `PACKAGE_COMPLETE`: progress 100%, opens output folder, state → IDLE

## Interaction Style

- do not pretend to understand how the user feels. no "You're right to be frustrated." etc.
- no analogies
- be concise, be precise
- answer the question asked, no 'helpful' suggestions

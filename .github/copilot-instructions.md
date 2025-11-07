## ContextPacker — Quick AI dev guide

This file gives an automated coding agent the minimal, actionable context needed to be productive in this repository.

1. Big picture

- Entrypoint: `app.py` — constructs the wxPython GUI and wires `TaskHandler` + `core` functions.
- Core responsibilities in `core/`: crawling (`crawler.py`), packaging (`packager.py`), UI actions (`actions.py`), and orchestration (`task_handler.py`).
- UI lives in `ui/` (panels, widgets, dialogs). `ui.main_frame.MainFrame` builds the main layout and delegates actions to `App` in `app.py`.

2. Cross-component patterns to follow

- Threading + messaging: background workers use `threading.Thread` and send structured messages to a `log_queue` (`queue.Queue`). The UI consumes messages and updates controls via `wx.CallAfter`.
  - Common message types: `log`, `file_saved`, `progress`, `status` (see `app.App._queue_listener_worker` and `core/actions`).
- Packaging: `core.packager.run_repomix()` runs `repomix.RepoProcessor`. Use `resource_path()` for bundled assets (handles PyInstaller's `_MEIPASS`).
- Local file scanning: `get_local_files()` merges `.repomixignore`, optional `.gitignore`, and user excludes. Note: `max_depth == 9` is treated as "unlimited".

3. Key developer workflows (commands)

- Install & dev run with Poetry:
  - `poetry install`
  - `poetry run python app.py`
- Build tasks via Nox (project root):
  - Build for production: `poetry run nox -s build`
  - Build and run for debugging: `poetry run nox -s build-run`
  - Clean artifacts: `poetry run nox -s clean`

4. Important implementation details & gotchas

- UI must only be updated from the main thread. Use `wx.CallAfter(...)` or push events through `log_queue`.
- Subprocess handling follows a cancellable pattern (there are cancel Events passed to worker threads, see `_clone_repo_worker`). On Windows, subprocesses use `creationflags=subprocess.CREATE_NO_WINDOW`.
- Packaging writes the final file to the user Downloads folder; `run_repomix()` expects exclude patterns and reports progress on `log_queue`.

5. Conventions when editing or adding code

- Keep UI code in `ui/` and core logic in `core/`.
- New background tasks should accept a `cancel_event` and `log_queue` and post structured messages rather than manipulating UI directly.
- Use `core.packager.resource_path()` for any filesystem references to assets so packaged builds work.

6. Integration points & external dependencies

- Selenium — used by the crawler. Requires a local browser installation.
- Repomix — used for producing the final packaged file.
- wxPython — UI runtime; running the app requires a desktop environment.

Files to inspect first when making changes: `app.py`, `core/actions.py`, `core/packager.py`, `core/crawler.py`, `ui/main_frame.py`.

If anything important is missing (CI steps, internal packaging hooks, or test commands), tell me where to look and I will update this file. Feedback welcome.

## How to run locally — troubleshooting

Quick checklist and common fixes when running the app on Windows (pwsh):

- Create the virtual environment & install deps:

```pwsh
poetry install
poetry shell # optional: activate the environment
poetry run python app.py
```

- If wxPython fails to install: the project pins a Windows wheel in `pyproject.toml`; ensure you're using the same Python minor version (3.14) or adjust the wheel to match your interpreter.
- Selenium crawling requires a browser; you can run the GUI without a browser but crawling will fail. Make sure Edge/Chrome/Firefox is installed and on PATH if using driver binaries.
- Git clone flow requires `git` on PATH. If cloning fails, verify `git --version` runs in the same environment the app uses.
- Common Selenium driver issues: either install a matching browser driver or use a driver manager. Logs from the crawler are emitted to the UI `log_queue` and appear in the app window.
- If packaging fails with Repomix errors, open the UI logs (List panel) or run a minimal repro by calling `core.packager.run_repomix()` from a small script to reproduce the traceback.

If you want, I can add a short troubleshooting script (checks for `git`, browser, and Python version) and a small README snippet for contributors.

Tip: there's a helper included: `scripts/check_env.py` and `scripts/check_env.ps1` — run `poetry run python scripts/check_env.py` or `.\scripts\check_env.ps1` to validate your environment.

import shutil
import subprocess
from pathlib import Path

import nox

# --- Configuration ---
APP_NAME = "ContextPacker"
DIST_DIR = Path("dist")
BUILD_DIR = Path("build")
SPEC_FILE = Path(f"{APP_NAME}.spec")


# --- Helper Functions ---
def get_project_version():
    with open("pyproject.toml") as f:
        for line in f:
            line = line.strip()
            if line.startswith("version"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "0.0.0"


# --- Nox Sessions ---
@nox.session(python=False)
def clean(session):
    """Remove all build artifacts and temporary files."""
    session.log("--- Cleaning Build Artifacts ---")

    for path in [DIST_DIR, BUILD_DIR]:
        if path.exists():
            session.log(f"Removing directory: {path}")
            shutil.rmtree(path, ignore_errors=True)

    session.log("Removing __pycache__ directories...")
    for pycache in Path(".").rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache, ignore_errors=True)

    session.log("Clean-up complete.")


@nox.session(python=False)
def run(session):
    """Run the application from source."""
    session.log("--- Launching Application ---")
    session.run("uv", "run", "python", "app.py", external=True)


@nox.session(python=False)
def build_run(session):
    """Build the app in debug mode and run it."""
    session.log("--- Building and Running (Debug) ---")

    build(session, debug=True, skip_clean=True)

    exe_path = DIST_DIR / APP_NAME / APP_NAME
    if exe_path.is_file():
        session.log(f"Build successful. Launching {exe_path}...")
        session.run(str(exe_path), external=True)
    else:
        session.error("Build failed or executable not found.")


@nox.session(python=False)
def build(session, debug=False, skip_clean=False):
    """Build the standalone executable."""
    build_type = "Debug" if debug else "Production"
    session.log(f"--- Building Executable ({build_type}) ---")

    session.log("Syncing dependencies with uv...")
    session.run("uv", "sync", external=True)

    if not skip_clean:
        clean(session)

    original_spec = SPEC_FILE.read_text()
    try:
        if debug:
            session.log("Modifying spec file for debug build (console=True).")
            modified_spec = original_spec.replace("console=False", "console=True")
            SPEC_FILE.write_text(modified_spec)
        else:
            session.log("Ensuring spec file is set for production build (console=False).")
            modified_spec = original_spec.replace("console=True", "console=False")
            SPEC_FILE.write_text(modified_spec)

        session.log("Running PyInstaller...")
        session.run("uv", "run", "pyinstaller", "--clean", "--log-level", "ERROR", str(SPEC_FILE), external=True)

    finally:
        session.log("Restoring original spec file.")
        SPEC_FILE.write_text(original_spec)

    exe_path = DIST_DIR / APP_NAME / APP_NAME
    if not exe_path.is_file():
        session.error("PyInstaller build finished, but the executable could not be found.")

    session.log(f"Build complete! Executable at: {exe_path}")

    if not debug:
        archive(session, exe_path)

    session.log("Opening output folder...")
    subprocess.run(["xdg-open", str(DIST_DIR.resolve())])


def archive(session, exe_path):
    """Create a compressed archive of the build."""
    session.log("--- Archiving Production Build ---")
    version = get_project_version()
    build_dir = exe_path.parent

    changelog_path = build_dir / "CHANGELOG.md"
    session.log(f"Generating changelog at {changelog_path}")
    try:
        git_log = subprocess.run(
            ["git", "log", "--pretty=format:- %s (%h)"], capture_output=True, text=True, check=True
        ).stdout
        changelog_path.write_text(git_log, encoding="utf-8")
    except (subprocess.CalledProcessError, FileNotFoundError):
        session.warn("Failed to generate changelog. Is Git installed?")

    if shutil.which("7za"):
        archive_name = f"ContextPacker-Linux-x64-v{version}.7z"
        archive_path = DIST_DIR / archive_name
        session.log(f"Compressing build output to {archive_path} using 7za...")
        session.run("7za", "a", "-t7z", "-m0=LZMA2", "-mx=3", str(archive_path), f"{build_dir}/*", external=True)
    else:
        session.warn("7za not found in PATH. Falling back to .zip compression.")
        archive_name = f"ContextPacker-Linux-x64-v{version}"
        archive_path = DIST_DIR / archive_name
        session.log(f"Compressing build output to {archive_path}.zip...")
        shutil.make_archive(str(archive_path), "zip", build_dir)

    session.log("Archiving complete.")

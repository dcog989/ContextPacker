"""Small environment diagnostic for ContextPacker.

Checks (Windows-focused):
- Python major/minor (project requires >=3.10, <3.15)
- `git` on PATH
- Presence of a browser (Edge/Chrome/Firefox) on PATH
- Key Python packages: wx, selenium, repomix

Exit codes:
0 = all critical checks passed
1 = one or more critical checks failed

Run from PowerShell/CMD with the project's virtualenv active:

    poetry run python scripts/check_env.py

"""

from __future__ import annotations

import shutil
import sys
import importlib
import os
import traceback
import subprocess
import re
from pathlib import Path


def check_python_version(min_major=3, min_minor=10, max_minor=14):
    v = sys.version_info
    ok = v.major == min_major and min_minor <= v.minor <= max_minor
    return ok, f"{v.major}.{v.minor}.{v.micro}"


def which_any(names: list[str]) -> str | None:
    """Return the first executable name found on PATH or common install locations.

    On Windows browsers are frequently not added to PATH, so check common
    Program Files / Local AppData locations for Edge/Chrome/Firefox.
    """
    # First try PATH lookup
    for n in names:
        found = shutil.which(n)
        if found:
            return found

    # On Windows, check common installation locations for browsers
    if os.name == "nt":
        candidates: dict[str, list[Path]] = {
            "msedge": [
                Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            ],
            "chrome": [
                Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            ],
            "firefox": [
                Path(os.environ.get("PROGRAMFILES", "")) / "Mozilla Firefox" / "firefox.exe",
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Mozilla Firefox" / "firefox.exe",
            ],
            "chromium": [
                Path(os.environ.get("PROGRAMFILES", "")) / "Chromium" / "Application" / "chromium.exe",
                Path(os.environ.get("LOCALAPPDATA", "")) / "Chromium" / "Application" / "chromium.exe",
            ],
        }

        for name in names:
            if name in candidates:
                for p in candidates[name]:
                    try:
                        if p and p.exists():
                            return str(p)
                    except Exception:
                        continue

    return None


def try_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


def main() -> int:
    critical_issues = []
    warnings = []

    py_ok, py_ver = check_python_version()
    print(f"Python: {py_ver} (required >=3.10,<3.15)")
    if not py_ok:
        critical_issues.append("Unsupported Python version. Use Python 3.10 - 3.14 to match the pinned wheels in pyproject.toml.")

    git_exec = which_any(["git"])
    print(f"git: {'found' if git_exec else 'missing'}")
    if not git_exec:
        critical_issues.append("`git` not found on PATH. Install Git to use repository clone features.")

    browser = which_any(["msedge", "chrome", "firefox", "chromium"])
    print(f"Browser: {browser if browser else 'none found (Edge/Chrome/Firefox)'}")
    if not browser:
        warnings.append("No supported browser found on PATH. Selenium crawling will not work without a browser and driver.")

    # Check webdriver binaries commonly used by Selenium
    webdriver_names = ["chromedriver", "msedgedriver", "geckodriver"]
    found_webdrivers = {}
    missing_webdrivers = []
    for wd in webdriver_names:
        wd_path = which_any([wd])
        if wd_path:
            found_webdrivers[wd] = wd_path
        else:
            missing_webdrivers.append(wd)

    # Check local driver caches before attempting remote installs
    local_driver_dirs = [Path(__file__).parent.parent / ".drivers", Path.home() / ".wdm" / "drivers"]
    driver_filenames = {"chromedriver": "chromedriver.exe", "msedgedriver": "msedgedriver.exe", "geckodriver": "geckodriver.exe"}

    for d in local_driver_dirs:
        try:
            if not d.exists():
                continue
            for wd in list(missing_webdrivers):
                fname = driver_filenames.get(wd)
                if not fname:
                    continue
                # walk the driver cache looking for the exe
                for p in d.rglob(fname):
                    if p.exists():
                        found_webdrivers[wd] = str(p)
                        try:
                            missing_webdrivers.remove(wd)
                        except ValueError:
                            pass
                        break
        except Exception:
            continue

    if found_webdrivers:
        for k, v in found_webdrivers.items():
            print(f"webdriver {k}: found at {v}")
    else:
        print("webdriver: none found (chromedriver/msedgedriver/geckodriver)")

    if missing_webdrivers:
        # Attempt to auto-install drivers if webdriver_manager is available.
        wm_installed = try_import("webdriver_manager")
        if wm_installed:
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                from webdriver_manager.firefox import GeckoDriverManager

                installed = []
                install_errors = []
                for wd in missing_webdrivers:
                    try:
                        if wd == "chromedriver":
                            path = ChromeDriverManager().install()
                        elif wd == "msedgedriver":
                            path = EdgeChromiumDriverManager().install()
                        elif wd == "geckodriver":
                            path = GeckoDriverManager().install()
                        else:
                            path = None

                        # Validate install result
                        if path and isinstance(path, (str, bytes)):
                            installed.append((wd, str(path)))
                            print(f"Downloaded webdriver {wd}: {path}")
                        else:
                            install_errors.append(f"{wd}: install() returned no path")
                    except Exception as e:
                        install_errors.append(f"{wd}: {e}")

                if install_errors:
                    warnings.append(f"webdriver_manager install issues: {'; '.join(install_errors)}")

                # Re-run lookup to report driver presence for successfully installed ones
                if installed:
                    for k, p in installed:
                        found = which_any([k])
                        if not found:
                            # Some drivers install into cache paths not on PATH; report the installed path
                            found_webdrivers[k] = p
                        else:
                            found_webdrivers[k] = found
                    missing_webdrivers = [m for m in missing_webdrivers if m not in found_webdrivers]
            except Exception as e:
                warnings.append(f"Attempted webdriver_manager install failed: {e}")
                # Fallback: try to detect browser version and give manual driver download hints
                try:
                    if browser and Path(browser).exists():
                        # Run the browser with --version to extract numeric version
                        cmd = [browser, "--version"]
                        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        output = (proc.stdout or proc.stderr or "").strip()
                        m = re.search(r"(\d+)\.(\d+)\.(\d+)", output)
                        major = m.group(1) if m else None

                        warnings.append("Browser version detection: " + (output or "unknown"))

                        if "edge" in str(browser).lower() or "msedge" in str(browser).lower():
                            if major:
                                latest_release_url = f"https://msedgedriver.azureedge.net/LATEST_RELEASE_{major}_WINDOWS"
                                manual_dl = "https://msedgedriver.azureedge.net/{version}/edgedriver_win64.zip"
                                warnings.append(f"If automatic download fails, query {latest_release_url} to get a version, then download {manual_dl} replacing {{version}} with that value.")
                            else:
                                warnings.append("If automatic download fails, get msedgedriver from: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
                        elif "chrome" in str(browser).lower() or "google" in str(browser).lower():
                            if major:
                                warnings.append(f"Chromedriver: check https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major} then download https://chromedriver.storage.googleapis.com/{{version}}/chromedriver_win32.zip")
                            else:
                                warnings.append("Chromedriver manual downloads: https://sites.google.com/chromium.org/driver/")
                        elif "firefox" in str(browser).lower() or "mozilla" in str(browser).lower():
                            warnings.append("Geckodriver downloads: https://github.com/mozilla/geckodriver/releases")
                except Exception:
                    warnings.append("Could not run browser to detect version for manual driver hints.")
        else:
            warnings.append(f"Missing webdriver binaries: {', '.join(missing_webdrivers)}. Install 'webdriver_manager' to let the script auto-download drivers, or place drivers on PATH.")

    # Check important packages
    required_pkgs = [
        ("wx", "wxpython"),
        ("selenium", "selenium"),
        ("repomix", "repomix"),
    ]
    missing_pkgs = []
    for mod, friendly in required_pkgs:
        ok = try_import(mod)
        print(f"import {mod}: {'OK' if ok else 'MISSING'}")
        if not ok:
            missing_pkgs.append(friendly)

    if missing_pkgs:
        warnings.append(f"Missing Python packages: {', '.join(missing_pkgs)}. Run `poetry install` in the project root.")

    print("\nSummary:")
    if not critical_issues and not warnings:
        print("  ✓ Environment looks good for basic development and running the GUI.")
        return 0

    if critical_issues:
        print("  Critical issues:")
        for it in critical_issues:
            print(f"   - {it}")

    if warnings:
        print("  Warnings:")
        for it in warnings:
            print(f"   - {it}")

    # Return non-zero when critical issues or warnings exist (treat warnings as non-critical failures to surface problems)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

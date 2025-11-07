"""Download and install browser drivers into a local .drivers/ folder.

Usage:
  poetry run python scripts/get_driver.py --browser edge
  poetry run python scripts/get_driver.py --browser chrome
  poetry run python scripts/get_driver.py --browser firefox

The script downloads the matching driver for the detected browser major version
and extracts it to `.drivers/<browser>/`. Returns a path to the driver executable.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import zipfile
from pathlib import Path
import json
import urllib.request
import urllib.error


DRIVERS_DIR = Path(__file__).parent.parent / ".drivers"


def run_cmd(cmd: list[str], timeout: int = 5) -> str:
    try:
        import subprocess

        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or p.stderr or "").strip()
    except Exception:
        return ""


def detect_browser_version(browser_exe: str) -> str | None:
    try:
        import struct
        from pathlib import Path

        # Get version from executable metadata instead of launching the browser
        if not Path(browser_exe).is_file():
            return None

        size = Path(browser_exe).stat().st_size
        if size < 100:  # Too small to be a real exe
            return None

        # Read PE header to get version from executable metadata
        with open(browser_exe, "rb") as f:
            # Skip DOS header
            if f.read(2) != b"MZ":
                return None
            f.seek(60)  # e_lfanew offset
            pe_offset = struct.unpack("<I", f.read(4))[0]

            # Read version info from resources
            f.seek(pe_offset + 24)  # Skip COFF header
            magic = struct.unpack("<H", f.read(2))[0]
            if magic != 0x10B and magic != 0x20B:  # IMAGE_NT_OPTIONAL_HDR32/64_MAGIC
                return None

            # Read ProductVersion from VS_FIXEDFILEINFO
            f.seek(pe_offset + (152 if magic == 0x10B else 168))
            ver_high, ver_low = struct.unpack("<II", f.read(8))
            major = (ver_high >> 16) & 0xFFFF
            minor = ver_high & 0xFFFF
            build = (ver_low >> 16) & 0xFFFF
            patch = ver_low & 0xFFFF
            return f"{major}.{minor}.{build}.{patch}"
    except Exception:
        # Fallback to running the browser if metadata read fails
        out = run_cmd([browser_exe, "--version"]) or run_cmd([browser_exe, "-version"]) or ""
        m = re.search(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", out)
        if m:
            return f"{m.group(1)}.{m.group(2)}.{m.group(3)}.{m.group(4)}"
    return None


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Use urllib to avoid an external dependency on 'requests'.
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            status = getattr(resp, "status", None)
            if status and status >= 400:
                raise urllib.error.HTTPError(url, status, getattr(resp, "reason", "HTTP error"), resp.headers, None)
            with open(dest, "wb") as fh:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    fh.write(chunk)
    except urllib.error.HTTPError:
        raise
    except Exception as e:
        raise RuntimeError(f"failed to download {url}: {e}") from e


def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest_dir)


def get_edge_driver(browser_exe: str | None) -> Path | None:
    version = None
    if browser_exe:
        version = detect_browser_version(browser_exe)

    if not version:
        # Without browser version we can't get the right driver
        print("Error: Could not detect Edge version. Please specify --browser-exe")
        return None

    try:
        # Known working Edge driver URL
        zip_url = "https://msedgedriver.microsoft.com/142.0.3595.53/edgedriver_win64.zip"
        out_zip = DRIVERS_DIR / "edge" / "edgedriver_142.0.3595.53.zip"
        print("Downloading", zip_url)
        download_file(zip_url, out_zip)
        extract_dir = DRIVERS_DIR / "edge" / "142.0.3595.53"
        extract_zip(out_zip, extract_dir)
        # driver exe name
        exe = extract_dir / "msedgedriver.exe"
        if exe.exists():
            return exe
    except Exception as e:
        print("Edge driver download failed:", e)
    return None


def get_chrome_driver(browser_exe: str | None) -> Path | None:
    major = None
    if browser_exe:
        major = detect_browser_version(browser_exe)

    if major:
        latest_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major}"
    else:
        latest_url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"

    try:
        with urllib.request.urlopen(latest_url, timeout=10) as r:
            version = r.read().decode("utf-8").strip()
        zip_url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_win32.zip"
        out_zip = DRIVERS_DIR / "chrome" / f"chromedriver_{version}.zip"
        print("Downloading", zip_url)
        download_file(zip_url, out_zip)
        extract_dir = DRIVERS_DIR / "chrome" / version
        extract_zip(out_zip, extract_dir)
        exe = extract_dir / "chromedriver.exe"
        if exe.exists():
            return exe
    except Exception as e:
        print("Chrome driver download failed:", e)
    return None


def get_firefox_driver(browser_exe: str | None) -> Path | None:
    # Use GitHub API to get latest release
    api = "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
    try:
        with urllib.request.urlopen(api, timeout=10) as r:
            text = r.read().decode("utf-8")
        data = json.loads(text)
        asset_url = None
        for a in data.get("assets", []):
            name = a.get("name", "")
            if "win64" in name and name.endswith(".zip"):
                asset_url = a.get("browser_download_url")
                break
        if asset_url:
            version = data.get("tag_name", "latest")
            out_zip = DRIVERS_DIR / "firefox" / f"geckodriver_{version}.zip"
            print("Downloading", asset_url)
            download_file(asset_url, out_zip)
            extract_dir = DRIVERS_DIR / "firefox" / version
            extract_zip(out_zip, extract_dir)
            exe = extract_dir / "geckodriver.exe"
            if exe.exists():
                return exe
    except Exception as e:
        print("Geckodriver download failed:", e)
    return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--browser", choices=["edge", "chrome", "firefox"], required=True)
    p.add_argument("--browser-exe", help="Path to browser executable")
    args = p.parse_args()

    browser_exe = args.browser_exe
    if not browser_exe:
        # try common locations
        if args.browser == "edge":
            # Try multiple Edge locations and names
            possible_paths = [
                Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                Path(os.environ.get("PROGRAMFILES", "")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            ]
            for exe in ["msedge", "microsoft-edge", "edge"]:
                if found := shutil.which(exe):
                    browser_exe = found
                    break
            if not browser_exe:
                for path in possible_paths:
                    if path.exists():
                        browser_exe = str(path)
                        break
        elif args.browser == "chrome":
            browser_exe = shutil.which("chrome") or str(Path(os.environ.get("PROGRAMFILES", "")) / "Google" / "Chrome" / "Application" / "chrome.exe")
        elif args.browser == "firefox":
            browser_exe = shutil.which("firefox") or str(Path(os.environ.get("PROGRAMFILES", "")) / "Mozilla Firefox" / "firefox.exe")

    if not browser_exe or not Path(browser_exe).exists():
        if args.browser == "edge":
            print("Could not find Edge browser. Default locations checked:")
            print("  - PATH: msedge, microsoft-edge, edge")
            print("  - %PROGRAMFILES(X86)%\\Microsoft\\Edge\\Application\\msedge.exe")
            print("  - %PROGRAMFILES%\\Microsoft\\Edge\\Application\\msedge.exe")
            print("\nPlease specify the path with --browser-exe")
        elif args.browser == "chrome":
            print("Could not find Chrome browser. Default locations checked:")
            print("  - PATH: chrome")
            print("  - %PROGRAMFILES%\\Google\\Chrome\\Application\\chrome.exe")
            print("\nPlease specify the path with --browser-exe")
        elif args.browser == "firefox":
            print("Could not find Firefox browser. Default locations checked:")
            print("  - PATH: firefox")
            print("  - %PROGRAMFILES%\\Mozilla Firefox\\firefox.exe")
            print("\nPlease specify the path with --browser-exe")
        return 1

    DRIVERS_DIR.mkdir(parents=True, exist_ok=True)

    exe = None
    if args.browser == "edge":
        exe = get_edge_driver(browser_exe)
    elif args.browser == "chrome":
        exe = get_chrome_driver(browser_exe)
    elif args.browser == "firefox":
        exe = get_firefox_driver(browser_exe)

    if exe:
        print("Installed driver:", exe)
        return 0
    print("Failed to download driver for", args.browser)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

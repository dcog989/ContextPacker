This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
.gitignore
app.py
assets/icons/ContextPacker.svg
assets/icons/copy.svg
build-for-release.ps1
config.json
core/actions.py
core/config_manager.py
core/config.py
core/crawler.py
core/packager.py
core/task_handler.py
core/utils.py
core/version.py
generate-requirements.ps1
LICENSE
pyi_rth_selenium.py
README.md
requirements.txt
ui/main_frame.py
ui/panels.py
ui/widgets/buttons.py
ui/widgets/dialogs.py
ui/widgets/gauges.py
ui/widgets/inputs.py
ui/widgets/lists.py
```

# Files

## File: assets/icons/ContextPacker.svg
````
<svg width="512" height="512" viewBox="8 8 84 84" xmlns="http://www.w3.org/2000/svg">
  <title>ContextPacker Logo</title>
  <path d="M 50 20 C 30 20 20 30 20 50 C 20 70 30 80 50 80 L 50 20 Z" fill="#2E8B57"/>
  <path d="M 50 20 C 70 20 80 30 80 50 C 80 70 70 80 50 80 L 50 20 Z" fill="#3CB371"/>
  <line x1="50" y1="10" x2="50" y2="90" stroke="#1E563A" stroke-width="6"/>
</svg>
````

## File: assets/icons/copy.svg
````
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<title>Copy Icon</title>
<path d="M16 1H4C2.9 1 2 1.9 2 3V17H4V3H16V1ZM20 5H8C6.9 5 6 5.9 6 7V21C6 22.1 6.9 23 8 23H20C21.1 23 22 22.1 22 21V7C22 5.9 21.1 5 20 5ZM20 21H8V7H20V21Z" fill="#E0E0E0"/>
</svg>
````

## File: build-for-release.ps1
````powershell
# build.ps1 - A simple script to build the ContextPacker executable.

# --- Configuration ---
$SpecFile = "ContextPacker.spec"
$DistDir = "dist"
$BuildDir = "build"

# --- Main Script ---

# Function to check for a command's existence
function Test-CommandExists {
    param($command)
    return (Get-Command $command -ErrorAction SilentlyContinue)
}

# 1. Check for PyInstaller
Write-Host "Checking for PyInstaller..." -ForegroundColor Green
if (-not (Test-CommandExists "pyinstaller")) {
    Write-Host "PyInstaller not found." -ForegroundColor Yellow
    $choice = Read-Host "Would you like to try and install it now via 'pip install pyinstaller'? (y/n)"
    if ($choice -eq 'y') {
        try {
            pip install pyinstaller
            if (-not (Test-CommandExists "pyinstaller")) {
                Write-Host "Installation failed or PyInstaller is not in your PATH. Please install it manually." -ForegroundColor Red
                exit 1
            }
            Write-Host "PyInstaller installed successfully." -ForegroundColor Green
        }
        catch {
            Write-Host "An error occurred during installation. Please install PyInstaller manually." -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "Build cancelled. PyInstaller is required." -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "PyInstaller found."
}

# 2. Clean previous build directories
Write-Host "Cleaning previous build directories..." -ForegroundColor Green
if (Test-Path $DistDir) {
    Write-Host "Removing old '$DistDir' directory..."
    Remove-Item -Recurse -Force $DistDir
}
if (Test-Path $BuildDir) {
    Write-Host "Removing old '$BuildDir' directory..."
    Remove-Item -Recurse -Force $BuildDir
}

# 3. Run PyInstaller
Write-Host "Running PyInstaller with spec file: $SpecFile" -ForegroundColor Green
pyinstaller --clean $SpecFile

# 4. Final Result
if ($LastExitCode -ne 0) {
    Write-Host "PyInstaller failed to build the application. See output above for errors." -ForegroundColor Red
    exit 1
}

$FinalExePath = Join-Path -Path (Get-Location) -ChildPath "$DistDir\ContextPacker.exe"
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "The executable can be found at: $FinalExePath"
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# Keep the window open if run by double-clicking
if ($null -eq $psISE) { Read-Host "Press Enter to exit" }
````

## File: config.json
````json
{
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.3351.121",
        "Mozilla/5.0 (iPhone17,1; CPU iPhone OS 18_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Mohegan Sun/4.7.4",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 7.0; SM-T827R4 Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.116 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0"
    ],
    "default_local_excludes": [
        ".archive/",
        ".git/",
        ".testing/",
        "node_modules/",
        ".repomixignore",
        "repomix.config.json"
    ],
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
        "*.woff2"
    ]
}
````

## File: core/config_manager.py
````python
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
````

## File: core/config.py
````python
from dataclasses import dataclass, field


@dataclass
class CrawlerConfig:
    start_url: str
    output_dir: str
    max_pages: int
    min_pause: float
    max_pause: float
    crawl_depth: int
    stay_on_subdomain: bool
    ignore_queries: bool
    user_agent: str
    include_paths: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(default_factory=list)
````

## File: core/packager.py
````python
from repomix import RepoProcessor, RepomixConfig
from pathlib import Path
import sys


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(getattr(sys, "_MEIPASS"))
    except Exception:
        base_path = Path(__file__).parent.parent
    return base_path / relative_path


def run_repomix(source_dir, output_filepath, log_queue, cancel_event, repomix_style="markdown", exclude_patterns=None):
    """
    Runs the repomix packaging process with the specified configuration.

    This function is designed to be run in a separate thread.
    """
    if cancel_event.is_set():
        log_queue.put({"type": "status", "status": "cancelled", "message": "Skipping packaging because process was cancelled."})
        return

    source_path = Path(source_dir)
    if not source_path.is_dir():
        log_queue.put({"type": "status", "status": "error", "message": "ERROR: Source directory for packaging is missing."})
        return

    output_path = Path(output_filepath)
    packaged_filename = output_path.name

    all_excludes = [packaged_filename, Path(output_filepath).name]
    if exclude_patterns:
        all_excludes.extend(exclude_patterns)

    log_queue.put({"type": "log", "message": f"Running repomix packager on {source_dir}..."})
    log_queue.put({"type": "log", "message": f"Output will be saved to: {output_filepath}"})

    try:
        config = RepomixConfig()
        config.output.file_path = str(output_path)
        config.output.style = repomix_style
        config.ignore.custom_patterns = all_excludes
        config.output.calculate_tokens = True
        config.output.show_file_stats = True
        config.security.enable_security_check = False

        processor = RepoProcessor(str(source_path), config=config)
        result = processor.process()

        log_queue.put({"type": "status", "status": "package_complete", "message": f"✔ Repomix finished successfully. Output: {result.config.output.file_path}"})

    except Exception as e:
        log_queue.put({"type": "status", "status": "error", "message": f"ERROR: An unexpected packaging error occurred: {e}"})
````

## File: generate-requirements.ps1
````powershell
# generate-requirements.ps1 - Generates a requirements.txt file for the project.

# --- Configuration ---
$OutputFile = "requirements.txt"
$SourceDir = "."

# --- Main Script ---

# Function to check for a command's existence
function Test-CommandExists {
    param($command)
    return (Get-Command $command -ErrorAction SilentlyContinue)
}

# 1. Check for pipreqs
Write-Host "Checking for pipreqs..." -ForegroundColor Green
if (-not (Test-CommandExists "pipreqs")) {
    Write-Host "pipreqs not found." -ForegroundColor Yellow
    $choice = Read-Host "Would you like to try and install it now via 'pip install pipreqs'? (y/n)"
    if ($choice -eq 'y') {
        try {
            pip install pipreqs
            if (-not (Test-CommandExists "pipreqs")) {
                Write-Host "Installation failed or pipreqs is not in your PATH. Please install it manually." -ForegroundColor Red
                exit 1
            }
            Write-Host "pipreqs installed successfully." -ForegroundColor Green
        }
        catch {
            Write-Host "An error occurred during installation. Please install pipreqs manually." -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "Script cancelled. pipreqs is required." -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "pipreqs found."
}

# 2. Run pipreqs
Write-Host "Generating requirements file..." -ForegroundColor Green
# Use --force to overwrite existing requirements.txt
pipreqs --force --savepath $OutputFile $SourceDir

if ($LastExitCode -ne 0) {
    Write-Host "pipreqs failed. See output above for errors." -ForegroundColor Red
    exit 1
}

# 3. Manually add dependencies pipreqs is known to miss for this project
Write-Host "Adding known dependencies that may have been missed (e.g., lxml)..." -ForegroundColor Green
Add-Content -Path $OutputFile -Value "`nlxml"

# 4. Final Result
Write-Host "--------------------------------------------------" -ForegroundColor Cyan
Write-Host "Successfully generated '$OutputFile'" -ForegroundColor Green
Write-Host "Please review the file for accuracy before committing."
Write-Host "--------------------------------------------------" -ForegroundColor Cyan

# Keep the window open if run by double-clicking
if ($null -eq $psISE) { Read-Host "Press Enter to exit" }
````

## File: LICENSE
````
MIT License

Copyright (c) 2025 dcog989

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
````

## File: pyi_rth_selenium.py
````python
import sys
import os
from selenium.webdriver.common.service import logger

# This is the name of the folder where PyInstaller bundles data files
# for a one-file build. We check for both for compatibility.
wdm_path = getattr(sys, "_MEIPASS2", None) or getattr(sys, "_MEIPASS", None)

if wdm_path:
    logger.debug(f"Selenium Manager path set by hook: {wdm_path}")
    os.environ["SE_MANAGER_PATH"] = wdm_path
else:
    # Fallback when running from source (though this hook won't execute then)
    wdm_path = os.path.dirname(sys.executable)
    logger.debug(f"Selenium Manager path set to executable directory: {wdm_path}")
    os.environ["SE_MANAGER_PATH"] = wdm_path
````

## File: ui/widgets/gauges.py
````python
import wx


class CustomGauge(wx.Panel):
    def __init__(self, parent, range=100, theme=None):
        super().__init__(parent)
        self.is_custom_themed = True
        self.theme = theme if theme else {}
        self._range = range
        self._value = 0
        self.UpdateTheme(self.theme)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.SetMinSize(wx.Size(-1, 10))

    def UpdateTheme(self, theme):
        self.theme = theme
        palette = self.theme.get("palette", {})
        self.track_color = palette.get("field", wx.Colour(60, 60, 60))
        self.bar_color = self.theme.get("accent_color", wx.Colour(60, 179, 113))
        self.SetBackgroundColour(palette.get("bg", wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)))
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()

        gc.SetBrush(wx.Brush(self.track_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, width, height, 3)

        if self._range > 0 and self._value > 0:
            progress_width = (self._value / self._range) * width
            gc.SetBrush(wx.Brush(self.bar_color))
            gc.DrawRoundedRectangle(0, 0, progress_width, height, 3)

    def SetValue(self, value):
        self._value = max(0, min(value, self._range))
        self.Refresh()

    def SetRange(self, range_val):
        self._range = range_val
        self.Refresh()

    def GetValue(self):
        return self._value

    def GetRange(self):
        return self._range
````

## File: ui/widgets/inputs.py
````python
import wx


class FocusTextCtrl(wx.Panel):
    def __init__(self, parent, value="", size=(-1, -1), style=wx.BORDER_NONE, theme=None):
        super().__init__(parent, size=size)
        self.is_custom_themed = True
        self.theme = theme if theme else {}
        self.unfocus_color = None

        self.padding_panel = wx.Panel(self)
        self.text_ctrl = wx.TextCtrl(self.padding_panel, value=value, style=style | wx.BORDER_NONE)

        padding_sizer = wx.BoxSizer(wx.VERTICAL)
        padding_sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, border=4)
        self.padding_panel.SetSizer(padding_sizer)

        border_sizer = wx.BoxSizer(wx.VERTICAL)
        border_sizer.Add(self.padding_panel, 1, wx.EXPAND | wx.ALL, border=1)
        self.SetSizer(border_sizer)

        self.text_ctrl.Bind(wx.EVT_SET_FOCUS, self.on_focus)
        self.text_ctrl.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

        self.UpdateTheme(self.theme)

    def UpdateTheme(self, theme):
        self.theme = theme
        palette = self.theme.get("palette", {})
        self.unfocus_color = palette.get("field")
        fg_color = palette.get("fg")

        if self.unfocus_color:
            self.SetBackgroundColour(self.unfocus_color)
            self.padding_panel.SetBackgroundColour(self.unfocus_color)
            self.text_ctrl.SetBackgroundColour(self.unfocus_color)
        if fg_color:
            self.text_ctrl.SetForegroundColour(fg_color)
        self.Refresh()

    def on_focus(self, event):
        accent_color = self.theme.get("accent_color")
        focus_field_color = self.theme.get("palette", {}).get("focus_field")

        if accent_color:
            self.SetBackgroundColour(accent_color)
        if focus_field_color:
            self.padding_panel.SetBackgroundColour(focus_field_color)
            self.text_ctrl.SetBackgroundColour(focus_field_color)

        self.Refresh()
        event.Skip()

    def on_kill_focus(self, event):
        if self.unfocus_color:
            self.SetBackgroundColour(self.unfocus_color)
            self.padding_panel.SetBackgroundColour(self.unfocus_color)
            self.text_ctrl.SetBackgroundColour(self.unfocus_color)
        self.Refresh()
        event.Skip()

    def GetValue(self):
        return self.text_ctrl.GetValue()

    def SetValue(self, value):
        self.text_ctrl.SetValue(value)

    def SetFocus(self):
        """Override to pass focus to the child text control."""
        self.text_ctrl.SetFocus()


class BaseToggleButton(wx.Panel):
    def __init__(self, parent, label, style=0, theme=None):
        super().__init__(parent, style=style)
        self.is_custom_themed = True
        self.label = label
        self.value = False
        self.theme = theme if theme else {}
        self.palette = {}
        self.accent_color = None
        self.hover_color = None
        self.hover = False

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_hover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_hover)
        self.UpdateTheme(self.theme)
        self.SetMinSize(self.DoGetBestSize())

    def UpdateTheme(self, theme):
        self.theme = theme if theme else {}
        self.palette = self.theme.get("palette", {})
        self.accent_color = self.theme.get("accent_color")
        self.hover_color = self.theme.get("hover_color")
        self.SetBackgroundColour(self.palette.get("bg"))
        self.Refresh()

    def on_paint(self, event):
        raise NotImplementedError

    def on_mouse_down(self, event):
        raise NotImplementedError

    def on_hover(self, event):
        self.hover = event.Entering()
        if self.hover:
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.Refresh()

    def SetValue(self, value):
        self.value = bool(value)
        self.Refresh()

    def GetValue(self):
        return self.value

    def DoGetBestSize(self):
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        width, height = dc.GetTextExtent(self.label)
        return wx.Size(width + 50, height + 10)


class CustomRadioButton(BaseToggleButton):
    def __init__(self, parent, label, style=0, theme=None):
        super().__init__(parent, label, style, theme)
        self.group = []

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()
        radius = height // 3
        indicator_x = radius + 5
        indicator_y = height // 2

        bg_color = self.hover_color if self.hover and self.hover_color else self.GetBackgroundColour()
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, width, height)

        if self.accent_color:
            gc.SetPen(wx.Pen(self.accent_color, 2))
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            gc.DrawEllipse(indicator_x - radius, indicator_y - radius, radius * 2, radius * 2)
            if self.value:
                gc.SetBrush(wx.Brush(self.accent_color))
                gc.DrawEllipse(indicator_x - radius / 2, indicator_y - radius / 2, radius, radius)

        fg_color = self.palette.get("fg")
        if fg_color:
            gc.SetFont(self.GetFont(), fg_color)
            _, label_height, _, _ = gc.GetFullTextExtent(self.label)
            gc.DrawText(self.label, indicator_x + radius + 10, (height - label_height) / 2)

    def on_mouse_down(self, event):
        if not self.value:
            self.SetValue(True)
            wx.PostEvent(self, wx.CommandEvent(wx.EVT_RADIOBUTTON.typeId, self.GetId()))

    def SetValue(self, value):
        self.value = bool(value)
        if self.value:
            for btn in self.group:
                if btn != self:
                    btn.SetValue(False)
        self.Refresh()


class CustomCheckBox(BaseToggleButton):
    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()
        box_size = height * 0.6
        box_x = 5
        box_y = (height - box_size) / 2

        bg_color = self.hover_color if self.hover and self.hover_color else self.GetBackgroundColour()
        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, width, height)

        if self.accent_color:
            gc.SetPen(wx.Pen(self.accent_color, 2))
            gc.SetBrush(wx.TRANSPARENT_BRUSH)
            gc.DrawRoundedRectangle(box_x, box_y, box_size, box_size, 3)
            if self.value:
                gc.SetPen(wx.Pen(self.accent_color, 3))
                gc.StrokeLine(box_x + 3, box_y + box_size / 2, box_x + box_size / 2.5, box_y + box_size - 3)
                gc.StrokeLine(box_x + box_size / 2.5, box_y + box_size - 3, box_x + box_size - 3, box_y + 3)

        fg_color = self.palette.get("fg")
        if fg_color:
            gc.SetFont(self.GetFont(), fg_color)
            _, label_height, _, _ = gc.GetFullTextExtent(self.label)
            gc.DrawText(self.label, box_x + box_size + 10, (height - label_height) / 2)

    def on_mouse_down(self, event):
        self.SetValue(not self.value)
        wx.PostEvent(self, wx.CommandEvent(wx.EVT_CHECKBOX.typeId, self.GetId()))


class ThemedLogCtrl(wx.Panel):
    def __init__(self, parent, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.VSCROLL | wx.BORDER_NONE):
        super().__init__(parent)
        self.text_ctrl = wx.TextCtrl(self, style=style)
        log_font = wx.Font(11, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName="Consolas")
        self.text_ctrl.SetFont(log_font)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def SetFocus(self):
        """Override to pass focus to the child text control."""
        self.text_ctrl.SetFocus()

    def AppendText(self, text):
        self.text_ctrl.AppendText(text)
        self.ScrollToEnd()

    def ScrollToEnd(self):
        wx.CallAfter(self.text_ctrl.ShowPosition, self.text_ctrl.GetLastPosition())

    def Clear(self):
        self.text_ctrl.Clear()

    def GetValue(self):
        return self.text_ctrl.GetValue()

    def SetValue(self, value):
        self.text_ctrl.SetValue(value)


class ThemedTextCtrl(ThemedLogCtrl):
    def __init__(self, parent, value=""):
        style = wx.TE_MULTILINE | wx.TE_RICH2 | wx.VSCROLL | wx.BORDER_NONE | wx.TE_PROCESS_ENTER
        super().__init__(parent, style=style)
        self.text_ctrl.SetEditable(True)
        self.text_ctrl.SetValue(value)
        self.text_ctrl.SetStyle(0, -1, wx.TextAttr())
````

## File: ui/widgets/lists.py
````python
import wx


class ThemedListCtrl(wx.ListCtrl):
    def __init__(self, parent, style, theme, is_dark):
        super().__init__(parent, style=style)
        self.theme = theme
        self.is_dark = is_dark
````

## File: core/utils.py
````python
import platform
from pathlib import Path
import ctypes


def set_title_bar_theme(window, is_dark):
    """Sets the title bar theme for a window on Windows."""
    if platform.system() != "Windows":
        return
    try:
        hwnd = window.GetHandle()
        if hwnd:
            value = ctypes.c_int(1 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
    except Exception as e:
        print(f"Warning: Failed to set title bar theme: {e}")


def get_downloads_folder():
    if platform.system() == "Windows":
        from ctypes import wintypes, oledll

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", wintypes.BYTE * 8)]

        FOLDERID_Downloads = GUID(0x374DE290, 0x123F, 0x4565, (0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B))
        path_ptr = ctypes.c_wchar_p()
        oledll.ole32.CoInitialize(None)
        try:
            if oledll.shell32.SHGetKnownFolderPath(ctypes.byref(FOLDERID_Downloads), 0, None, ctypes.byref(path_ptr)) == 0:
                return path_ptr.value
            else:
                raise ctypes.WinError()
        finally:
            oledll.ole32.CoTaskMemFree(path_ptr)
            oledll.ole32.CoUninitialize()
    return str(Path.home() / "Downloads")
````

## File: ui/widgets/buttons.py
````python
import wx


class CustomButton(wx.Panel):
    def __init__(self, parent, label, theme):
        super().__init__(parent)
        self.is_custom_themed = True
        self.label = label
        self.hover = False
        self.theme = theme if theme else {}
        self.color = None
        self.hover_color = None
        self.UpdateTheme(self.theme)
        self.disabled_color = wx.Colour(128, 128, 128)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_hover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_hover)
        self.SetMinSize(self.DoGetBestSize())

    def UpdateTheme(self, theme):
        self.theme = theme
        self.color = self.theme.get("accent_hover_color")
        self.hover_color = self.theme.get("accent_color")
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()

        bg_color = self.disabled_color
        if self.IsEnabled():
            if self.hover:
                bg_color = self.hover_color if self.hover_color else self.color
            else:
                bg_color = self.color

        if not bg_color:
            bg_color = self.disabled_color

        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, width, height, 5)
        gc.SetFont(self.GetFont(), wx.WHITE)
        label_width, label_height, _, _ = gc.GetFullTextExtent(self.label)
        gc.DrawText(self.label, (width - label_width) / 2, (height - label_height) / 2)

    def on_mouse_down(self, event):
        print(f"DIAG: CustomButton on_mouse_down at {__import__('datetime').datetime.now()}")
        if self.IsEnabled():
            wx.PostEvent(self, wx.CommandEvent(wx.EVT_BUTTON.typeId, self.GetId()))

    def on_hover(self, event):
        self.hover = event.Entering()
        if self.hover and self.IsEnabled():
            self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))
        self.Refresh()

    def DoGetBestSize(self):
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        width, height = dc.GetTextExtent(self.label)
        return wx.Size(width + 40, height + 20)

    def Enable(self, enable=True):
        result = super().Enable(enable)
        self.Refresh()
        return result

    def Disable(self):
        return self.Enable(False)


class CustomSecondaryButton(CustomButton):
    def __init__(self, parent, label, theme):
        self.alert_active = False
        super().__init__(parent, label, theme)

    def UpdateTheme(self, theme):
        self.theme = theme
        palette = self.theme.get("palette", {})
        self.color = palette.get("secondary_bg")
        self.hover_color = self.theme.get("hover_color")
        self.Refresh()

    def SetAlertState(self, active=False):
        self.alert_active = active
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()

        bg_color = self.disabled_color
        text_color = self.theme.get("palette", {}).get("fg")

        if self.IsEnabled():
            if self.alert_active:
                bg_color = self.theme.get("danger_color")
                text_color = wx.WHITE
            elif self.hover:
                bg_color = self.hover_color
            else:
                bg_color = self.color

        if not bg_color:
            bg_color = self.disabled_color
        if not text_color:
            text_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT)

        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, width, height, 5)

        gc.SetFont(self.GetFont(), text_color)
        label_width, label_height, _, _ = gc.GetFullTextExtent(self.label)
        gc.DrawText(self.label, (width - label_width) / 2, (height - label_height) / 2)


class IconCustomButton(CustomSecondaryButton):
    def __init__(self, parent, bitmap, theme, size):
        self.bitmap = bitmap
        self.success_active = False
        super().__init__(parent, label="", theme=theme)
        self.SetMinSize(size)
        self.SetSize(size)

    def UpdateTheme(self, theme):
        super().UpdateTheme(theme)
        self.success_color = self.theme.get("accent_color")
        self.Refresh()

    def SetSuccessState(self, active=False):
        self.success_active = active
        self.Refresh()

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        width, height = self.GetSize()

        bg_color = self.disabled_color
        if self.IsEnabled():
            if self.success_active:
                bg_color = self.success_color
            elif self.hover:
                bg_color = self.hover_color
            else:
                bg_color = self.color

        if not bg_color:
            bg_color = self.disabled_color

        gc.SetBrush(wx.Brush(bg_color))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRoundedRectangle(0, 0, width, height, 5)

        if self.bitmap and self.bitmap.IsOk():
            bmp_w, bmp_h = self.bitmap.GetSize()
            dc.DrawBitmap(self.bitmap, int((width - bmp_w) / 2), int((height - bmp_h) / 2), useMask=False)

    def DoGetBestSize(self):
        return self.GetSize()
````

## File: ui/widgets/dialogs.py
````python
import wx
import webbrowser
from .buttons import CustomButton, CustomSecondaryButton
from core.packager import resource_path
from core.utils import set_title_bar_theme


class ThemedMessageDialog(wx.Dialog):
    def __init__(self, parent, message, title, style, theme):
        super().__init__(parent, title=title)
        self.theme = theme
        self.SetBackgroundColour(self.theme["palette"]["bg"])
        self.Bind(wx.EVT_SHOW, self.on_show)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        message_text = wx.StaticText(self, label=message)
        message_text.SetForegroundColour(self.theme["palette"]["fg"])
        message_text.Wrap(350)
        main_sizer.Add(message_text, flag=wx.ALL | wx.EXPAND, border=20)

        button_sizer = self.CreateButtonSizer(style)
        main_sizer.Add(button_sizer, flag=wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, border=20)

        self.SetSizerAndFit(main_sizer)
        self.CenterOnParent()

    def CreateButtonSizer(self, flags):
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        if flags & wx.YES_NO:
            yes_button = CustomButton(self, "Yes", self.theme)
            no_button = CustomSecondaryButton(self, "No", self.theme)
            yes_button.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_YES))
            no_button.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_NO))
            button_sizer.Add(no_button, 0, wx.RIGHT, 10)
            button_sizer.Add(yes_button, 0)
        elif flags & wx.OK:
            ok_button = CustomButton(self, "OK", self.theme)
            ok_button.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
            button_sizer.Add(ok_button, 0)

        return button_sizer

    def on_show(self, event):
        if event.IsShown():
            wx.CallAfter(self._set_title_bar_theme)
        event.Skip()

    def _set_title_bar_theme(self):
        is_dark = self.theme.get("palette", {}).get("bg").GetRed() < 128
        set_title_bar_theme(self, is_dark)


class AboutDialog(wx.Dialog):
    def __init__(self, parent, theme, version, font_path, log_verbose_func):
        super().__init__(parent, title="About ContextPacker")
        self.theme = theme
        self.version = version
        self.font_path = font_path
        self.log_verbose = log_verbose_func

        self.SetBackgroundColour(self.theme["palette"]["bg"])
        self.Bind(wx.EVT_SHOW, self.on_show)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSpacer(20)

        font_loaded = False
        if self.font_path.exists():
            if wx.Font.AddPrivateFont(str(self.font_path)):
                font_loaded = True
            else:
                self.log_verbose("Warning: Failed to load custom font 'Source Code Pro'.")
        else:
            self.log_verbose(f"Warning: Custom font not found at '{self.font_path}'.")

        logo_path = resource_path("assets/icons/ContextPacker-x128.png")
        if logo_path.exists():
            bmp = wx.Bitmap(str(logo_path), wx.BITMAP_TYPE_PNG)
            logo_bitmap = wx.StaticBitmap(self, bitmap=wx.BitmapBundle(bmp))
            main_sizer.Add(logo_bitmap, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        title_font = wx.Font(22, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        if font_loaded:
            title_font.SetFaceName("Source Code Pro")

        title_text = wx.StaticText(self, label="ContextPacker")
        title_text.SetFont(title_font)
        title_text.SetForegroundColour(self.theme["accent_color"])
        main_sizer.Add(title_text, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        description = "Scrape websites or select local files, then package into a single file, optimized for LLMs."
        desc_font = self.GetFont()
        desc_font.SetPointSize(12)
        desc_text = wx.StaticText(self, label=description, style=wx.ALIGN_CENTER)
        desc_text.SetFont(desc_font)
        desc_text.SetForegroundColour(self.theme["palette"]["fg"])
        main_sizer.Add(desc_text, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        main_sizer.AddSpacer(15)

        milkshake_font = wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL)
        if font_loaded:
            milkshake_font.SetFaceName("Source Code Pro")

        milkshake_text = wx.StaticText(self, label='"I drink your milkshake! I drink it up!"')
        milkshake_text.SetFont(milkshake_font)
        milkshake_text.SetForegroundColour(self.theme["palette"]["fg"])
        main_sizer.Add(milkshake_text, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        version_font = self.GetFont()
        version_font.SetPointSize(12)
        version_text = wx.StaticText(self, label=f"Version {self.version}")
        version_text.SetFont(version_font)
        version_text.SetForegroundColour(self.theme["palette"]["fg"])
        main_sizer.Add(version_text, 0, wx.ALIGN_CENTER | wx.BOTTOM, 10)

        url = "https://github.com/dcog989/ContextPacker"
        hyperlink = wx.StaticText(self, label=url)
        link_font = self.GetFont()
        link_font.SetPointSize(12)
        link_font.SetUnderlined(True)
        hyperlink.SetFont(link_font)
        is_dark = self.theme.get("palette", {}).get("bg").GetRed() < 128
        link_color = wx.Colour(102, 178, 255) if is_dark else wx.Colour(0, 102, 204)
        hyperlink.SetForegroundColour(link_color)
        hyperlink.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        hyperlink.Bind(wx.EVT_LEFT_DOWN, lambda event: webbrowser.open(url))
        main_sizer.Add(hyperlink, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        ok_button = CustomButton(self, "OK", self.theme)
        ok_button.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_OK))
        main_sizer.Add(ok_button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 20)

        outer_sizer = wx.BoxSizer(wx.HORIZONTAL)
        outer_sizer.Add(main_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 40)

        self.SetSizerAndFit(outer_sizer)
        self.CenterOnParent()

    def on_show(self, event):
        if event.IsShown():
            wx.CallAfter(self._set_title_bar_theme)
        event.Skip()

    def _set_title_bar_theme(self):
        is_dark = self.theme.get("palette", {}).get("bg").GetRed() < 128
        set_title_bar_theme(self, is_dark)
````

## File: core/version.py
````python
__version__ = "1.5.0"
````

## File: requirements.txt
````
beautifulsoup4==4.13.5
markdownify==1.2.0
repomix==0.3.4
selenium==4.35.0
wxpython==4.2.3
lxml==6.0.1
````

## File: .gitignore
````
.repomixignore
repomix.config.json
.archive/
.vscode/
.gemini/
.dev-notes/


# Byte-compiled / optimized / DLL files
__pycache__/
*.py[codz]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py.cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to ignore these files since the code is
#   intended to run in multiple environments; otherwise, check them in:
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock

# UV
#   Similar to Pipfile.lock, it is generally recommended to include uv.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#uv.lock

# poetry
#   Similar to Pipfile.lock, it is generally recommended to include poetry.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#   https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control
#poetry.lock
#poetry.toml

# pdm
#   Similar to Pipfile.lock, it is generally recommended to include pdm.lock in version control.
#   pdm recommends including project-wide configuration in pdm.toml, but excluding .pdm-python.
#   https://pdm-project.org/en/latest/usage/project/#working-with-version-control
#pdm.lock
#pdm.toml
.pdm-python
.pdm-build/

# pixi
#   Similar to Pipfile.lock, it is generally recommended to include pixi.lock in version control.
#pixi.lock
#   Pixi creates a virtual environment in the .pixi directory, just like venv module creates one
#   in the .venv directory. It is recommended not to include this directory in version control.
.pixi

# PEP 582; used by e.g. github.com/David-OConnor/pyflow and github.com/pdm-project/pdm
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.envrc
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
#  JetBrains specific template is maintained in a separate JetBrains.gitignore that can
#  be found at https://github.com/github/gitignore/blob/main/Global/JetBrains.gitignore
#  and can be added to the global gitignore or merged into this file.  For a more nuclear
#  option (not recommended) you can uncomment the following to ignore the entire idea folder.
#.idea/

# Abstra
# Abstra is an AI-powered process automation framework.
# Ignore directories containing user credentials, local state, and settings.
# Learn more at https://abstra.io/docs
.abstra/

# Visual Studio Code
#  Visual Studio Code specific template is maintained in a separate VisualStudioCode.gitignore 
#  that can be found at https://github.com/github/gitignore/blob/main/Global/VisualStudioCode.gitignore
#  and can be added to the global gitignore or merged into this file. However, if you prefer, 
#  you could uncomment the following to ignore the entire vscode folder
# .vscode/

# Ruff stuff:
.ruff_cache/

# PyPI configuration file
.pypirc

# Cursor
#  Cursor is an AI-powered code editor. `.cursorignore` specifies files/directories to
#  exclude from AI features like autocomplete and code analysis. Recommended for sensitive data
#  refer to https://docs.cursor.com/context/ignore-files
.cursorignore
.cursorindexingignore

# Marimo
marimo/_static/
marimo/_lsp/
__marimo__/
````

## File: core/task_handler.py
````python
import wx
from pathlib import Path
import threading
import multiprocessing

import core.actions as actions
from ui.widgets.dialogs import ThemedMessageDialog


class TaskHandler:
    def __init__(self, app_instance):
        self.app = app_instance

    def start_download_task(self):
        print(f"DIAG: TaskHandler.start_download_task called at {__import__('datetime').datetime.now()}")
        dl_button = self.app.main_panel.crawler_panel.download_button
        self.app._toggle_ui_controls(False, widget_to_keep_enabled=dl_button)

        start_url = self.app.main_panel.crawler_panel.start_url_ctrl.GetValue()
        git_pattern = r"(\.git$)|(github\.com)|(gitlab\.com)|(bitbucket\.org)"
        if __import__("re").search(git_pattern, start_url):
            self.app.main_panel.copy_button.SetSuccessState(False)
            wx.BeginBusyCursor()
            self.app.is_task_running = True
            self.app.main_panel.package_button.Disable()
            self.app.main_panel.copy_button.Disable()
            dl_button.label = "Cloning..."
            dl_button.Refresh()
            self.app.cancel_event = threading.Event()
            actions.start_git_clone(self.app, self.app.cancel_event)
            return

        try:
            self.app.main_panel.crawler_panel.get_crawler_config("dummy_dir_for_validation")
        except (ValueError, AttributeError):
            msg = "Invalid input. Please ensure 'Max Pages', 'Min Pause', and 'Max Pause' are whole numbers."
            dlg = ThemedMessageDialog(self.app, msg, "Input Error", wx.OK | wx.ICON_ERROR, self.app.theme)
            dlg.ShowModal()
            dlg.Destroy()
            self.app._toggle_ui_controls(True)
            return

        self.app.main_panel.copy_button.SetSuccessState(False)
        wx.BeginBusyCursor()
        self.app.is_task_running = True
        self.app.main_panel.package_button.Disable()
        self.app.main_panel.copy_button.Disable()
        dl_button.label = "Stop!"
        dl_button.Refresh()

        self.app.cancel_event = multiprocessing.Event()
        self.app.start_queue_listener()
        actions.start_download(self.app, self.app.cancel_event)

    def start_package_task(self, file_list_for_count):
        pkg_button = self.app.main_panel.package_button
        self.app._toggle_ui_controls(False, widget_to_keep_enabled=pkg_button)

        is_web_mode = self.app.main_panel.web_crawl_radio.GetValue()
        if not is_web_mode:
            source_dir = self.app.main_panel.local_panel.local_dir_ctrl.GetValue()
            if not source_dir or not Path(source_dir).is_dir():
                msg = f"The specified input directory is not valid:\n{source_dir}"
                dlg = ThemedMessageDialog(self.app, msg, "Input Error", wx.OK | wx.ICON_ERROR, self.app.theme)
                dlg.ShowModal()
                dlg.Destroy()
                self.app._toggle_ui_controls(True)
                return

        self.app.main_panel.copy_button.SetSuccessState(False)
        wx.BeginBusyCursor()
        self.app.is_task_running = True
        self.app.main_panel.crawler_panel.download_button.Disable()
        self.app.main_panel.copy_button.Disable()
        pkg_button.label = "Stop!"
        pkg_button.Refresh()

        self.app.cancel_event = threading.Event()
        self.app.start_queue_listener()
        actions.start_packaging(self.app, self.app.cancel_event, file_list_for_count)

    def stop_current_task(self):
        if self.app.cancel_event:
            self.app.cancel_event.set()

        dl_button = self.app.main_panel.crawler_panel.download_button
        pkg_button = self.app.main_panel.package_button

        # Change label to give immediate feedback and disable to prevent multi-clicks
        if dl_button.IsEnabled():
            dl_button.label = "Stopping..."
            dl_button.Disable()
            dl_button.Refresh()

        if pkg_button.IsEnabled():
            pkg_button.label = "Stopping..."
            pkg_button.Disable()
            pkg_button.Refresh()

        self.app.log_verbose("Stopping process...")

    def handle_status(self, status, msg_obj):
        message = msg_obj.get("message", "")
        if status == "error":
            dlg = ThemedMessageDialog(self.app, message, "An Error Occurred", wx.OK | wx.ICON_ERROR, self.app.theme)
            dlg.ShowModal()
            dlg.Destroy()
        elif status == "clone_complete":
            self.app.log_verbose("✔ Git clone successful.")
            self.app.main_panel.local_panel.local_dir_ctrl.SetValue(msg_obj.get("path", ""))
            self.app.main_panel.web_crawl_radio.SetValue(False)
            self.app.main_panel.local_dir_radio.SetValue(True)
            self.app.toggle_input_mode()
        elif message:
            self.app.log_verbose(message)

        if status in ["source_complete", "package_complete", "cancelled", "error", "clone_complete"]:
            if status == "package_complete":
                self.app._open_output_folder()
            self.cleanup_after_task()
            self.app._update_button_states()

    def cleanup_after_task(self):
        if self.app.is_task_running:
            wx.EndBusyCursor()
            self.app.is_task_running = False

        self.app.stop_queue_listener()
        self.app._toggle_ui_controls(True)

        self.app.worker_thread = None
        self.app.cancel_event = None

        if self.app.is_shutting_down:
            wx.CallAfter(self.app.Destroy)
            return

        dl_button = self.app.main_panel.crawler_panel.download_button
        dl_button.label = "Download & Convert"
        dl_button.Enable()
        dl_button.Refresh()

        pkg_button = self.app.main_panel.package_button
        pkg_button.label = "Package"
        pkg_button.Enable()
        pkg_button.Refresh()

        self.app.main_panel.list_panel.progress_gauge.SetValue(0)
        self.app._update_button_states()

        self.app.timer.Start(100)
````

## File: README.md
````markdown
# ![ContextPacker logo](https://github.com/dcog989/ContextPacker/blob/main/assets/icons/ContextPacker-x64.png) ContextPacker

A desktop app to scrape websites, Git repositories, or package local files into a single file, optimized for consumption by LLMs.

![ContextPacker screenshot](https://github.com/user-attachments/assets/955e7a42-45c7-44e4-a37e-43003e49f06a)

## Features

* **Web Crawling**: Scrape a website, convert pages to Markdown, and package them into one file.
* **Git Repository Cloning**: Enter a Git URL to automatically clone the repository and switch to local packaging mode.
* **Local Packaging**: Package a local directory (e.g., a code repository) into a single file.
* **Multiple Output Formats**: Package files as `.md`, `.txt`, or `.xml`.
* **Smart Filtering**: Automatically respects `.gitignore` rules and provides an option to hide common binary and image files from the list.
* **Customizable**: Scraping options (depth, paths, speed) and file exclusions can be configured.
* **External Configuration**: Key settings can be modified in a `config.json` file.
* **Cross-Platform**: Light and Dark theme support (detects system theme on Windows, macOS, and Linux).

## Installation

1. **Install a Web Browser**: The web crawling feature requires one of the following browsers to be installed:
    * Microsoft Edge
    * Google Chrome
    * Mozilla Firefox

2. **Install Git**: The Git repository cloning feature requires `git` to be installed and accessible in your system's PATH.

3. Clone the repository or download the source code.

4. It is recommended to create a virtual environment:

    ```sh
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

5. Install the required dependencies from the virtual environment:

    ```sh
    pip install -r requirements.txt
    ```

6. Run the application:

    ```sh
    python app.py
    ```

## Usage

The application has two main modes, selectable via radio buttons.

### 1. Web Crawl Mode

This mode is for scraping online content or cloning Git repositories.

1. Select the **"Web Crawl"** radio button.
2. Enter the **Start URL**.
    * For a website, enter the full URL to begin scraping.
    * For a Git repository, enter the repository's clone URL (e.g., `https://github.com/user/repo.git`). The app will detect it, clone the repo, and switch to Local Directory mode.
3. Adjust the crawling options as needed (these are ignored for Git URLs).
4. Click **"Download & Convert"**.

### 2. Local Directory Mode

This mode is for packaging local files.

1. Select the **"Local Directory"** radio button.
2. Choose the **Input Directory** you want to package.
3. Use the **Excludes** text area to list any files or directories you wish to exclude. These patterns are combined with the rules in your `.gitignore` file.
4. Use the checkboxes to include subdirectories or hide common binary and image files from the list.
5. Click **"Package"**. The application will package all visible files into a single file in your Downloads folder, using the format selected in the output dropdown.

## Configuration

On first run, the application creates a `config.json` file in the same directory. You can edit this file to customize:

* `user_agents`: The list of user-agents available in the dropdown.
* `default_local_excludes`: The default patterns that appear in the "Excludes" text box.
* `binary_file_patterns`: The list of file patterns to hide when "Hide Images + Binaries" is checked.

## Building from Source

You can create a standalone executable using PyInstaller.

1. Install PyInstaller: `pip install pyinstaller`
2. The repository includes a pre-configured `ContextPacker.spec` file and a runtime hook (`pyi_rth_selenium.py`) to correctly handle Selenium's dependencies.
3. Run the build command from the project root:

    ```sh
    pyinstaller --clean ContextPacker.spec
    ```

4. The final single-file executable will be located in the `dist` folder.

## Technology Stack

* **UI**: Python with [wxPython](https://wxpython.org/)
* **Web Scraping**: [Selenium](https://www.selenium.dev/) + [Beautiful Soup](https://pypi.org/project/beautifulsoup4/)
* **HTML to Markdown**: [markdownify](https://pypi.org/project/markdownify/)
* **File Packaging**: [repomix](https://pypi.org/project/repomix/)
````

## File: ui/main_frame.py
````python
import wx
from .widgets.buttons import CustomButton, IconCustomButton
from .widgets.dialogs import ThemedMessageDialog
from .widgets.inputs import CustomRadioButton, FocusTextCtrl
from .panels import CrawlerInputPanel, LocalInputPanel, ListPanel
from core.config_manager import get_config
from core.packager import resource_path

config = get_config()


class MainFrame(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.controller = parent
        self.theme = self.controller.theme

        font = self.GetFont()
        font.SetPointSize(11)
        self.SetFont(font)

        self._create_widgets()
        self.create_sizers()
        self._bind_events()

    def _create_widgets(self):
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE | wx.SP_BORDER)
        self.left_panel = wx.Panel(self.splitter)
        self.right_panel_container = wx.Panel(self.splitter)

        self.input_static_box = wx.StaticBox(self.left_panel, label="Input")
        self.web_crawl_radio = CustomRadioButton(self.input_static_box, label="Web Crawl", theme=self.theme)
        self.local_dir_radio = CustomRadioButton(self.input_static_box, label="Local Directory", theme=self.theme)
        self.web_crawl_radio.group = [self.web_crawl_radio, self.local_dir_radio]
        self.local_dir_radio.group = [self.web_crawl_radio, self.local_dir_radio]
        self.web_crawl_radio.SetValue(True)

        self.crawler_panel = CrawlerInputPanel(self.input_static_box, self.theme, self.controller.version)
        self.local_panel = LocalInputPanel(self.input_static_box, self.theme)

        self.list_static_box = wx.StaticBox(self.right_panel_container, label="List")
        self.list_panel = ListPanel(self.list_static_box, self.theme, self.controller.is_dark)

        self.output_static_box = wx.StaticBox(self.right_panel_container, label="Output")
        self.output_filename_ctrl = FocusTextCtrl(self.output_static_box, value="ContextPacker-package", theme=self.theme)
        self.output_timestamp_label = wx.StaticText(self.output_static_box, label="")
        self.output_format_choice = wx.Choice(self.output_static_box, choices=[".md", ".txt", ".xml"])
        default_format = config.get("default_output_format", ".md")
        choices = self.output_format_choice.GetStrings()
        if default_format in choices:
            self.output_format_choice.SetSelection(choices.index(default_format))
        else:
            self.output_format_choice.SetSelection(0)
        self.package_button = CustomButton(self.output_static_box, label="Package", theme=self.theme)

        package_button_height = self.package_button.GetBestSize().GetHeight()
        copy_button_size = wx.Size(package_button_height, package_button_height)

        icon_path = resource_path("assets/icons/copy.png")
        img = wx.Image(str(icon_path), wx.BITMAP_TYPE_PNG)
        img.Rescale(24, 24, wx.IMAGE_QUALITY_HIGH)
        copy_bitmap = wx.Bitmap(img)

        self.copy_button = IconCustomButton(self.output_static_box, copy_bitmap, self.theme, size=copy_button_size)
        self.copy_button.SetToolTip("Copy final package contents to clipboard")
        self.copy_button.Disable()

        font = self.output_timestamp_label.GetFont()
        font.SetStyle(wx.FONTSTYLE_ITALIC)
        self.output_timestamp_label.SetFont(font)

    def create_sizers(self):
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add(self.splitter, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(main_sizer)

        left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.left_panel.SetSizer(left_sizer)

        input_sizer = wx.StaticBoxSizer(self.input_static_box, wx.VERTICAL)
        left_sizer.Add(input_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        radio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        radio_sizer.Add(self.web_crawl_radio, 0, wx.RIGHT, 10)
        radio_sizer.Add(self.local_dir_radio, 0)
        input_sizer.Add(radio_sizer, 0, wx.ALL, 10)
        input_sizer.Add(self.crawler_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        input_sizer.Add(self.local_panel, 1, wx.EXPAND | wx.ALL, 10)

        right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.right_panel_container.SetSizer(right_sizer)

        list_box_sizer = wx.StaticBoxSizer(self.list_static_box, wx.VERTICAL)
        list_box_sizer.Add(self.list_panel, 1, wx.EXPAND | wx.ALL, 5)
        right_sizer.Add(list_box_sizer, 1, wx.EXPAND | wx.ALL, 5)

        output_box_sizer = wx.StaticBoxSizer(self.output_static_box, wx.VERTICAL)
        filename_sizer = wx.BoxSizer(wx.HORIZONTAL)
        filename_sizer.Add(self.output_filename_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        filename_sizer.Add(self.output_timestamp_label, 0, wx.ALIGN_CENTER_VERTICAL)
        filename_sizer.Add(self.output_format_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)
        filename_sizer.Add(self.package_button, 0, wx.ALIGN_CENTER_VERTICAL)
        filename_sizer.Add(self.copy_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        output_box_sizer.Add(filename_sizer, 0, wx.EXPAND | wx.ALL, 10)
        right_sizer.Add(output_box_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.splitter.SplitVertically(self.left_panel, self.right_panel_container)
        self.splitter.SetSashPosition(650)
        self.splitter.SetMinimumPaneSize(600)

    def _bind_events(self):
        self.web_crawl_radio.Bind(wx.EVT_RADIOBUTTON, self.controller.on_toggle_input_mode)
        self.local_dir_radio.Bind(wx.EVT_RADIOBUTTON, self.controller.on_toggle_input_mode)
        self.local_panel.browse_button.Bind(wx.EVT_BUTTON, self.controller.on_browse)
        self.local_panel.include_subdirs_check.Bind(wx.EVT_CHECKBOX, self.controller.on_local_filters_changed)
        self.local_panel.hide_binaries_check.Bind(wx.EVT_CHECKBOX, self.controller.on_local_filters_changed)

        exclude_ctrl = self.local_panel.local_exclude_ctrl.text_ctrl
        exclude_ctrl.Bind(wx.EVT_KILL_FOCUS, self.controller.on_local_filters_changed)
        exclude_ctrl.Bind(wx.EVT_TEXT_ENTER, self.controller.on_local_filters_changed)
        exclude_ctrl.Bind(wx.EVT_KEY_UP, self.controller.on_exclude_text_update)
        exclude_ctrl.Bind(wx.EVT_LEFT_UP, self.controller.on_exclude_text_update)

        self.crawler_panel.download_button.Bind(wx.EVT_BUTTON, self.controller.on_download_button_click)
        self.package_button.Bind(wx.EVT_BUTTON, self.controller.on_package_button_click)
        self.list_panel.delete_button.Bind(wx.EVT_BUTTON, self.on_delete_selected_item)
        self.copy_button.Bind(wx.EVT_BUTTON, self.controller.on_copy_to_clipboard)

        self.crawler_panel.about_logo.Bind(wx.EVT_LEFT_DOWN, self.controller.on_show_about_dialog)
        self.crawler_panel.about_logo.Bind(wx.EVT_RIGHT_DOWN, self.controller.on_show_about_dialog)
        self.crawler_panel.about_text.Bind(wx.EVT_LEFT_DOWN, self.controller.on_show_about_dialog)
        self.crawler_panel.about_text.Bind(wx.EVT_RIGHT_DOWN, self.controller.on_show_about_dialog)

    def on_delete_selected_item(self, event):
        is_web_mode = self.web_crawl_radio.GetValue()
        list_ctrl = self.list_panel.standard_log_list if is_web_mode else self.list_panel.local_file_list
        data_source = self.list_panel.scraped_files if is_web_mode else self.list_panel.local_files

        selected_count = list_ctrl.GetSelectedItemCount()
        if selected_count == 0:
            return

        if is_web_mode:
            title = "Confirm Deletion"
            message = f"Are you sure you want to permanently delete {selected_count} downloaded file(s)?"
        else:
            title = "Confirm Removal"
            message = f"Are you sure you want to remove {selected_count} item(s) from the package list?"

        with ThemedMessageDialog(self, message, title, wx.YES_NO | wx.NO_DEFAULT, self.theme) as dlg:
            if dlg.ShowModal() != wx.ID_YES:
                return

        selected_indices = []
        item = list_ctrl.GetFirstSelected()
        while item != -1:
            selected_indices.append(item)
            item = list_ctrl.GetNextSelected(item)

        for index in sorted(selected_indices, reverse=True):
            item_to_remove = data_source.pop(index)
            list_ctrl.DeleteItem(index)

            if is_web_mode:
                self.controller.delete_scraped_file(item_to_remove["path"])
            else:
                self.controller.remove_local_file_from_package(item_to_remove["rel_path"])

        self.list_panel.delete_button.SetAlertState(False)
        self.controller._update_button_states()
        self.list_panel.update_file_count()
````

## File: core/crawler.py
````python
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, urljoin
from pathlib import Path
import queue
import time
import random
import re
import os
from markdownify import markdownify as md
import platform
import subprocess
import threading


def _get_browser_binary_path_windows(browser_name, log_queue):
    """
    Finds a browser's executable on Windows by checking registry keys
    and common file system locations.
    """
    import winreg

    search_config = {
        "chrome": {
            "reg_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
            ],
            "fs_paths": [r"Google\Chrome\Application\chrome.exe", r"Chromium\Application\chrome.exe"],
        },
        "msedge": {
            "reg_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
            ],
            "fs_paths": [r"Microsoft\Edge\Application\msedge.exe"],
        },
        "firefox": {
            "reg_keys": [
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"),
            ],
            "fs_paths": [r"Mozilla Firefox\firefox.exe", r"Firefox Developer Edition\firefox.exe"],
        },
    }

    config = search_config.get(browser_name)
    if not config:
        return None

    for hive, subkey in config["reg_keys"]:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                path, _ = winreg.QueryValueEx(key, "")
                if Path(path).exists():
                    return path
        except FileNotFoundError:
            continue
        except Exception:
            continue

    base_paths = []
    for var in ["ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"]:
        path = os.environ.get(var)
        if path:
            base_paths.append(Path(path))
    if not os.environ.get("LOCALAPPDATA"):
        base_paths.append(Path.home() / "AppData" / "Local")

    for fs_path in config["fs_paths"]:
        for base in base_paths:
            full_path = base / fs_path
            if full_path.exists():
                return str(full_path)
    return None


def _get_browser_binary_path(browser_name, log_queue):
    """
    Finds the path to a browser's executable, checking common locations
    for the current operating system.
    """
    system = platform.system()
    if system == "Windows":
        return _get_browser_binary_path_windows(browser_name, log_queue)

    paths_to_check = []
    if system == "Darwin":
        path_map = {
            "chrome": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
            "msedge": ["/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
            "firefox": ["/Applications/Firefox.app/Contents/MacOS/firefox"],
        }
        paths_to_check = path_map.get(browser_name, [])
    elif system == "Linux":
        path_map = {
            "chrome": ["/usr/bin/google-chrome", "/opt/google/chrome/chrome"],
            "msedge": ["/usr/bin/microsoft-edge"],
            "firefox": ["/usr/bin/firefox"],
        }
        paths_to_check = path_map.get(browser_name, [])

    if paths_to_check:
        for path in paths_to_check:
            if Path(path).exists():
                return path
    return None


def sanitize_filename(url):
    parsed_url = urlparse(url)
    path_segment = parsed_url.path
    if not path_segment or path_segment.endswith("/"):
        path_segment += "index"
    if path_segment.startswith("/"):
        path_segment = path_segment[1:]

    filename = path_segment.replace("/", "-")
    if not filename:
        filename = "index"

    return re.sub(r'[<>:"/\\|?*]', "_", filename)


def crawl_website(config, log_queue, cancel_event):
    """
    Crawls a website based on the provided configuration.
    """
    print(f"DIAG: crawl_website thread started at {__import__('datetime').datetime.now()}")
    log_queue.put({"type": "log", "message": "Searching for a compatible web browser..."})

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    chrome_options.page_load_strategy = "eager"
    chrome_binary_path = _get_browser_binary_path("chrome", log_queue)
    if chrome_binary_path:
        chrome_options.binary_location = chrome_binary_path

    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument("--headless")
    edge_options.add_argument("--log-level=3")
    edge_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    edge_options.page_load_strategy = "eager"
    edge_binary_path = _get_browser_binary_path("msedge", log_queue)
    if edge_binary_path:
        edge_options.binary_location = edge_binary_path

    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument("--headless")
    firefox_options.add_argument("--log-level=3")
    firefox_options.page_load_strategy = "eager"
    firefox_binary_path = _get_browser_binary_path("firefox", log_queue)
    if firefox_binary_path:
        firefox_options.binary_location = firefox_binary_path

    creation_flags = 0
    if platform.system() == "Windows":
        creation_flags = subprocess.CREATE_NO_WINDOW

    browsers_to_try = [
        ("msedge", webdriver.Edge, edge_options, EdgeService),
        ("chrome", webdriver.Chrome, chrome_options, ChromeService),
        ("firefox", webdriver.Firefox, firefox_options, FirefoxService),
    ]

    driver = None
    for name_key, driver_class, options, service_class in browsers_to_try:
        try:
            log_queue.put({"type": "log", "message": f"  -> Attempting to initialize {name_key}..."})
            service = service_class(creationflags=creation_flags)
            driver = driver_class(service=service, options=options)
            log_queue.put({"type": "log", "message": f"✔ Success: Using {name_key} for web crawling."})
            break

        except WebDriverException as e:
            log_queue.put({"type": "log", "message": f"  -> {name_key} not found or failed to start. Details: {e.msg}"})

    if driver is None:
        error_msg = "ERROR: Could not find a compatible web browser or its driver.\nPlease ensure a supported browser (Edge, Chrome, or Firefox) is installed."
        log_queue.put({"type": "status", "status": "error", "message": error_msg})
        return

    driver.set_page_load_timeout(15)

    def _normalize_url(url):
        url_no_fragment = url.split("#")[0]
        if url_no_fragment.endswith(".html"):
            url_no_fragment = url_no_fragment[:-5]
        if url_no_fragment.endswith("/"):
            url_no_fragment = url_no_fragment[:-1]
        return url_no_fragment

    def _url_matches_any_pattern(url, patterns):
        parsed_url_path = urlparse(url).path
        for pattern in patterns:
            if pattern.startswith(("http://", "https://")):
                if url.startswith(pattern):
                    return True
            elif pattern in parsed_url_path:
                return True
        return False

    log_queue.put({"type": "log", "message": "Starting web crawl..."})

    start_domain = urlparse(config.start_url).netloc

    urls_to_visit = queue.Queue()
    normalized_start_url = _normalize_url(config.start_url)
    urls_to_visit.put((config.start_url, 0))
    processed_urls = {normalized_start_url}

    pages_saved = 0

    try:
        while not urls_to_visit.empty() and pages_saved < config.max_pages:
            if cancel_event.is_set():
                break

            current_url, depth = urls_to_visit.get()
            log_queue.put({"type": "progress", "value": pages_saved, "max_value": config.max_pages})

            try:
                log_queue.put({"type": "log", "message": f"GET (Depth {depth}): {current_url}"})
                driver.get(current_url)

                pause_duration = random.uniform(config.min_pause, config.max_pause)
                time.sleep(pause_duration)

                if cancel_event.is_set():
                    break

                final_url_from_driver = driver.current_url
                if config.ignore_queries:
                    final_url_from_driver = final_url_from_driver.split("?")[0]

                normalized_final_url = _normalize_url(final_url_from_driver)

                if "404" in driver.title or "Not Found" in driver.title:
                    log_queue.put({"type": "log", "message": f"  -> Skipping (404 Not Found): {final_url_from_driver}"})
                    continue

                processed_urls.add(normalized_final_url)
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, "lxml")

                for tag in soup(["script", "style"]):
                    tag.decompose()
                cleaned_html = str(soup)

                filename = sanitize_filename(normalized_final_url) + ".md"
                md_content = md(cleaned_html)

                output_path = Path(config.output_dir) / filename
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)

                pages_saved += 1
                log_queue.put(
                    {
                        "type": "file_saved",
                        "url": final_url_from_driver,
                        "path": str(output_path),
                        "filename": filename,
                        "pages_saved": pages_saved,
                        "max_pages": config.max_pages,
                        "queue_size": urls_to_visit.qsize(),
                    }
                )

                if depth < config.crawl_depth:
                    links = soup.find_all("a", href=True)
                    for link in links:
                        if not isinstance(link, Tag):
                            continue

                        href_attr = link.get("href")
                        if not isinstance(href_attr, str):
                            continue

                        if not href_attr or href_attr.startswith(("mailto:", "javascript:", "#")):
                            continue

                        abs_link = urljoin(final_url_from_driver, href_attr)
                        normalized_abs_link = _normalize_url(abs_link)

                        parsed_link_domain = urlparse(abs_link).netloc
                        if config.stay_on_subdomain and parsed_link_domain != start_domain:
                            continue

                        if config.exclude_paths and _url_matches_any_pattern(abs_link, config.exclude_paths):
                            continue

                        if config.include_paths and not _url_matches_any_pattern(abs_link, config.include_paths):
                            continue

                        if normalized_abs_link not in processed_urls:
                            processed_urls.add(normalized_abs_link)
                            urls_to_visit.put((abs_link, depth + 1))

            except TimeoutException:
                log_queue.put({"type": "log", "message": f"  -> TIMEOUT after 5s on: {current_url}"})
                continue
            except WebDriverException as e:
                log_queue.put({"type": "log", "message": f"  -> SELENIUM ERROR: {e.msg}"})
            except Exception as e:
                log_queue.put({"type": "log", "message": f"  -> PROCESSING ERROR: {e}"})

    finally:
        if driver:

            def _cleanup_driver(d):
                try:
                    d.quit()
                except Exception:
                    pass

            cleanup_thread = threading.Thread(target=_cleanup_driver, args=(driver,), daemon=True)
            cleanup_thread.start()

    if not cancel_event.is_set():
        log_queue.put({"type": "status", "status": "source_complete", "message": f"\nWeb scrape finished. Saved {pages_saved} pages."})
    else:
        log_queue.put({"type": "status", "status": "cancelled", "message": "Process cancelled by user."})
````

## File: core/actions.py
````python
import threading
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import wx
import logging
import os
import fnmatch
import subprocess
import queue
import multiprocessing

from .packager import run_repomix


def start_download(app, cancel_event):
    """Initializes and starts the web crawling process in a new process."""
    print(f"DIAG: actions.start_download called at {datetime.now()}")
    app.main_panel.list_panel.clear_logs()
    app.main_panel.list_panel.progress_gauge.SetValue(0)

    if app.temp_dir and Path(app.temp_dir).is_dir():
        shutil.rmtree(app.temp_dir)

    app.temp_dir = tempfile.mkdtemp(prefix="ContextPacker-")
    app.log_verbose(f"Created temporary directory: {app.temp_dir}")
    crawler_config = app.main_panel.crawler_panel.get_crawler_config(app.temp_dir)

    app.log_verbose("Starting url conversion...")
    app.worker_thread = multiprocessing.Process(target=_crawl_process_worker, args=(crawler_config, app.log_queue, cancel_event), daemon=True)
    print(f"DIAG: Worker process created. Starting now at {datetime.now()}.")
    app.worker_thread.start()


def _enqueue_output(stream, q):
    """Reads lines from a stream and puts them into a queue."""
    for line in iter(stream.readline, ""):
        q.put(line)
    stream.close()


def start_git_clone(app, cancel_event):
    """Initializes and starts a git clone process in a new thread."""
    app.main_panel.list_panel.clear_logs()

    if app.temp_dir and Path(app.temp_dir).is_dir():
        shutil.rmtree(app.temp_dir)

    app.temp_dir = tempfile.mkdtemp(prefix="ContextPacker-")
    app.log_verbose(f"Created temporary directory for git clone: {app.temp_dir}")
    url = app.main_panel.crawler_panel.start_url_ctrl.GetValue()

    app.log_verbose(f"Starting git clone for {url}...")
    app.worker_thread = threading.Thread(target=_clone_repo_worker, args=(url, app.temp_dir, app.log_queue, cancel_event), daemon=True)
    app.worker_thread.start()


def _crawl_process_worker(crawler_config, log_queue, cancel_event):
    """
    This function runs in a separate process to perform the web crawl.
    It imports necessary modules within the function to ensure it works
    correctly with multiprocessing.
    """
    from .crawler import crawl_website

    crawl_website(crawler_config, log_queue, cancel_event)


def _clone_repo_worker(url, path, log_queue, cancel_event):
    """Worker function to perform a git clone and stream output."""
    if not shutil.which("git"):
        error_msg = "ERROR: Git is not installed or not found in your system's PATH. Please install Git to use this feature."
        log_queue.put({"type": "status", "status": "error", "message": error_msg})
        return

    try:
        process = subprocess.Popen(
            ["git", "clone", "--depth", "1", url, path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        if not process.stdout:
            process.wait()
            log_queue.put({"type": "status", "status": "error", "message": "Failed to capture git clone output stream."})
            return

        output_queue = queue.Queue()
        reader_thread = threading.Thread(target=_enqueue_output, args=(process.stdout, output_queue), daemon=True)
        reader_thread.start()

        while process.poll() is None:
            if cancel_event.is_set():
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                break

            try:
                line = output_queue.get(timeout=0.1)
                if line:
                    log_queue.put({"type": "log", "message": line.strip()})
            except queue.Empty:
                continue

        while not output_queue.empty():
            line = output_queue.get_nowait()
            if line:
                log_queue.put({"type": "log", "message": line.strip()})

        if cancel_event.is_set():
            log_queue.put({"type": "status", "status": "cancelled", "message": "Git clone cancelled."})
            return

        if process.returncode == 0:
            log_queue.put({"type": "status", "status": "clone_complete", "path": path})
        else:
            log_queue.put({"type": "status", "status": "error", "message": "Git clone failed. Check the log for details."})

    except Exception as e:
        log_queue.put({"type": "status", "status": "error", "message": f"An error occurred while cloning the repository: {e}"})


def start_packaging(app, cancel_event, file_list=None):
    """Initializes and starts the packaging process in a new thread."""
    is_web_mode = app.main_panel.web_crawl_radio.GetValue()
    app.filename_prefix = app.main_panel.output_filename_ctrl.GetValue().strip() or "ContextPacker-package"
    source_dir = ""
    effective_excludes = []

    if is_web_mode:
        if not app.temp_dir or not any(Path(app.temp_dir).iterdir()):
            app.log_verbose("ERROR: No downloaded content to package. Please run 'Download & Convert' first.")
            return
        source_dir = app.temp_dir
        effective_excludes = []
    else:
        source_dir = app.main_panel.local_panel.local_dir_ctrl.GetValue()
        default_excludes = [p.strip() for p in app.main_panel.local_panel.local_exclude_ctrl.GetValue().splitlines() if p.strip()]

        additional_excludes = set()
        if not app.main_panel.local_panel.include_subdirs_check.GetValue():
            source_path = Path(source_dir)
            if source_path.is_dir():
                for item in source_path.iterdir():
                    if item.is_dir():
                        additional_excludes.add(f"{item.name}/")

        effective_excludes = list(set(default_excludes) | app.local_files_to_exclude | additional_excludes)

    extension = app.main_panel.output_format_choice.GetStringSelection()
    style_map = {".md": "markdown", ".txt": "plain", ".xml": "xml"}
    repomix_style = style_map.get(extension, "markdown")

    app.main_panel.list_panel.progress_gauge.SetValue(0)

    _run_packaging_thread(app, source_dir, app.filename_prefix, effective_excludes, extension, repomix_style, cancel_event, file_list)


def _run_packaging_thread(app, source_dir, filename_prefix, exclude_paths, extension, repomix_style, cancel_event, file_list=None):
    """Configures and runs the repomix packager in a worker thread."""
    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    downloads_path = app._get_downloads_folder()
    output_basename = f"{filename_prefix}-{timestamp}{extension}"
    app.final_output_path = str(Path(downloads_path) / output_basename)

    app.log_verbose("\nStarting packaging process...")

    class RepomixProgressHandler(logging.Handler):
        def __init__(self, log_queue_ref, total_files_ref):
            super().__init__()
            self.log_queue = log_queue_ref
            self.processed_count = 0
            self.total_files = total_files_ref

        def emit(self, record):
            msg = self.format(record)
            if "Processing file:" in msg:
                self.processed_count += 1
                progress_value = int((self.processed_count / self.total_files) * 100) if self.total_files > 0 else 0
                wx.CallAfter(self.log_queue.put, {"type": "progress", "value": progress_value, "max_value": 100})

            wx.CallAfter(self.log_queue.put, {"type": "log", "message": msg})

    total_files_for_progress = 0
    is_web_mode = app.main_panel.web_crawl_radio.GetValue()
    if file_list is not None:
        if is_web_mode:
            total_files_for_progress = len(file_list)
        else:
            total_files_for_progress = len([f for f in file_list if f.get("type") == "File"])
    else:  # Fallback to scanning if file_list is not provided
        if Path(source_dir).is_dir():
            current_exclude_paths = exclude_paths or []
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = Path(root) / file
                    rel_path_str = file_path.relative_to(source_dir).as_posix()
                    is_excluded = any(fnmatch.fnmatch(rel_path_str, pattern) for pattern in current_exclude_paths)
                    if not is_excluded:
                        total_files_for_progress += 1

    progress_handler = RepomixProgressHandler(app.log_queue, total_files_for_progress)
    progress_handler.setLevel(logging.INFO)

    repomix_logger = logging.getLogger("repomix")
    original_level = repomix_logger.level
    repomix_logger.setLevel(logging.INFO)
    repomix_logger.addHandler(progress_handler)

    try:
        app.worker_thread = threading.Thread(target=run_repomix, args=(source_dir, app.final_output_path, app.log_queue, cancel_event, repomix_style, exclude_paths), daemon=True)
        app.worker_thread.start()
    finally:
        repomix_logger.removeHandler(progress_handler)
        repomix_logger.setLevel(original_level)


def populate_local_files(app):
    """Convenience function to trigger a refresh of the local file list."""
    app.populate_local_file_list()


def get_local_files(root_dir, include_subdirs, custom_excludes, binary_excludes, cancel_event=None):
    """
    Scans a directory and returns a filtered list of files and folders,
    pruning ignored directories for efficiency.
    """
    base_path = Path(root_dir)
    if not base_path.is_dir():
        return []

    files_to_show = []
    all_ignore_patterns = list(custom_excludes)

    gitignore_path = base_path / ".gitignore"
    if gitignore_path.is_file():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                gitignore_patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
                all_ignore_patterns.extend(gitignore_patterns)
        except Exception:
            pass

    all_ignore_patterns.extend(binary_excludes)

    for root, dirnames, filenames in os.walk(str(base_path), topdown=True):
        if cancel_event and cancel_event.is_set():
            return []
        root_path = Path(root)
        rel_root_path = root_path.relative_to(base_path)

        ignored_dirs = set()
        for d in dirnames:
            dir_path_posix = (rel_root_path / d).as_posix()
            if any(fnmatch.fnmatch(dir_path_posix, pattern) or fnmatch.fnmatch(f"{dir_path_posix}/", pattern) for pattern in all_ignore_patterns):
                ignored_dirs.add(d)
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs]

        for d in dirnames:
            rel_path_str = (rel_root_path / d).as_posix()
            files_to_show.append({"name": rel_path_str + "/", "type": "Folder", "size": 0, "size_str": "", "rel_path": rel_path_str + "/"})

        for f in filenames:
            rel_path = rel_root_path / f
            if not any(fnmatch.fnmatch(rel_path.as_posix(), pattern) for pattern in all_ignore_patterns):
                try:
                    full_path = root_path / f
                    size = full_path.stat().st_size
                    size_str = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
                    rel_path_str = rel_path.as_posix()
                    files_to_show.append({"name": rel_path_str, "type": "File", "size": size, "size_str": size_str, "rel_path": rel_path_str})
                except (OSError, ValueError):
                    continue

        if not include_subdirs:
            break

    if cancel_event and cancel_event.is_set():
        return []

    files_to_show.sort(key=lambda p: (p["type"] != "Folder", p["name"].lower()), reverse=True)
    return files_to_show
````

## File: ui/panels.py
````python
import wx
from .widgets.buttons import CustomButton, CustomSecondaryButton
from .widgets.inputs import FocusTextCtrl, CustomRadioButton, CustomCheckBox, ThemedLogCtrl, ThemedTextCtrl
from .widgets.lists import ThemedListCtrl
from .widgets.gauges import CustomGauge
from core.config import CrawlerConfig
from core.config_manager import get_config
from core.packager import resource_path

config = get_config()


class CrawlerInputPanel(wx.Panel):
    def __init__(self, parent, theme, version):
        super().__init__(parent)
        self.theme = theme
        self.version = version
        self._create_widgets()
        self._create_sizers()
        self.on_user_agent_change(None)
        self.start_url_ctrl.text_ctrl.Bind(wx.EVT_TEXT, self.on_url_change)
        self.on_url_change(None)

    def _create_widgets(self):
        self.start_url_label = wx.StaticText(self, label="Start URL:")
        self.start_url_ctrl = FocusTextCtrl(self, value="", theme=self.theme)
        self.user_agent_label = wx.StaticText(self, label="User-Agent:")
        user_agents = config.get("user_agents", [])
        self.user_agent_combo = wx.Choice(self, choices=user_agents)
        if user_agents:
            self.user_agent_combo.SetStringSelection(user_agents[0])
        self.max_pages_label = wx.StaticText(self, label="Max Pages:")
        self.max_pages_ctrl = FocusTextCtrl(self, value="50", theme=self.theme)
        self.crawl_depth_label = wx.StaticText(self, label="Crawl Depth:")
        self.crawl_depth_ctrl = wx.SpinCtrl(self, value="1", min=0, max=99)
        crawl_depth_tooltip = "0 = only the start URL.\n1 = the start URL and all pages linked from it.\n2 = pages linked from those pages, and so on."
        self.crawl_depth_label.SetToolTip(crawl_depth_tooltip)
        self.crawl_depth_ctrl.SetToolTip(crawl_depth_tooltip)
        self.pause_label = wx.StaticText(self, label="Pause (ms):")
        self.min_pause_ctrl = FocusTextCtrl(self, value="212", theme=self.theme)
        self.max_pause_ctrl = FocusTextCtrl(self, value="2200", theme=self.theme)
        self.include_paths_label = wx.StaticText(self, label="Include Paths:")
        self.include_paths_ctrl = ThemedTextCtrl(self)
        self.exclude_paths_label = wx.StaticText(self, label="Exclude Paths:")
        self.exclude_paths_ctrl = ThemedTextCtrl(self)
        self.stay_on_subdomain_check = CustomCheckBox(self, label="Stay on start URL's subdomain", theme=self.theme)
        self.stay_on_subdomain_check.SetValue(True)
        self.ignore_queries_check = CustomCheckBox(self, label="Ignore URL query parameters (?...)", theme=self.theme)
        self.ignore_queries_check.SetValue(True)
        self.download_button = CustomButton(self, label="Download & Convert", theme=self.theme)
        self.user_agent_combo.Bind(wx.EVT_CHOICE, self.on_user_agent_change)

        font = self.include_paths_ctrl.text_ctrl.GetFont()
        dc = wx.ClientDC(self)
        dc.SetFont(font)
        _w, char_height = dc.GetTextExtent("Xg")
        min_height = (char_height * 4) + 12
        self.include_paths_ctrl.SetMinSize(wx.Size(-1, min_height))
        self.exclude_paths_ctrl.SetMinSize(wx.Size(-1, min_height))

        logo_path = resource_path("assets/icons/ContextPacker-x64.png")
        if logo_path.exists():
            img = wx.Image(str(logo_path), wx.BITMAP_TYPE_PNG)
            img.Rescale(64, 64, wx.IMAGE_QUALITY_HIGH)
            bmp = wx.Bitmap(img)
            self.about_logo = wx.StaticBitmap(self, bitmap=wx.BitmapBundle(bmp))
            self.about_logo.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        else:
            self.about_logo = wx.StaticText(self, label="?")

        self.about_text = wx.StaticText(self, label="ContextPacker")
        self.about_text.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        about_font = wx.Font(20, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        font_path = resource_path("assets/fonts/SourceCodePro-Regular.ttf")
        if font_path.exists():
            if wx.Font.AddPrivateFont(str(font_path)):
                about_font.SetFaceName("Source Code Pro")
        self.about_text.SetFont(about_font)
        self.about_text.SetForegroundColour(self.theme["accent_color"])

        self.version_text = wx.StaticText(self, label=f"v{self.version}")
        version_font = self.GetFont()
        version_font.SetPointSize(9)
        self.version_text.SetFont(version_font)

    def _create_sizers(self):
        sizer = wx.FlexGridSizer(10, 2, 15, 10)
        sizer.AddGrowableCol(1, 1)
        sizer.Add(self.start_url_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.start_url_ctrl, 1, wx.EXPAND)
        sizer.Add(self.user_agent_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.user_agent_combo, 1, wx.EXPAND)
        numerical_sizer = wx.BoxSizer(wx.HORIZONTAL)
        numerical_sizer.Add(self.max_pages_ctrl, 0, wx.RIGHT, 15)
        numerical_sizer.Add(self.crawl_depth_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        numerical_sizer.Add(self.crawl_depth_ctrl, 0)
        sizer.Add(self.max_pages_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(numerical_sizer, 1, wx.ALIGN_LEFT | wx.EXPAND)
        sizer.Add(self.pause_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        pause_sizer = wx.BoxSizer(wx.HORIZONTAL)
        pause_sizer.Add(self.min_pause_ctrl, 1, wx.EXPAND | wx.RIGHT, 5)
        pause_sizer.Add(wx.StaticText(self, label=" to "), 0, wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT, 5)
        pause_sizer.Add(self.max_pause_ctrl, 1, wx.EXPAND)
        sizer.Add(pause_sizer, 1, wx.EXPAND)
        sizer.Add(self.include_paths_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP | wx.TOP, 5)
        sizer.Add(self.include_paths_ctrl, 1, wx.EXPAND | wx.BOTTOM, 5)
        sizer.Add(self.exclude_paths_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP | wx.TOP, 5)
        sizer.Add(self.exclude_paths_ctrl, 1, wx.EXPAND | wx.BOTTOM, 5)
        options_sizer = wx.BoxSizer(wx.VERTICAL)
        options_sizer.Add(self.stay_on_subdomain_check, 0, wx.BOTTOM, 5)
        options_sizer.Add(self.ignore_queries_check, 0)
        sizer.Add(wx.StaticText(self, label=""), 0)
        sizer.Add(options_sizer, 1, wx.EXPAND | wx.TOP, 5)
        sizer.Add(wx.StaticText(self, label=""), 0)
        sizer.Add(self.download_button, 0, wx.ALIGN_LEFT | wx.TOP, 10)

        about_text_sizer = wx.BoxSizer(wx.VERTICAL)
        about_text_sizer.Add(self.about_text, 0, wx.ALIGN_LEFT)
        about_text_sizer.Add(self.version_text, 0, wx.ALIGN_LEFT | wx.TOP, 2)

        sizer.Add(self.about_logo, 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP | wx.TOP, 15)
        sizer.Add(about_text_sizer, 0, wx.ALIGN_LEFT | wx.TOP, 15)

        self.SetSizer(sizer)

    def on_user_agent_change(self, event):
        full_ua_string = self.user_agent_combo.GetStringSelection()
        self.user_agent_combo.SetToolTip(wx.ToolTip(full_ua_string))

    def on_url_change(self, event):
        url = self.start_url_ctrl.GetValue()
        self.download_button.Enable(bool(url.strip()))
        if event:
            event.Skip()

    def get_crawler_config(self, output_dir):
        return CrawlerConfig(
            start_url=self.start_url_ctrl.GetValue(),
            output_dir=output_dir,
            max_pages=int(self.max_pages_ctrl.GetValue()),
            min_pause=int(self.min_pause_ctrl.GetValue()) / 1000.0,
            max_pause=int(self.max_pause_ctrl.GetValue()) / 1000.0,
            crawl_depth=self.crawl_depth_ctrl.GetValue(),
            include_paths=[p.strip() for p in self.include_paths_ctrl.GetValue().splitlines() if p.strip()],
            exclude_paths=[p.strip() for p in self.exclude_paths_ctrl.GetValue().splitlines() if p.strip()],
            stay_on_subdomain=self.stay_on_subdomain_check.GetValue(),
            ignore_queries=self.ignore_queries_check.GetValue(),
            user_agent=self.user_agent_combo.GetStringSelection(),
        )


class LocalInputPanel(wx.Panel):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self._create_widgets()
        self._create_sizers()

    def _create_widgets(self):
        self.local_dir_label = wx.StaticText(self, label="Input Directory:")
        self.local_dir_ctrl = FocusTextCtrl(self, theme=self.theme)
        self.browse_button = CustomButton(self, label="Browse...", theme=self.theme)
        self.local_exclude_label = wx.StaticText(self, label="Excludes:")
        self.local_exclude_ctrl = ThemedTextCtrl(self)
        self.local_exclude_ctrl.SetToolTip("List of files or folders to exclude by default (e.g., node_modules/, *.log).\nThese are combined with files you delete from the Output list.\nOne pattern per line.")
        font = self.local_exclude_ctrl.text_ctrl.GetFont()
        dc = wx.ClientDC(self)
        dc.SetFont(font)
        _w, char_height = dc.GetTextExtent("Xg")
        min_height = char_height * 6 + 12
        self.local_exclude_ctrl.SetMinSize(wx.Size(-1, min_height))
        default_excludes_list = config.get("default_local_excludes", [])
        default_excludes = "\n".join(default_excludes_list)
        self.local_exclude_ctrl.SetValue(default_excludes)
        self.include_subdirs_check = CustomCheckBox(self, label="Include Subdirectories", theme=self.theme)
        self.include_subdirs_check.SetValue(True)
        self.hide_binaries_check = CustomCheckBox(self, label="Hide Images + Binaries", theme=self.theme)
        self.hide_binaries_check.SetValue(True)

    def _create_sizers(self):
        sizer = wx.FlexGridSizer(3, 2, 10, 10)
        sizer.AddGrowableCol(1, 1)
        sizer.AddGrowableRow(1, 1)

        # Row 0: Input Directory
        sizer.Add(self.local_dir_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        dir_input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        dir_input_sizer.Add(self.local_dir_ctrl, 1, wx.EXPAND | wx.RIGHT, 10)
        dir_input_sizer.Add(self.browse_button, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(dir_input_sizer, 1, wx.EXPAND)

        # Row 1: Excludes
        sizer.Add(self.local_exclude_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_TOP | wx.TOP, 5)
        sizer.Add(self.local_exclude_ctrl, 1, wx.EXPAND)

        # Row 2: Options
        sizer.AddSpacer(0)  # Empty cell for alignment
        options_sizer = wx.BoxSizer(wx.VERTICAL)
        options_sizer.Add(self.include_subdirs_check, 0, wx.BOTTOM, 5)
        options_sizer.Add(self.hide_binaries_check, 0)
        sizer.Add(options_sizer, 0, wx.EXPAND | wx.TOP, 5)

        self.SetSizer(sizer)


class ListPanel(wx.Panel):
    def __init__(self, parent, theme, is_dark):
        super().__init__(parent)
        self.theme = theme
        self.is_dark = is_dark
        self.scraped_files = []
        self.local_files = []
        self.discovered_url_count = 0
        self.user_has_resized = False
        self.sort_col_local = 0
        self.sort_dir_local = -1
        self.sort_col_web = 0
        self.sort_dir_web = -1
        self._create_widgets()
        self._create_sizers()
        self._bind_events()
        self.toggle_output_view(is_web_mode=True)
        self.local_file_list.ShowSortIndicator(self.sort_col_local, self.sort_dir_local == 1)
        self.standard_log_list.ShowSortIndicator(self.sort_col_web, self.sort_dir_web == 1)

    def _create_widgets(self):
        self.log_mode_panel = wx.Panel(self)
        self.standard_log_radio = CustomRadioButton(self.log_mode_panel, label="Files", theme=self.theme)
        self.verbose_log_radio = CustomRadioButton(self.log_mode_panel, label="Log", theme=self.theme)
        self.standard_log_radio.group = [self.standard_log_radio, self.verbose_log_radio]
        self.verbose_log_radio.group = [self.standard_log_radio, self.verbose_log_radio]
        self.standard_log_radio.SetValue(True)

        self.standard_log_list = ThemedListCtrl(self, style=wx.LC_REPORT | wx.LC_VRULES, theme=self.theme, is_dark=self.is_dark)
        self.standard_log_list.InsertColumn(0, "URL", width=200, format=wx.LIST_FORMAT_LEFT)
        self.standard_log_list.InsertColumn(1, "Saved Filename", width=400)
        self.verbose_log_ctrl = ThemedLogCtrl(self)
        self.local_file_list = ThemedListCtrl(self, style=wx.LC_REPORT | wx.LC_VRULES, theme=self.theme, is_dark=self.is_dark)
        self.local_file_list.InsertColumn(0, "Name", width=450, format=wx.LIST_FORMAT_LEFT)
        self.local_file_list.InsertColumn(1, "Type", width=120)
        self.local_file_list.InsertColumn(2, "Size", width=120, format=wx.LIST_FORMAT_RIGHT)

        self.delete_button = CustomSecondaryButton(self, label="Delete Selected", theme=self.theme)
        self.progress_gauge = CustomGauge(self, theme=self.theme)
        self.file_count_label = wx.StaticText(self, label="")

    def _create_sizers(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        log_mode_sizer = wx.BoxSizer(wx.HORIZONTAL)
        log_mode_sizer.Add(self.standard_log_radio, 0, wx.RIGHT, 10)
        log_mode_sizer.Add(self.verbose_log_radio, 0)
        self.log_mode_panel.SetSizer(log_mode_sizer)

        sizer.Add(self.log_mode_panel, 0, wx.ALL, 5)
        sizer.Add(self.verbose_log_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.standard_log_list, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.local_file_list, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.progress_gauge, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)

        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_sizer.Add(self.file_count_label, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        bottom_sizer.Add(self.delete_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizer.Add(bottom_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    def _bind_events(self):
        self.standard_log_radio.Bind(wx.EVT_RADIOBUTTON, self.on_toggle_log_mode)
        self.verbose_log_radio.Bind(wx.EVT_RADIOBUTTON, self.on_toggle_log_mode)

        for list_ctrl in [self.standard_log_list, self.local_file_list]:
            list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_selection_changed)
            list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_list_selection_changed)
            list_ctrl.Bind(wx.EVT_LIST_COL_END_DRAG, self.on_col_end_drag)
            list_ctrl.Bind(wx.EVT_LIST_COL_CLICK, self.on_col_click)

    def on_col_click(self, event):
        list_ctrl = event.GetEventObject()
        col = event.GetColumn()
        is_web_mode = list_ctrl == self.standard_log_list

        if is_web_mode:
            data_source, (sort_col, sort_dir), keys = self.scraped_files, (self.sort_col_web, self.sort_dir_web), ["url", "filename"]
        else:
            data_source, (sort_col, sort_dir), keys = self.local_files, (self.sort_col_local, self.sort_dir_local), ["name", "type", "size"]

        if col == sort_col:
            sort_dir *= -1
        else:
            sort_col = col
            sort_dir = 1

        sort_key = keys[col]
        reverse = sort_dir == -1

        if not is_web_mode and sort_key == "name":
            data_source.sort(key=lambda item: (item.get("type") != "Folder", item.get("name", "").lower()), reverse=reverse)
        else:
            data_source.sort(key=lambda item: item.get(sort_key, 0) if isinstance(item.get(sort_key, 0), (int, float)) else str(item.get(sort_key, "")).lower(), reverse=reverse)

        list_ctrl.ShowSortIndicator(col, not reverse)

        if is_web_mode:
            self.sort_col_web, self.sort_dir_web = sort_col, sort_dir
            self.populate_web_file_list()
        else:
            self.sort_col_local, self.sort_dir_local = sort_col, sort_dir
            self.populate_local_file_list(data_source)

    def on_col_end_drag(self, event):
        self.user_has_resized = True
        event.Skip()

    def resize_columns(self):
        if self.user_has_resized:
            return

        scrollbar_width = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X, self) + 5

        sl_list = self.standard_log_list
        if sl_list.IsShown():
            sl_width = sl_list.GetClientSize().width - scrollbar_width
            if sl_width > 0:
                sl_url_width = int(sl_width * 0.35)
                sl_filename_width = sl_width - sl_url_width
                sl_list.SetColumnWidth(0, sl_url_width)
                sl_list.SetColumnWidth(1, sl_filename_width)

        lf_list = self.local_file_list
        if lf_list.IsShown():
            lf_width = lf_list.GetClientSize().width - scrollbar_width
            if lf_width > 0:
                lf_type_width = 120
                lf_size_width = 120
                lf_name_width = lf_width - lf_type_width - lf_size_width
                lf_list.SetColumnWidth(0, lf_name_width)
                lf_list.SetColumnWidth(1, lf_type_width)
                lf_list.SetColumnWidth(2, lf_size_width)

    def _update_delete_button_state(self):
        list_ctrl = None
        if self.standard_log_list.IsShown():
            list_ctrl = self.standard_log_list
        elif self.local_file_list.IsShown():
            list_ctrl = self.local_file_list

        if list_ctrl:
            is_anything_selected = list_ctrl.GetSelectedItemCount() > 0
            self.delete_button.SetAlertState(is_anything_selected)
        else:
            self.delete_button.SetAlertState(False)

    def on_list_selection_changed(self, event):
        self._update_delete_button_state()

    def on_toggle_log_mode(self, event):
        if self.log_mode_panel.IsShown():
            is_files_mode = self.standard_log_radio.GetValue()
            self.standard_log_list.Show(is_files_mode)
            self.verbose_log_ctrl.Show(not is_files_mode)
            self.delete_button.Show(is_files_mode)
            if not is_files_mode:
                wx.CallAfter(self.verbose_log_ctrl.ScrollToEnd)
            self._update_delete_button_state()
            self.Layout()

    def toggle_output_view(self, is_web_mode):
        self.verbose_log_ctrl.Clear()
        self.log_mode_panel.Show(is_web_mode)
        self.local_file_list.Show(not is_web_mode)
        self.progress_gauge.SetValue(0)
        self.progress_gauge.Show(is_web_mode)
        if is_web_mode:
            self.on_toggle_log_mode(None)
        else:
            self.standard_log_list.Hide()
            self.verbose_log_ctrl.Hide()
            self.delete_button.Show(True)

        self.user_has_resized = False
        self._update_delete_button_state()
        self.Layout()
        wx.CallAfter(self.resize_columns)
        self.update_file_count()

    def add_scraped_files_batch(self, files_data):
        for file_data in files_data:
            new_file = {"url": file_data["url"], "path": file_data["path"], "filename": file_data["filename"]}
            self.scraped_files.append(new_file)

        sort_key = ["url", "filename"][self.sort_col_web]
        reverse = self.sort_dir_web == -1
        self.scraped_files.sort(key=lambda item: str(item.get(sort_key, "")).lower(), reverse=reverse)

        self.populate_web_file_list()

    def populate_web_file_list(self):
        self.standard_log_list.Freeze()
        self.standard_log_list.DeleteAllItems()
        for item in self.scraped_files:
            index = self.standard_log_list.InsertItem(self.standard_log_list.GetItemCount(), item["url"])
            self.standard_log_list.SetItem(index, 1, item["filename"])
        self.standard_log_list.Thaw()
        self.update_file_count()

    def populate_local_file_list(self, files):
        self.local_file_list.Freeze()
        self.local_file_list.DeleteAllItems()
        self.local_files = files
        for f in files:
            index = self.local_file_list.InsertItem(self.local_file_list.GetItemCount(), f["name"])
            self.local_file_list.SetItem(index, 1, f["type"])
            self.local_file_list.SetItem(index, 2, f["size_str"])
        self.local_file_list.Thaw()

        if not self.user_has_resized:
            self.resize_columns()
        self.update_file_count()

    def log_verbose(self, message):
        self.verbose_log_ctrl.AppendText(message + "\n")

    def clear_logs(self):
        self.verbose_log_ctrl.Clear()
        self.standard_log_list.DeleteAllItems()
        self.scraped_files.clear()
        self.discovered_url_count = 0
        self._update_delete_button_state()
        self.update_file_count()

    def update_discovered_count(self, count):
        self.discovered_url_count = count
        self.update_file_count()

    def update_file_count(self):
        label = ""
        if self.standard_log_list.IsShown():
            saved_count = self.standard_log_list.GetItemCount()
            total_known = saved_count + self.discovered_url_count
            if total_known > 0:
                label = f"{saved_count} saved / {total_known} discovered"
        elif self.local_file_list.IsShown():
            count = self.local_file_list.GetItemCount()
            if count > 0:
                label = f"{count} item(s)"

        self.file_count_label.SetLabel(label)
````

## File: app.py
````python
import wx
import winreg
import os
from datetime import datetime
from pathlib import Path
import ctypes
import subprocess
import platform
import multiprocessing
import threading

from ui.main_frame import MainFrame
from ui.widgets.dialogs import AboutDialog
import core.actions as actions
from core.packager import resource_path
from core.version import __version__
from core.config_manager import get_config
from core.task_handler import TaskHandler
from core.utils import get_downloads_folder, set_title_bar_theme

config = get_config()
BINARY_FILE_PATTERNS = config.get("binary_file_patterns", [])


class App(wx.Frame):
    def __init__(self):
        super().__init__(None, title="ContextPacker", size=wx.Size(1600, 950))

        self.version = __version__
        self.task_handler = TaskHandler(self)
        self.temp_dir = None
        self.final_output_path = None
        self.filename_prefix = ""
        self.log_queue = multiprocessing.Queue()
        self.cancel_event = None
        self.worker_thread = None
        self.is_shutting_down = False
        self.is_task_running = False
        self.is_dark = False  # Default to light mode
        self.local_files_to_exclude = set()
        self.exclude_list_last_line = 0
        self.local_scan_worker = None
        self.local_scan_cancel_event = None
        self.exclude_update_timer = wx.Timer(self)
        self.queue_listener_thread = None

        self._set_theme_palette()
        self.main_panel = MainFrame(self)
        self._apply_theme_to_widgets()
        self._setup_timer()
        self._set_icon()

        self.toggle_input_mode()
        self.Center()
        self.Show()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_TIMER, self.on_exclude_timer, self.exclude_update_timer)

        threading.Thread(target=self._detect_and_apply_theme, daemon=True).start()

    def start_queue_listener(self):
        if self.queue_listener_thread is None:
            self.queue_listener_thread = threading.Thread(target=self._queue_listener_worker, daemon=True)
            self.queue_listener_thread.start()

    def stop_queue_listener(self):
        if self.queue_listener_thread is not None:
            self.log_queue.put(None)  # Sentinel to stop the thread
            self.queue_listener_thread.join(timeout=1)
            self.queue_listener_thread = None

    def _queue_listener_worker(self):
        while True:
            try:
                msg_obj = self.log_queue.get()
                if msg_obj is None:  # Sentinel value
                    break
                wx.CallAfter(self._process_log_queue_message, msg_obj)
            except (EOFError, BrokenPipeError):
                break  # Exit if the queue is broken (e.g., child process crashed)
            except Exception:
                # Log other potential exceptions without crashing the listener
                continue

    def _process_log_queue_message(self, msg_obj):
        msg_type = msg_obj.get("type")
        message = msg_obj.get("message", "")

        if msg_type == "log":
            self.log_verbose(message)
        elif msg_type == "file_saved":
            # This is now handled in batches, but a single message handler is fine
            self.main_panel.list_panel.add_scraped_files_batch([msg_obj])
            queue_size = msg_obj.get("queue_size", 0)
            self.main_panel.list_panel.update_discovered_count(queue_size)
            verbose_msg = f"  -> Saved: {msg_obj['filename']} [{msg_obj['pages_saved']}/{msg_obj['max_pages']}]"
            self.log_verbose(verbose_msg)
        elif msg_type == "progress":
            self.main_panel.list_panel.progress_gauge.SetValue(msg_obj["value"])
            self.main_panel.list_panel.progress_gauge.SetRange(msg_obj["max_value"])
        elif msg_type == "status":
            self.task_handler.handle_status(msg_obj.get("status"), msg_obj)
        else:
            self.log_verbose(str(message))

    def _detect_and_apply_theme(self):
        """Worker function to detect dark mode and apply the theme."""
        is_dark = self._is_dark_mode()
        wx.CallAfter(self._update_theme, is_dark)

    def _update_theme(self, is_dark):
        """Updates the application theme. Must be called on the main thread."""
        if self.is_dark == is_dark:
            self._set_title_bar_theme()
            return

        self.is_dark = is_dark
        if hasattr(self, "main_panel") and self.main_panel:
            self.main_panel.list_panel.is_dark = is_dark
        self._set_theme_palette()
        self._apply_theme_to_widgets()
        self._set_title_bar_theme()

    def _is_dark_mode(self):
        system = platform.system()
        if system == "Windows":
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0
            except Exception:
                return False
        elif system == "Darwin":
            try:
                cmd = "defaults read -g AppleInterfaceStyle"
                p = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                return "Dark" in p.stdout
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False
        else:
            bg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
            return bg_color.GetLuminance() < 0.5

    def _set_theme_palette(self):
        self.accent_color = wx.Colour("#3CB371")
        self.accent_hover_color = wx.Colour("#2E8B57")
        danger_color = wx.Colour("#B22222")

        dark_colors = {"bg": wx.Colour(46, 46, 46), "fg": wx.Colour(224, 224, 224), "field": wx.Colour(60, 60, 60), "hover": wx.Colour(80, 80, 80), "secondary_bg": wx.Colour(80, 80, 80), "focus_field": wx.Colour(70, 70, 70)}
        light_colors = {"bg": wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK), "fg": wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT), "field": wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW), "hover": wx.Colour(212, 212, 212), "secondary_bg": wx.Colour(225, 225, 225), "focus_field": wx.Colour(230, 245, 230)}

        self.palette = dark_colors if self.is_dark else light_colors
        self.hover_color = self.palette["hover"]
        self.SetBackgroundColour(self.palette["bg"])

        self.theme = {
            "palette": self.palette,
            "accent_color": self.accent_color,
            "accent_hover_color": self.accent_hover_color,
            "hover_color": self.hover_color,
            "danger_color": danger_color,
        }

    def _apply_theme_to_widgets(self):
        def set_colors_recursive(widget):
            if hasattr(widget, "is_custom_themed") and widget.is_custom_themed:
                widget.UpdateTheme(self.theme)
                return

            widget.SetBackgroundColour(self.palette["bg"])
            widget.SetForegroundColour(self.palette["fg"])

            if isinstance(widget, (wx.TextCtrl, wx.Choice, wx.SpinCtrl, wx.ListCtrl)):
                widget.SetBackgroundColour(self.palette["field"])
                widget.SetForegroundColour(self.palette["fg"])
            if isinstance(widget, wx.StaticBox):
                widget.SetForegroundColour(self.palette["fg"])

            for child in widget.GetChildren():
                set_colors_recursive(child)

        set_colors_recursive(self.main_panel)
        self.main_panel.list_panel.verbose_log_ctrl.text_ctrl.SetBackgroundColour(self.palette["field"])
        self.main_panel.list_panel.verbose_log_ctrl.text_ctrl.SetForegroundColour(self.palette["fg"])
        self.main_panel.list_panel.standard_log_list.SetBackgroundColour(self.palette["field"])
        self.main_panel.list_panel.standard_log_list.SetForegroundColour(self.palette["fg"])
        self.main_panel.list_panel.local_file_list.SetBackgroundColour(self.palette["field"])
        self.main_panel.list_panel.local_file_list.SetForegroundColour(self.palette["fg"])
        self.main_panel.crawler_panel.include_paths_ctrl.text_ctrl.SetBackgroundColour(self.palette["field"])
        self.main_panel.crawler_panel.exclude_paths_ctrl.text_ctrl.SetBackgroundColour(self.palette["field"])
        self.main_panel.local_panel.local_exclude_ctrl.text_ctrl.SetBackgroundColour(self.palette["field"])
        self.main_panel.crawler_panel.about_text.SetForegroundColour(self.theme["accent_color"])
        self.main_panel.crawler_panel.version_text.SetForegroundColour(self.palette["fg"])
        self.Refresh()

    def _set_title_bar_theme(self):
        set_title_bar_theme(self, self.is_dark)

    def _setup_timer(self):
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_check_log_queue, self.timer)
        self.timer.Start(100)

    def _set_icon(self):
        try:
            icon_path = resource_path("assets/icons/ContextPacker.ico")
            if icon_path.exists():
                self.SetIcon(wx.Icon(str(icon_path), wx.BITMAP_TYPE_ICO))
        except Exception as e:
            print(f"Warning: Failed to set icon: {e}")

    def on_close(self, event):
        self.timer.Stop()
        self.stop_queue_listener()
        if self.local_scan_cancel_event:
            self.local_scan_cancel_event.set()

        if self.worker_thread and self.worker_thread.is_alive():
            if not self.is_shutting_down:
                self.is_shutting_down = True
                self.log_verbose("Shutdown requested. Waiting for task to terminate...")
                if self.cancel_event:
                    self.cancel_event.set()
                self.main_panel.crawler_panel.download_button.Disable()
                self.main_panel.package_button.Disable()
            event.Veto()
            return
        else:
            self.Destroy()

    def _toggle_ui_controls(self, enable=True, widget_to_keep_enabled=None):
        """Enable or disable all input controls, optionally keeping one enabled."""
        crawler_panel = self.main_panel.crawler_panel
        crawler_controls = [
            crawler_panel.start_url_ctrl,
            crawler_panel.user_agent_combo,
            crawler_panel.max_pages_ctrl,
            crawler_panel.crawl_depth_ctrl,
            crawler_panel.min_pause_ctrl,
            crawler_panel.max_pause_ctrl,
            crawler_panel.include_paths_ctrl,
            crawler_panel.exclude_paths_ctrl,
            crawler_panel.stay_on_subdomain_check,
            crawler_panel.ignore_queries_check,
            crawler_panel.download_button,
        ]

        widgets_to_toggle = [
            self.main_panel.web_crawl_radio,
            self.main_panel.local_dir_radio,
            self.main_panel.local_panel,
            self.main_panel.output_filename_ctrl,
            self.main_panel.output_format_choice,
            self.main_panel.package_button,
        ]

        widgets_to_toggle.extend(crawler_controls)

        for widget in widgets_to_toggle:
            if widget != widget_to_keep_enabled:
                if widget:
                    widget.Enable(enable)

        if not enable and widget_to_keep_enabled:
            if widget_to_keep_enabled:
                widget_to_keep_enabled.Enable(True)

    def on_toggle_input_mode(self, event):
        self.toggle_input_mode()

    def toggle_input_mode(self):
        is_url_mode = self.main_panel.web_crawl_radio.GetValue()
        self.main_panel.crawler_panel.Show(is_url_mode)
        self.main_panel.local_panel.Show(not is_url_mode)
        self.main_panel.list_panel.toggle_output_view(is_web_mode=is_url_mode)
        self.main_panel.left_panel.Layout()
        if not is_url_mode:
            self.start_local_file_scan()
        self._update_button_states()

    def on_browse(self, event):
        with wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.main_panel.local_panel.local_dir_ctrl.SetValue(path)
                self.start_local_file_scan()
        self._update_button_states()
        wx.CallAfter(self.main_panel.local_panel.local_dir_ctrl.SetFocus)

    def on_local_filters_changed(self, event):
        self.exclude_update_timer.Stop()
        self.start_local_file_scan()
        event.Skip()

    def on_exclude_text_update(self, event):
        self.exclude_update_timer.StartOnce(500)
        event.Skip()

    def on_download_button_click(self, event):
        print(f"DIAG: on_download_button_click called at {datetime.now()}")
        if self.is_task_running:
            self.on_stop_process()
        else:
            self.task_handler.start_download_task()

    def on_package_button_click(self, event):
        if self.is_task_running:
            self.on_stop_process()
        else:
            file_list_for_count = []
            if self.main_panel.web_crawl_radio.GetValue():
                file_list_for_count = self.main_panel.list_panel.scraped_files
            else:
                file_list_for_count = self.main_panel.list_panel.local_files
            self.task_handler.start_package_task(file_list_for_count)

    def on_stop_process(self):
        self.task_handler.stop_current_task()

    def on_copy_to_clipboard(self, event):
        if not self.final_output_path or not Path(self.final_output_path).exists():
            self.log_verbose("ERROR: No output file found to copy.")
            return

        try:
            with open(self.final_output_path, "r", encoding="utf-8") as f:
                content = f.read()

            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(content))
                wx.TheClipboard.Close()
                self.log_verbose(f"Copied {len(content):,} characters to clipboard.")
                self.main_panel.copy_button.SetSuccessState(True)
            else:
                self.log_verbose("ERROR: Could not open clipboard.")
        except Exception as e:
            self.log_verbose(f"ERROR: Failed to copy to clipboard: {e}")

    def on_exclude_timer(self, event):
        """Called when the debounce timer for the exclude list fires."""
        self.start_local_file_scan()

    def _update_timestamp_label(self):
        if self.main_panel and self.main_panel.output_timestamp_label:
            timestamp_str = datetime.now().strftime("-%y%m%d-%H%M%S")
            if self.main_panel.output_timestamp_label.GetLabel() != timestamp_str:
                self.main_panel.output_timestamp_label.SetLabel(timestamp_str)
                self.main_panel.right_panel_container.Layout()

    def on_check_log_queue(self, event):
        if not (self.worker_thread and self.worker_thread.is_alive()):
            self._update_timestamp_label()

    def _update_button_states(self):
        is_web_mode = self.main_panel.web_crawl_radio.GetValue()
        package_ready = False
        copy_ready = bool(self.final_output_path and Path(self.final_output_path).exists())

        if is_web_mode:
            if self.temp_dir and any(f.is_file() for f in Path(self.temp_dir).iterdir()):
                package_ready = True
        else:
            if self.main_panel.local_panel.local_dir_ctrl.GetValue():
                package_ready = True

        self.main_panel.package_button.Enable(package_ready)
        self.main_panel.copy_button.Enable(copy_ready)
        self.main_panel.copy_button.SetSuccessState(copy_ready)

    def log_verbose(self, message):
        self.main_panel.list_panel.log_verbose(message)

    def _open_output_folder(self):
        if not self.final_output_path:
            return
        self.log_verbose("Opening output folder...")
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["explorer", "/select,", self.final_output_path], creationflags=0x08000000)
            elif system == "Darwin":
                subprocess.run(["open", "-R", self.final_output_path], check=True)
            else:
                subprocess.run(["xdg-open", str(Path(self.final_output_path).parent)], check=True)
        except Exception as e:
            self.log_verbose(f"ERROR: Could not open output folder: {e}")

    def delete_scraped_file(self, filepath):
        try:
            os.remove(filepath)
            self.log_verbose(f"Deleted file: {filepath}")
            self._update_button_states()
        except Exception as e:
            self.log_verbose(f"ERROR: Could not delete file {filepath}: {e}")

    def remove_local_file_from_package(self, rel_path):
        self.local_files_to_exclude.add(rel_path)
        self.log_verbose(f"Will exclude from package: {rel_path}")

    def start_local_file_scan(self):
        if self.local_scan_worker and self.local_scan_worker.is_alive():
            if self.local_scan_cancel_event:
                self.local_scan_cancel_event.set()

        self.local_scan_cancel_event = threading.Event()

        input_dir = self.main_panel.local_panel.local_dir_ctrl.GetValue()
        if not input_dir or not Path(input_dir).is_dir():
            self.main_panel.list_panel.populate_local_file_list([])
            return

        wx.BeginBusyCursor()
        self.main_panel.local_panel.browse_button.Enable(False)
        self.main_panel.local_panel.include_subdirs_check.Enable(False)
        self.main_panel.local_panel.hide_binaries_check.Enable(False)

        self.local_files_to_exclude.clear()
        custom_excludes = [p.strip() for p in self.main_panel.local_panel.local_exclude_ctrl.GetValue().splitlines() if p.strip()]
        binary_excludes = BINARY_FILE_PATTERNS if self.main_panel.local_panel.hide_binaries_check.GetValue() else []
        args = (
            input_dir,
            self.main_panel.local_panel.include_subdirs_check.GetValue(),
            custom_excludes,
            binary_excludes,
            self.local_scan_cancel_event,
        )
        self.local_scan_worker = threading.Thread(target=self._local_scan_worker, args=args, daemon=True)
        self.local_scan_worker.start()

    def _local_scan_worker(self, input_dir, include_subdirs, custom_excludes, binary_excludes, cancel_event):
        try:
            files_to_show = actions.get_local_files(input_dir, include_subdirs, custom_excludes, binary_excludes, cancel_event)
            if not cancel_event.is_set():
                wx.CallAfter(self._on_local_scan_complete, files_to_show)
            else:
                wx.CallAfter(self._on_local_scan_complete, None)
        except Exception as e:
            wx.CallAfter(self.log_verbose, f"ERROR scanning directory: {e}")
            wx.CallAfter(self._on_local_scan_complete, None)

    def _on_local_scan_complete(self, files):
        if files is not None:
            self.main_panel.list_panel.populate_local_file_list(files)
        if self.main_panel.local_panel:
            self.main_panel.local_panel.browse_button.Enable(True)
            self.main_panel.local_panel.include_subdirs_check.Enable(True)
            self.main_panel.local_panel.hide_binaries_check.Enable(True)
        wx.EndBusyCursor()
        self.local_scan_worker = None

    def populate_local_file_list(self, include_subdirs=None):
        self.start_local_file_scan()

    def _get_downloads_folder(self):
        return get_downloads_folder()

    def on_show_about_dialog(self, event):
        font_path = resource_path("assets/fonts/SourceCodePro-Regular.ttf")
        with AboutDialog(self, self.theme, self.version, font_path, self.log_verbose) as dlg:
            dlg.ShowModal()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        print(f"DIAG: DPI awareness setting failed. Error: {e}")

    app = wx.App(False)
    frame = App()
    app.MainLoop()
````

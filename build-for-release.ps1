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

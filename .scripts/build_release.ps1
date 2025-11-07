<#
.SYNOPSIS
    Build a Windows release for ContextPacker using Poetry, Nox and PyInstaller.

.DESCRIPTION
    This helper automates the common steps to build a production release on Windows.
    It attempts to locate the Poetry virtualenv, upgrade pip, install binary deps
    into the venv if necessary, runs `poetry install` and then `poetry run nox -s build`.

    Run this from the repository root in PowerShell (pwsh).

.PARAMETER PythonPath
    Optional path to a Python executable to use for the project's virtualenv. If
    provided the script will tell Poetry to use that interpreter before installing.

.EXAMPLE
    pwsh -File .\scripts\build_release.ps1

    pwsh -File .\scripts\build_release.ps1 -PythonPath 'C:\Python314\python.exe'
#>

param(
    [string]$PythonPath = ''
)

Set-StrictMode -Version Latest

function Write-ErrAndExit([string]$msg) {
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$repoRoot = Resolve-Path -Path (Join-Path $scriptDir '..') | Select-Object -ExpandProperty Path
Push-Location -Path $repoRoot | Out-Null

Write-Host "Building ContextPacker release..." -ForegroundColor Cyan

if ($PythonPath) {
    Write-Host "Telling Poetry to use: $PythonPath"
    & poetry env use $PythonPath 2>&1 | Write-Host
}

# Ensure Poetry has a venv for this project
$venvPath = ''
try {
    $venvPath = (& poetry env info -p).Trim()
}
catch {
    Write-Host "Poetry virtualenv not found — creating one via 'poetry install'..."
    & poetry install
    $venvPath = (& poetry env info -p).Trim()
}

if (-not (Test-Path $venvPath)) {
    Write-ErrAndExit "Poetry venv path not found: $venvPath"
}

$py = Join-Path $venvPath 'Scripts\python.exe'
if (-not (Test-Path $py)) {
    Write-ErrAndExit "Python executable not found in venv: $py"
}

Write-Host "Using venv python: $py"

Write-Host "Upgrading pip/setuptools/wheel inside venv..."
& $py -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { Write-ErrAndExit 'Failed to upgrade pip in venv' }

Write-Host "Attempting to ensure binary dependencies are present (wxpython, pywin32)..."
try {
    & $py -m pip install wxpython -q
}
catch {
    Write-Host "Warning: automatic pip install of wxpython failed. If this fails you may need to use a matching Python (3.14) or install the wheel manually." -ForegroundColor Yellow
}

Write-Host "Running 'poetry install' to finalize the environment..."
& poetry install
if ($LASTEXITCODE -ne 0) { Write-ErrAndExit 'poetry install failed' }

Write-Host "Building release with Nox (PyInstaller spec) ..."
& poetry run nox -s build
if ($LASTEXITCODE -ne 0) { Write-ErrAndExit 'nox build failed' }

Write-Host "Build finished — check the 'dist' directory for the produced artifacts." -ForegroundColor Green

Pop-Location | Out-Null

exit 0

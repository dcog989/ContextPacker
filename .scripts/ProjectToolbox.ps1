# Project Toolbox - clean & build
# Version: 0.1.0
# -----------------------------------------------------------------------------

function Show-Menu {
    Clear-Host
    Write-Host "============= ContextPacker Project Toolbox ==============" -ForegroundColor Cyan
    Write-Host
    Write-Host " 1 > Clean Build Artifacts"
    Write-Host " 2 > Check for Package Updates"
    Write-Host " 3 > Quick Run (from Source)"
    Write-Host " 4 > Build and Run (Debug Executable)"
    Write-Host " 5 > Build for Production"
    Write-Host " 6 > Open Log File"
    Write-Host " 7 > Exit"
    Write-Host
    Write-Host "==========================================================" -ForegroundColor Cyan
}

# The project root is the parent directory of $PSScriptRoot
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogFilePath = Join-Path $ProjectRoot "logs\contextpacker.log"

do {
    Show-Menu
    $choice = Read-Host "Enter option [1-7]"

    # Set location to the project root for Poetry/Nox commands
    # Use -ErrorAction Stop to ensure failure here is caught by the try/catch block
    Push-Location -Path $ProjectRoot -ErrorAction Stop

    try {
        switch ($choice) {
            '1' {
                Write-Host "`n>>> Cleaning build artifacts..." -ForegroundColor Green
                poetry run nox -s clean
            }
            '2' {
                Write-Host "`n>>> Checking for outdated packages..." -ForegroundColor Green
                poetry show --outdated
            }
            '3' {
                Write-Host "`n>>> Running from source..." -ForegroundColor Green
                poetry run nox -s run
            }
            '4' {
                Write-Host "`n>>> Building and running for debug..." -ForegroundColor Green
                poetry run nox -s build_run
            }
            '5' {
                Write-Host "`n>>> Building for production..." -ForegroundColor Green
                poetry run nox -s build
            }
            '6' {
                Write-Host "`n>>> Opening log file..." -ForegroundColor Green
                # Use SilentlyContinue to prevent red text if logs directory doesn't exist
                if (Test-Path $LogFilePath -ErrorAction SilentlyContinue) {
                    Invoke-Item $LogFilePath
                }
                else {
                    Write-Host "Log file not found at: $LogFilePath" -ForegroundColor Yellow
                }
            }
            '7' {
                Write-Host "`nExiting script."
            }
            default {
                Write-Host "`nInvalid selection. Please try again." -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "`nAn error occurred:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red

        # Use SilentlyContinue to prevent red text if logs directory doesn't exist
        if (Test-Path $LogFilePath -ErrorAction SilentlyContinue) {
            Write-Host "Opening log file for details..." -ForegroundColor Yellow
            Invoke-Item $LogFilePath
        }
    }
    finally {
        # Return to the original directory
        Pop-Location
    }

    if ($choice -ne '7') {
        Write-Host "`nPress Enter to return to the menu..." -ForegroundColor Yellow
        Read-Host | Out-Null
    }

} until ($choice -eq '7')
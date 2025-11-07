# Project Toolbox - clean & build
# Version: 0.1.0

function Show-Menu {
    Clear-Host
    Write-Host "============= ContextPacker Project Toolbox ==============" -ForegroundColor Cyan
    Write-Host
    Write-Host " 1 > Clean Build Artifacts"
    Write-Host " 2 > Check for Package Updates"
    Write-Host " 3 > Build and Run (Debug)"
    Write-Host " 4 > Build for Production"
    Write-Host " 5 > Exit"
    Write-Host
    Write-Host "==========================================================" -ForegroundColor Cyan
}

$ProjectRoot = Resolve-Path -Path (Join-Path $PSScriptRoot "..")

do {
    Show-Menu
    $choice = Read-Host "Enter option [1-5]"

    # Set location to the project root for Poetry/Nox commands
    Push-Location -Path $ProjectRoot

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
                Write-Host "`n>>> Building and running for debug..." -ForegroundColor Green
                poetry run nox -s build_run
            }
            '4' {
                Write-Host "`n>>> Building for production..." -ForegroundColor Green
                poetry run nox -s build
            }
            '5' {
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
    }
    finally {
        # Return to the original directory
        Pop-Location
    }

    if ($choice -ne '5') {
        Write-Host "`nPress Enter to return to the menu..." -ForegroundColor Yellow
        Read-Host | Out-Null
    }

} until ($choice -eq '5')
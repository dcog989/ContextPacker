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
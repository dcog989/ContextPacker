# Project Toolbox - clean & build
# Version: 0.1.8
# -----------------------------------------------------------------------------

# --- Configuration Section ---
# Adjust these variables as needed for your project
$Config = @{
    ProjectName = "ContextPacker"
    ProjectRoot = $null  # Will be set after function definition
    LogsDir     = "logs"
    LogFileName = "contextpacker.log"
    MenuOptions = @{
        '1' = @{ Name = "Clean Build Artifacts"; Action = { Invoke-ActionClean } }
        '2' = @{ Name = "Check for Package Updates"; Action = { Invoke-ActionCheckUpdates } }
        '3' = @{ Name = "Quick Run (from Source)"; Action = { Invoke-ActionQuickRun } }
        '4' = @{ Name = "Build and Run (Debug Executable)"; Action = { Invoke-ActionBuildRunDebug } } # Fixed syntax
        '5' = @{ Name = "Build Production Package"; Action = { Invoke-ActionBuildProduction } }
        '6' = @{ Name = "Open Log File"; Action = { Invoke-ActionOpenLog } }
        'Q' = @{ Name = "Quit"; Action = { return 'exit' } }
    }
}

# -----------------------------------------------------------------------------

# Function to attempt finding the project root based on standard Python project files
function Get-ProjectRoot {
    $currentPath = $PSScriptRoot
    $rootIndicatorFiles = @("pyproject.toml", "poetry.lock")

    while ($currentPath) {
        foreach ($indicator in $rootIndicatorFiles) {
            if (Test-Path (Join-Path $currentPath $indicator)) {
                Write-Verbose "Found project root at: $currentPath (based on $indicator)"
                return $currentPath
            }
        }
        $parentPath = Split-Path $currentPath -Parent
        if ($parentPath -eq $currentPath) {
            # Reached the system root
            break
        }
        $currentPath = $parentPath
    }
    # Fallback: use parent of script root if standard files not found
    Write-Warning "Could not find standard project root file (pyproject.toml/poetry.lock). Using parent directory of script."
    return Split-Path -Parent $PSScriptRoot
}

# Function to verify required tools are available (Poetry and Nox via poetry run)
function Test-RequiredTools {
    try {
        $poetryVersion = & poetry --version
        Write-Host "Poetry found: $poetryVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "Error: 'poetry' command not found or failed." -ForegroundColor Red
        Write-Host "Please ensure Poetry is installed and accessible." -ForegroundColor Red
        return $false
    }

    # Set location to the project root to run poetry commands in the correct context
    Push-Location -Path $Config.ProjectRoot -ErrorAction Stop
    try {
        # Attempt to run 'nox --version' using poetry. This will fail if nox is not installed in the env.
        $noxCheckResult = & poetry run nox --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Poetry run failed with exit code $LASTEXITCODE. Output: $noxCheckResult"
        }
        Write-Host "Nox found in Poetry environment (Version: $noxCheckResult)." -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "Error: 'nox' command not found or failed within the Poetry environment." -ForegroundColor Red
        Write-Host "This usually means Nox is not installed in the project's virtual environment." -ForegroundColor Red
        Write-Host "Solution: Run 'poetry install' in the project root to install dependencies listed in pyproject.toml." -ForegroundColor Yellow
        Write-Host "If Nox is missing from pyproject.toml, add it using 'poetry add --group dev nox'." -ForegroundColor Yellow
        return $false
    }
    finally {
        Pop-Location # Return to the original directory
    }
}

# Centralized logging function
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    # Ensure logs directory exists
    $logDir = Join-Path $Config.ProjectRoot $Config.LogsDir
    if (!(Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    Add-Content -Path $Config.LogFilePath -Value $logEntry
}

# Action Functions (Using poetry run)
function Invoke-ActionClean {
    Write-Host "`n>>> Cleaning build artifacts..." -ForegroundColor Green
    Write-Log "Initiated Clean Build Artifacts task."
    $exitCode = 0
    try {
        $result = & poetry run nox -s clean
        Write-Host $result
    }
    catch {
        $exitCode = 1
        Write-Log "Error during Clean: $($_.Exception.Message)" "ERROR"
        Write-Host "An error occurred during cleaning: $($_.Exception.Message)" -ForegroundColor Red
    }
    return $exitCode
}

function Invoke-ActionCheckUpdates {
    Write-Host "`n>>> Checking for outdated packages..." -ForegroundColor Green
    Write-Log "Initiated Check for Package Updates task."
    $exitCode = 0
    try {
        $outdatedResult = & poetry show --outdated
        if ($LASTEXITCODE -eq 0) {
            if ($outdatedResult -and $outdatedResult.Count -gt 0) {
                Write-Host "Outdated packages found:" -ForegroundColor Yellow
                Write-Host $outdatedResult
                Write-Host ""

                $confirmUpdate = Read-Host "Do you want to update these packages now? (y/N)"
                if ($confirmUpdate -eq 'y' -or $confirmUpdate -eq 'Y') {
                    Write-Host "`n>>> Updating packages..." -ForegroundColor Green
                    & poetry update
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host "Packages updated successfully." -ForegroundColor Green
                    }
                    else {
                        Write-Host "Package update failed." -ForegroundColor Red
                        $exitCode = 1
                    }
                }
                else {
                    Write-Host "Package update skipped." -ForegroundColor Yellow
                }
            }
            else {
                Write-Host "All packages are up to date." -ForegroundColor Green
            }
        }
        else {
            Write-Log "Error running 'poetry show --outdated': Exit code $LASTEXITCODE" "ERROR"
            Write-Host "Error running 'poetry show --outdated'. Check logs." -ForegroundColor Red
            $exitCode = 1
        }
    }
    catch {
        $exitCode = 1
        Write-Log "Error during Check Updates: $($_.Exception.Message)" "ERROR"
        Write-Host "An error occurred while checking for updates: $($_.Exception.Message)" -ForegroundColor Red
    }
    return $exitCode
}

function Invoke-ActionQuickRun {
    Write-Host "`n>>> Running from source..." -ForegroundColor Green
    Write-Log "Initiated Quick Run task."
    $exitCode = 0
    try {
        $result = & poetry run nox -s run
        Write-Host $result
    }
    catch {
        $exitCode = 1
        Write-Log "Error during Quick Run: $($_.Exception.Message)" "ERROR"
        Write-Host "An error occurred during quick run: $($_.Exception.Message)" -ForegroundColor Red
    }
    return $exitCode
}

function Invoke-ActionBuildRunDebug {
    Write-Host "`n>>> Building and running for debug..." -ForegroundColor Green
    Write-Log "Initiated Build and Run Debug task."
    $exitCode = 0
    try {
        $result = & poetry run nox -s build_run
        Write-Host $result
    }
    catch {
        $exitCode = 1
        Write-Log "Error during Build Run Debug: $($_.Exception.Message)" "ERROR"
        Write-Host "An error occurred during debug build/run: $($_.Exception.Message)" -ForegroundColor Red
    }
    return $exitCode
}

function Invoke-ActionBuildProduction {
    Write-Host "`n>>> Building for production..." -ForegroundColor Green
    Write-Log "Initiated Build for Production task."
    $exitCode = 0
    try {
        $result = & poetry run nox -s build
        Write-Host $result

    }
    catch {
        $exitCode = 1
        Write-Log "Error during Production Build: $($_.Exception.Message)" "ERROR"
        Write-Host "An error occurred during production build: $($_.Exception.Message)" -ForegroundColor Red
    }
    return $exitCode
}

function Invoke-ActionOpenLog {
    Write-Host "`n>>> Opening log file..." -ForegroundColor Green
    Write-Log "User requested to open log file."
    if (Test-Path $Config.LogFilePath) {
        try {
            Invoke-Item $Config.LogFilePath
        }
        catch {
            Write-Host "Failed to open log file: $($_.Exception.Message)" -ForegroundColor Red
            Write-Log "Failed to open log file: $($_.Exception.Message)" "ERROR"
        }
    }
    else {
        Write-Host "Log file not found at: $($Config.LogFilePath)" -ForegroundColor Yellow
        Write-Log "Log file not found at: $($Config.LogFilePath)" "WARN"
    }
}

# Initialize ProjectRoot and LogFilePath based on config
$Config.ProjectRoot = Get-ProjectRoot
$Config.LogFilePath = Join-Path $Config.ProjectRoot $Config.LogsDir $Config.LogFileName

# Main Menu Display Function
function Show-Menu {
    Clear-Host
    Write-Host "============= $($Config.ProjectName) Project Toolbox ==============" -ForegroundColor Cyan
    Write-Host ""
    foreach ($key in ($Config.MenuOptions.Keys | Sort-Object)) {
        Write-Host " $key > $($Config.MenuOptions[$key].Name)"
    }
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
}

# --- Main Script Execution ---
$firstRun = $true
do {
    Show-Menu

    # Run environment check only on the first iteration
    if ($firstRun) {
        $firstRun = $false
        Write-Host "`nPre-flight check..." -ForegroundColor Yellow
        if (-not (Test-RequiredTools)) {
            Write-Host "`nEnvironment check failed. Some features may not work." -ForegroundColor Red
            Write-Host "Press Enter to continue to the menu or close the window to exit..." -ForegroundColor Yellow
            Read-Host | Out-Null
        }
    }

    # Prompt with 'Q' now that it's an option
    $validChoice = $false
    do {
        $choice = Read-Host "Enter option [1-Q]"
        if ($Config.MenuOptions.ContainsKey($choice)) {
            $validChoice = $true
        }
        else {
            Write-Host "Invalid selection. Enter a number from the menu or 'Q' to quit." -ForegroundColor Red
        }
    } while (-not $validChoice)

    # Set location to the project root for Poetry/Nox commands
    Push-Location -Path $Config.ProjectRoot -ErrorAction Stop
    $actionResult = $null
    try {
        Write-Log "User selected option: $choice"
        $actionScriptBlock = $Config.MenuOptions[$choice].Action
        $actionResult = & $actionScriptBlock
    }
    catch {
        Write-Host "`nAn unexpected error occurred:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Log "Unexpected error in main loop: $($_.Exception.Message)" "ERROR"
        if (Test-Path $Config.LogFilePath) {
            Write-Host "Opening log file for details..." -ForegroundColor Yellow
            Invoke-Item $Config.LogFilePath
        }
    }
    finally {
        Pop-Location # Return to the original directory
    }

    # Handle exit signal or pause for other actions
    if ($actionResult -eq 'exit') {
        Write-Host "`nExiting script. Goodbye!" -ForegroundColor Green
        Write-Log "Script exited by user."
        break # Exit the do-while loop
    }
    else {
        Write-Host "`nPress Enter to return to the menu..." -ForegroundColor Yellow
        Read-Host | Out-Null
    }
} while ($true) # Loop continues until 'exit' signal is returned from an action
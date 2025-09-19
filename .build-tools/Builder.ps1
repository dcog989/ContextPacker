# Builder.ps1 - A menu-driven script for managing the ContextPacker build process.

# --- Initial Setup ---
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

$LogDir = Join-Path $ProjectRoot ".build-tools"
$LogTimestamp = Get-Date -Format "yyyyMMdd.HHmmss"
$LogFile = Join-Path $LogDir "ContextPacker-build-$LogTimestamp.log"

# --- Helper Functions ---
function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$Timestamp] $Message" | Out-File -FilePath $LogFile -Append
}

function Remove-OldLogs {
    Write-Log "--- Script Start ---"
    $ConfigPath = Join-Path $ProjectRoot "config.json"
    $MaxLogs = 21 # Default
    if (Test-Path $ConfigPath) {
        try {
            $Config = Get-Content $ConfigPath | ConvertFrom-Json
            if ($Config.PSObject.Properties["max_build_logs"]) {
                $MaxLogs = $Config.max_build_logs
            }
        }
        catch {
            Write-Log "Warning: Could not read 'max_build_logs' from config.json. Using default of $MaxLogs."
        }
    }
    
    $LogFiles = Get-ChildItem -Path $LogDir -Filter "ContextPacker-build-*.log" | Sort-Object CreationTime -Descending
    
    if ($LogFiles.Count -gt $MaxLogs) {
        $FilesToDelete = $LogFiles | Select-Object -Skip $MaxLogs
        Write-Log "Cleaning up old log files..."
        foreach ($file in $FilesToDelete) {
            Write-Log "Removing $($file.Name)"
            Remove-Item $file.FullName -Force
        }
    }
}

# Function to check for a command's existence
function Test-CommandExists {
    param($command)
    return (Get-Command $command -ErrorAction SilentlyContinue)
}

# Function to install a Python package if it's missing
function Assert-PythonPackage {
    param(
        [string]$PackageName,
        [string]$CommandName
    )
    Write-Host "Checking for $PackageName..." -ForegroundColor Green
    Write-Log "Checking for $PackageName..."
    if (-not (Test-CommandExists $CommandName)) {
        Write-Log "$PackageName not found."
        $choice = Read-Host "$PackageName not found. Would you like to try and install it now via 'pip install $PackageName'? (y/n)"
        if ($choice -eq 'y') {
            Write-Log "User chose to install $PackageName."
            & pip install $PackageName 2>&1 | Out-File -FilePath $LogFile -Append
            if (-not (Test-CommandExists $CommandName)) {
                Write-Host "Installation failed. See log for details." -ForegroundColor Red
                Write-Log "Installation failed or $PackageName is not in PATH."
                return $false
            }
            Write-Host "$PackageName installed successfully." -ForegroundColor Green
            Write-Log "$PackageName installed successfully."
        }
        else {
            Write-Host "Action cancelled. $PackageName is required." -ForegroundColor Red
            Write-Log "User cancelled installation."
            return $false
        }
    }
    else {
        Write-Log "$PackageName found."
    }
    return $true
}

function New-ChangelogFile {
    param([string]$OutputPath)
    Write-Host "Generating CHANGELOG.md..."
    Write-Log "Generating CHANGELOG.md..."
    try {
        $gitLogOutput = & git log --pretty=format:"- %s (%h)" 2>&1
        $gitLogOutput | Out-File -FilePath $LogFile -Append
        if ($LastExitCode -ne 0) { throw "Git command failed." }
        
        $gitLogOutput | Out-File -FilePath $OutputPath -Encoding utf8
        Write-Log "CHANGELOG.md generated successfully at $OutputPath."
        return $true
    }
    catch {
        Write-Host "Failed to generate CHANGELOG.md. See log for details." -ForegroundColor Red
        Write-Log "ERROR: Failed to generate CHANGELOG.md. Is Git installed and is this a Git repository? Details: $($_.Exception.Message)"
        return $false
    }
}

# --- Task Functions ---

function Remove-BuildArtifacts {
    Write-Host "--- Cleaning Build Artifacts ---" -ForegroundColor Cyan

    $processName = "ContextPacker"
    $distPath = (Join-Path $ProjectRoot "dist").ToLower()
    # Find a running process that originates from our local 'dist' directory.
    $existingProcess = Get-Process -Name $processName -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.ToLower().StartsWith($distPath) }

    if ($existingProcess) {
        $confirm = Read-Host "$processName is running from the 'dist' directory. To clean it, the process must be stopped. Stop it now? (y/n)"
        if ($confirm.ToLower() -eq 'y') {
            Write-Host "Stopping existing $processName process..."
            Write-Log "Stopping existing $processName process (PID: $($existingProcess.Id)) to allow clean-up."
            Stop-Process -Name $processName -Force
            Start-Sleep -Seconds 1 # Give the OS a moment to release file handles
        }
        else {
            Write-Host "Skipping clean-up of 'dist' directory because the application is running." -ForegroundColor Yellow
            Write-Log "User cancelled clean-up of 'dist' because process was running."
        }
    }

    $DirsToRemove = @("build", "dist")
    foreach ($dir in $DirsToRemove) {
        if (Test-Path $dir) {
            Write-Host "Removing directory: $dir"
            Write-Log "Removing directory: $dir"
            try {
                Remove-Item -Recurse -Force $dir -ErrorAction Stop
            }
            catch {
                Write-Host "Could not fully remove '$dir'. It may be in use. See log for details." -ForegroundColor Yellow
                Write-Log "ERROR: Failed to remove '$dir'. Details: $($_.Exception.Message)"
            }
        }
    }

    $PyCacheDirs = Get-ChildItem -Path $ProjectRoot -Recurse -Directory -Filter "__pycache__"
    if ($PyCacheDirs) {
        Write-Host "Removing __pycache__ directories..."
        Write-Log "Removing __pycache__ directories..."
        $PyCacheDirs | Remove-Item -Recurse -Force
    }

    Write-Host "✔ Clean-up complete." -ForegroundColor Green
    Write-Log "Clean-up complete."
}

function New-RequirementsFile {
    Write-Host "--- Generating requirements.txt ---" -ForegroundColor Cyan
    if (-not (Assert-PythonPackage -PackageName "pipreqs" -CommandName "pipreqs")) { return }

    Write-Host "Running pipreqs..."
    & pipreqs --force --savepath "requirements.txt" "." 2>&1 | Out-File -FilePath $LogFile -Append
    if ($LastExitCode -ne 0) {
        Write-Host "pipreqs failed. See log for details." -ForegroundColor Red
        Write-Log "pipreqs command failed with exit code $LastExitCode."
        return
    }

    Write-Host "Adding known dependencies..."
    Add-Content -Path "requirements.txt" -Value "`nlxml"
    Write-Log "Appended 'lxml' to requirements.txt"

    Write-Host "✔ Successfully generated requirements.txt" -ForegroundColor Green
}

function Invoke-Build {
    param(
        [switch]$DebugMode
    )
    $BuildTypeName = if ($DebugMode) { "Debug" } else { "Production" }
    Write-Host "--- Building Executable ($BuildTypeName) ---" -ForegroundColor Cyan
    if (-not (Assert-PythonPackage -PackageName "pyinstaller" -CommandName "pyinstaller")) { return $null }

    $AppName = "ContextPacker"
    $SpecFile = "$AppName.spec"
    $DistDir = "dist"
    $BuildDir = "build"
    $AbsoluteDistDir = Join-Path $ProjectRoot $DistDir

    Write-Host "Cleaning previous build directories..."
    if (Test-Path $AbsoluteDistDir) { Remove-Item -Recurse -Force $AbsoluteDistDir 2>&1 | Out-File -FilePath $LogFile -Append }
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir 2>&1 | Out-File -FilePath $LogFile -Append }
    Write-Log "Cleaned old build directories."

    $originalSpecContent = Get-Content $SpecFile -Raw
    try {
        if ($DebugMode) {
            Write-Log "Modifying spec file for debug build (console=True)."
            $modifiedSpecContent = $originalSpecContent -replace 'console=False', 'console=True'
            $modifiedSpecContent | Set-Content $SpecFile -Encoding utf8
        }
        else {
            Write-Log "Ensuring spec file is set for production build (console=False)."
            $modifiedSpecContent = $originalSpecContent -replace 'console=True', 'console=False'
            $modifiedSpecContent | Set-Content $SpecFile -Encoding utf8
        }

        Write-Host "Running PyInstaller..."
        $PyInstallerArgs = @("--clean", "--log-level", "ERROR", $SpecFile)
        
        $output = & pyinstaller $PyInstallerArgs 2>&1
        $output | Out-File -FilePath $LogFile -Append

        if ($LastExitCode -ne 0) {
            Write-Host "PyInstaller failed. See log for details." -ForegroundColor Red
            Write-Log "PyInstaller command failed with exit code $LastExitCode."
            Write-Host "--- PyInstaller Error Output ---" -ForegroundColor Yellow
            $output | Write-Host
            return $null
        }
    }
    finally {
        Write-Log "Restoring original spec file."
        $originalSpecContent | Set-Content $SpecFile -Encoding utf8
    }

    # PyInstaller can place the exe in dist/ or dist/AppName/. This handles both.
    $FinalExePath = Join-Path -Path $AbsoluteDistDir -ChildPath "$AppName\$AppName.exe"
    if (-not (Test-Path $FinalExePath)) {
        $FinalExePath = Join-Path -Path $AbsoluteDistDir -ChildPath "$AppName.exe"
        if (-not (Test-Path $FinalExePath)) {
            Write-Host "PyInstaller build finished, but the executable could not be found." -ForegroundColor Red
            Write-Log "ERROR: Could not find $AppName.exe in '$AbsoluteDistDir' or its subdirectory."
            return $null
        }
    }

    Write-Host "✔ Build complete!" -ForegroundColor Green
    Write-Log "PyInstaller build successful. Executable at: $FinalExePath"
    
    if (!$DebugMode) {
        $ChangelogPath = Join-Path $AbsoluteDistDir "CHANGELOG.md"
        if (New-ChangelogFile -OutputPath $ChangelogPath) {
            $7zExe = Join-Path $ProjectRoot ".build-tools\7z\7za.exe"
            if (-not (Test-Path $7zExe)) {
                Write-Host "7za.exe not found. Skipping compression." -ForegroundColor Yellow
                Write-Log "Warning: 7za.exe not found at $7zExe. Skipping compression."
            }
            else {
                $Version = (Get-Content "core/version.py").Split('"')[1]
                $ArchiveName = "ContextPacker-v$($Version).7z"
                $ArchivePath = Join-Path $AbsoluteDistDir $ArchiveName
                Write-Host "Compressing build output..."
                Write-Log "Compressing to $ArchivePath..."
                
                # Use absolute paths for 7z arguments for reliability
                $7zArgs = @("a", "-t7z", "-m0=LZMA2", "-mx=3", $ArchivePath, $FinalExePath, $ChangelogPath)
                & $7zExe $7zArgs 2>&1 | Out-File -FilePath $LogFile -Append

                if ($LastExitCode -eq 0) {
                    Write-Host "✔ Compression successful." -ForegroundColor Green
                    Write-Log "7z compression successful."
                }
                else {
                    Write-Host "Compression failed. See log for details." -ForegroundColor Red
                    Write-Log "7z compression failed with exit code $LastExitCode."
                }
            }
        }
    }
    
    Write-Host "Opening output folder..."
    Invoke-Item $AbsoluteDistDir
    Write-Log "Opened output folder: $AbsoluteDistDir"
    return $FinalExePath
}

function Invoke-BuildAndRun {
    $processName = "ContextPacker"
    $existingProcess = Get-Process -Name $processName -ErrorAction SilentlyContinue

    if ($existingProcess) {
        $confirm = Read-Host "$processName is already running. Do you want to stop it and proceed? (y/n)"
        if ($confirm.ToLower() -eq 'y') {
            Write-Host "Stopping existing $processName process..."
            Write-Log "Stopping existing $processName process (PID: $($existingProcess.Id))."
            Stop-Process -Name $processName -Force
        }
        else {
            Write-Host "Build cancelled by user." -ForegroundColor Yellow
            Write-Log "User cancelled build because process was running."
            return
        }
    }
    
    $exePath = Invoke-Build -DebugMode
    if ($exePath -and (Test-Path $exePath)) {
        Write-Host "Build successful. Launching..." -ForegroundColor Green
        Write-Log "Launching debug build..."
        Start-Process $exePath
    }
    else {
        Write-Host "Build failed. Cannot run application." -ForegroundColor Red
        Write-Log "Build failed, cannot run."
    }
}

# --- Script Entry Point ---
Remove-OldLogs

# --- Main Menu Loop ---
:menuLoop while ($true) {
    Clear-Host
    Write-Host "---------------------------------"
    Write-Host "  ContextPacker Build Assistant  "
    Write-Host "---------------------------------"
    Write-Host "Verbose output is logged to:" -ForegroundColor Gray
    Write-Host (Split-Path $LogFile -Leaf) -ForegroundColor Gray
    Write-Host ""
    Write-Host "1. Clean Build Artifacts"
    Write-Host "2. Generate requirements.txt"
    Write-Host "3. Build and Run (Debug)"
    Write-Host "4. Build Executable (Production)"
    Write-Host "Q. Quit"
    $choice = Read-Host "`nPlease select an option"
    
    Write-Log "`n--- Build Action: $choice ---"

    switch ($choice) {
        "1" { Remove-BuildArtifacts }
        "2" { New-RequirementsFile }
        "3" { Invoke-BuildAndRun }
        "4" { Invoke-Build }
        "q" { break menuLoop }
        default { Write-Host "Invalid option." -ForegroundColor Red }
    }

    if ($choice.ToLower() -ne "q") {
        Write-Host ""
        Read-Host "Press Enter to return to the menu..."
    }
}

Write-Host "Exiting builder."
Write-Log "--- Script End ---`n"```
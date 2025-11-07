<#
PowerShell helper to run the environment checker.

Usage:
    .\scripts\check_env.ps1

This script will prefer `poetry run python` if `poetry` is available, otherwise falls back to `python`.
It forwards the exit code from the Python script.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Invoke-CheckEnv {
    $pyScript = "scripts\check_env.py"

    $poetry = Get-Command poetry -ErrorAction SilentlyContinue
    if ($poetry) {
        Write-Host "Running: poetry run python $pyScript"
        $proc = Start-Process -FilePath "poetry" -ArgumentList "run", "python", $pyScript -NoNewWindow -Wait -PassThru
        return $proc.ExitCode
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        Write-Error "No 'python' executable found on PATH and poetry is not available. Activate your virtualenv or install Python."
        return 2
    }

    Write-Host "Running: python $pyScript"
    $proc = Start-Process -FilePath $python.Path -ArgumentList $pyScript -NoNewWindow -Wait -PassThru
    return $proc.ExitCode
}

$exitCode = Invoke-CheckEnv
if ($exitCode -eq 0) {
    Write-Host "Environment check passed." -ForegroundColor Green
}
elseif ($exitCode -eq 2) {
    Write-Error "Environment check couldn't run due to missing runtime (python/poetry)."
}
else {
    Write-Warning "Environment check returned non-zero exit code: $exitCode"
}

exit $exitCode

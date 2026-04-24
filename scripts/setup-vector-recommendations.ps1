Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$backendDir = Join-Path $repoRoot "backend"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

Write-Host "Using Python: $python"

& $python (Join-Path $backendDir "setup_vector_recommendations.py") @args

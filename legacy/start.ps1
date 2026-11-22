# Convenience launcher: setup (if needed) + run backend
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
if (-not (Test-Path ".venv") -and -not (Test-Path "backend\env")) {
    .\setup.ps1
}
.\run_backend.ps1

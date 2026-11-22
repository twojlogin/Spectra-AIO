# Spectra-AIO backend launcher (Windows PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        $k,$v = $_ -split '=',2
        if ($k -and $v -and -not [Environment]::GetEnvironmentVariable($k.Trim())) {
            [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim())
        }
    }
}

$venvPython = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" }
              elseif (Test-Path "backend\env\Scripts\python.exe") { "backend\env\Scripts\python.exe" }
              else { "python" }

$hostAddr = if ($env:SPECTRA_HOST) { $env:SPECTRA_HOST } else { "127.0.0.1" }
$port = if ($env:SPECTRA_PORT) { $env:SPECTRA_PORT } else { "8000" }

Write-Host "[*] Starting Spectra-AIO backend on http://$hostAddr`:$port"
& $venvPython -m uvicorn backend.main_backend:app --host $hostAddr --port $port

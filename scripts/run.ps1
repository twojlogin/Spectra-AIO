$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if (Test-Path ".venv\Scripts\python.exe") { $py = ".venv\Scripts\python.exe" } else { $py = "python" }
$hostAddr = if ($env:SPECTRA_HOST) { $env:SPECTRA_HOST } else { "127.0.0.1" }
$port = if ($env:SPECTRA_PORT) { $env:SPECTRA_PORT } else { "8000" }
& $py -m uvicorn backend.main_backend:app --host $hostAddr --port $port

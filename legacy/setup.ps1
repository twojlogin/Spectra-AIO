# Spectra-AIO setup script (Windows PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Find-Python {
    foreach ($cmd in @("py -3", "python", "python3")) {
        try {
            & $cmd --version | Out-Null
            if ($LASTEXITCODE -eq 0) { return $cmd }
        } catch {}
    }
    return $null
}

$pythonCmd = $env:PYTHON_BIN
if (-not $pythonCmd) { $pythonCmd = Find-Python }
if (-not $pythonCmd) {
    Write-Error "Python 3.10+ not found. Install Python and retry."
}

Write-Host "[*] Using Python: $pythonCmd"
& $pythonCmd -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)"
if ($LASTEXITCODE -ne 0) { Write-Error "Python 3.10+ is required." }

$venvDir = if ($env:VENV_DIR) { $env:VENV_DIR } else { ".venv" }
if (-not (Test-Path $venvDir)) {
    Write-Host "[*] Creating virtual environment: $venvDir"
    & $pythonCmd -m venv $venvDir
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) { Write-Error "venv python not found at $venvPython" }

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r backend\requirements.txt

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[*] Created .env from .env.example"
}

Write-Host "[OK] Setup complete."
Write-Host "Next: .\\run_backend.ps1"

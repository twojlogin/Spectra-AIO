# SpectraCam-AIO Launcher (Fixed venv/pip handling)
# Robust: detects Python, creates venv, installs deps via venv python -m pip
# Self-contained, local aliases, backend starter.

# DYNAMICZNA ŚCIEŻKA - H5N1_CORE_LOGIC
$Base = $PSScriptRoot
Write-Host "`n== SpectraCam-AIO Initializer (Portable) ==" -ForegroundColor Cyan
Write-Host "[*] Lokalizacja bazowa: $Base" -ForegroundColor Gray

# Create base folders
$folders = @(
    "$Base\backend",
    "$Base\backend\modules",
    "$Base\backend\env",
    "$Base\frontend",
    "$Base\tools",
    "$Base\aliases"
)
foreach ($f in $folders) {
    if (-not (Test-Path $f)) {
        New-Item -ItemType Directory -Path $f | Out-Null
        Write-Host "[+] Created $f"
    }
}

# -------------- Python detection --------------
Write-Host "`n[+] Detecting Python interpreter..."
$pythonCandidates = @("py -3", "python", "python3")
$pythonCmd = $null

foreach ($c in $pythonCandidates) {
    try {
        $ver = & $c --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $ver) {
            $pythonCmd = $c
            Write-Host "[=] Using Python: $c -> $ver"
            break
        }
    } catch {
        # ignore
    }
}

if (-not $pythonCmd) {
    Write-Host ""
    Write-Host "ERROR: Nie znaleziono Pythona w systemie." -ForegroundColor Red
    Write-Host "Zainstaluj Python 3 (i zaznacz 'Add to PATH') lub użyj instalatora z Microsoft Store."
    Write-Host "Jeśli chcesz, podam proste polecenia do instalacji. Skrypt przerwany."
    return
}

# Normalize simple command for later invocations (full executable path optional)
function Invoke-Python([string]$arguments) {
    # Use & to run command with args split
    $cmd = $pythonCmd
    & $cmd $arguments
    return $LASTEXITCODE
}

# -------------- Create venv (single project venv) --------------
$VenvPath = Join-Path $Base "backend\env"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "`n[+] Creating Python virtual environment at $VenvPath ..."
    # Use detected python to create venv
    & $pythonCmd -m venv $VenvPath
    Start-Sleep -Milliseconds 700
    if (-not (Test-Path $VenvPython)) {
        Write-Host "ERROR: Nie udało się utworzyć venv. Sprawdź instalację Pythona." -ForegroundColor Red
        return
    } else {
        Write-Host "[✓] venv created."
    }
} else {
    Write-Host "[=] venv already exists at $VenvPath"
}

# -------------- Ensure pip in venv works --------------
Write-Host "`n[+] Ensuring pip (venv python -m pip) is available..."
& $VenvPython -m ensurepip --upgrade 2>&1 | Out-Null
Start-Sleep -Milliseconds 300

# -------------- Create initial requirements if missing --------------
$req = Join-Path $Base "backend\requirements.txt"
if (-not (Test-Path $req)) {
    @"
# Core scraping + API
fastapi
uvicorn
requests
beautifulsoup4

# Optional for future:
pillow
pydantic
"@ | Out-File $req -Encoding UTF8
    Write-Host "[+] Created default requirements.txt"
} else {
    Write-Host "[=] requirements.txt exists"
}

# -------------- Install dependencies using venv python -m pip --------------
Write-Host "`n[+] Installing Python dependencies via venv python -m pip..."
$installCmd = & $VenvPython -m pip install -r $req 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: pip returned non-zero exit code. Output:" -ForegroundColor Yellow
    $installCmd | ForEach-Object { Write-Host $_ }
    Write-Host "Możesz spróbować uruchomić ponownie, lub sprawdzić połączenie internetowe."
} else {
    Write-Host "[✓] Dependencies installed."
}

# -------------- Create local alias file (session-loadable) --------------
$AliasFile = Join-Path $Base "aliases\commands.ps1"
@"
function sca-start-backend {
    & '$VenvPython' '$Base\backend\main_backend.py'
}

function sca-start-backend-uvicorn {
    & '$VenvPython' -m uvicorn backend.main_backend:app --host 127.0.0.1 --port 8000 --reload
}

function sca-shell {
    # Open interactive powershell that inherits venv python on PATH
    Write-Host 'Starting PowerShell inside venv environment...'
    & '$VenvPython' -c `"import os,sys;print('venv python:', sys.executable)`"
    powershell
}

function sca-exit {
    Write-Host 'Closing SpectraCam-AIO session...'
    exit
}
"@ | Out-File $AliasFile -Encoding UTF8

Write-Host "[+] Local alias script written to $AliasFile"

# -------------- Create backend main if missing --------------
$BackendMain = Join-Path $Base "backend\main_backend.py"
if (-not (Test-Path $BackendMain)) {
@"
import importlib
import os
from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def root():
    return {'status': 'SpectraCam-AIO backend active'}

def load_modules():
    modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
    if not os.path.exists(modules_dir):
        os.makedirs(modules_dir)
    for filename in os.listdir(modules_dir):
        if not filename.endswith('.py'): continue
        module_name = filename[:-3]
        module_path = f'backend.modules.{module_name}'
        try:
            mod = importlib.import_module(module_path)
            if hasattr(mod, 'register'):
                mod.register(app)
                print(f'[MODULE] Loaded: {module_name}')
        except Exception as e:
            print(f'[ERROR] Module {module_name}: {e}')

load_modules()
"@ | Out-File $BackendMain -Encoding UTF8
    Write-Host "[+] backend main created."
} else {
    Write-Host "[=] backend main exists"
}

# -------------- Create sample test module if missing --------------
$ModulesDir = Join-Path $Base "backend\modules"
if (-not (Test-Path $ModulesDir)) { New-Item -ItemType Directory -Path $ModulesDir | Out-Null }

$TestModule = Join-Path $ModulesDir "mod_test.py"
if (-not (Test-Path $TestModule)) {
@"
# Simple test module for SpectraCam-AIO
def register(app):
    @app.get('/modules/test')
    def test():
        return {'module':'test','status':'ok'}
"@ | Out-File $TestModule -Encoding UTF8
    Write-Host "[+] test module created."
} else {
    Write-Host "[=] test module exists"
}

# -------------- Load local aliases into current session (non-destructive) --------------
try {
    . $AliasFile
    Write-Host "`n== SpectraCam-AIO ready. ==" -ForegroundColor Green
    Write-Host "Commands:"
    Write-Host "  sca-start-backend        -> run backend (blocking)"
    Write-Host "  sca-start-backend-uvicorn-> run uvicorn on :8000 (dev)"
    Write-Host "  sca-shell               -> open shell (note: plain powershell)"
    Write-Host "  sca-exit                -> quit session"
    Write-Host ""
    Write-Host 'To reload aliases later in any PowerShell session:  . $AliasFile'
} catch {
    Write-Host "Failed to load local aliases: $($_.Exception.Message)" -ForegroundColor Red
}

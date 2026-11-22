# H5N1 / Spectra-AIO launcher (Windows)
$ErrorActionPreference = "Continue"
$BaseDir = $PSScriptRoot
Set-Location $BaseDir

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   Spectra-AIO Command Center" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1) Try to start Tor
$torCandidates = @(
    (Join-Path $BaseDir "tor\tor.exe"),
    (Join-Path $BaseDir "tor.exe"),
    "tor.exe"
)
$torExe = $null
foreach ($c in $torCandidates) { if (Test-Path $c) { $torExe = $c; break } }

if (-not (Get-Process "tor" -ErrorAction SilentlyContinue)) {
    if ($torExe) {
        Write-Host "[*] Starting Tor: $torExe" -ForegroundColor Yellow
        Start-Process -FilePath $torExe -WindowStyle Hidden
        Start-Sleep -Seconds 5
    } else {
        Write-Host "[!] tor.exe not found. Start system Tor manually (SOCKS 9050)." -ForegroundColor Yellow
    }
} else {
    Write-Host "[+] Tor already running." -ForegroundColor Green
}

# 2) Start backend
$backendStarter = Join-Path $BaseDir "run_backend.ps1"
if (-not (Test-Path $backendStarter)) { $backendStarter = Join-Path $BaseDir "run_spectracam.ps1" }
if (Test-Path $backendStarter) {
    Write-Host "[*] Starting backend..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$backendStarter`""
} else {
    Write-Host "[!] No backend launcher found." -ForegroundColor Red
}

Write-Host "`nReady. Example:" -ForegroundColor Cyan
Write-Host "python auto_full_recon.py chaturbate example_user" -ForegroundColor White

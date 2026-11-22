Write-Host "[SpectraCam AIO] Launching Backend..." -ForegroundColor Green

$ProjectRoot = (Resolve-Path -Path $PSScriptRoot).Path
$venvCandidates = @(
    (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
    (Join-Path $ProjectRoot "backend\env\Scripts\python.exe")
)
$VenvPython = $null
foreach ($c in $venvCandidates) { if (Test-Path $c) { $VenvPython = $c; break } }
if (-not $VenvPython) { $VenvPython = "python" }

if (Test-Path (Join-Path $ProjectRoot ".env")) {
    Get-Content (Join-Path $ProjectRoot ".env") | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
        $k,$v = $_ -split '=',2
        if ($k -and $v -and -not [Environment]::GetEnvironmentVariable($k.Trim())) {
            [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim())
        }
    }
}

$hostAddr = if ($env:SPECTRA_HOST) { $env:SPECTRA_HOST } else { "127.0.0.1" }
$port = if ($env:SPECTRA_PORT) { $env:SPECTRA_PORT } else { "8000" }
$Command = "Set-Location '$ProjectRoot'; & '$VenvPython' -m uvicorn backend.main_backend:app --host $hostAddr --port $port"

if (Test-Path (Join-Path $ProjectRoot "aliases\commands.ps1")) {
    . (Join-Path $ProjectRoot "aliases\commands.ps1")
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", $Command
Write-Host "[SpectraCam AIO] Backend is starting in a new window."

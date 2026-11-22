# =========================
# SpectraCam-AIO Launcher (Portable)
# =========================

# DYNAMICZNA ŚCIEŻKA - H5N1_CORE_LOGIC
$BaseDir = $PSScriptRoot
Write-Host "[*] Rozpoczynam w: $BaseDir" -ForegroundColor Green

$Modules = @("YouTube", "Twitch", "Telegram", "Discord")
$AliasFile = Join-Path $BaseDir "aliases.txt"

# Tworzenie katalogów (tylko podkatalogi, BaseDir już istnieje)
foreach ($mod in $Modules) {
    $modPath = Join-Path $BaseDir $mod
    if (!(Test-Path $modPath)) { New-Item -Path $modPath -ItemType Directory }
}

# Tworzenie virtualenv dla każdego modułu
foreach ($mod in $Modules) {
    $venvPath = Join-Path $BaseDir "$mod\venv"
    if (!(Test-Path $venvPath)) {
        python -m venv $venvPath
        Write-Host "Virtualenv created for $mod"
    }
}

# Tworzenie pliku aliasów
if (!(Test-Path $AliasFile)) {
    @"
# SpectraCam-AIO aliases
# Format: <alias>=<module path>
"@ | Out-File $AliasFile -Encoding UTF8
    foreach ($mod in $Modules) {
        $venvActivate = Join-Path $BaseDir "$mod\venv\Scripts\Activate.ps1"
        $aliasLine = "$mod = `"$venvActivate`""
        Add-Content $AliasFile $aliasLine
    }
}

# Funkcje uruchamiania i zamykania modułów
function Start-Module {
    param([string]$ModuleName)
    $venvActivate = Join-Path $BaseDir "$ModuleName\venv\Scripts\Activate.ps1"
    if (Test-Path $venvActivate) {
        Write-Host "Uruchamiam moduł $ModuleName..."
        & $venvActivate
        Write-Host "Moduł $ModuleName aktywny. Wpisz 'deactivate' aby wyjść."
    } else {
        Write-Host "Nie znaleziono modułu $ModuleName."
    }
}

function Stop-Module {
    param([string]$ModuleName)
    Write-Host "Dezaktywacja modułu $ModuleName..."
    deactivate
}

# Menu główne
while ($true) {
    Clear-Host
    Write-Host "=== SpectraCam-AIO Menu ==="
    Write-Host "1) Uruchom moduł"
    Write-Host "2) Dezaktywuj moduł"
    Write-Host "3) Lista modułów"
    Write-Host "4) Wyjście"
    $choice = Read-Host "Wybierz opcję [1-4]"

    switch ($choice) {
        "1" {
            $modName = Read-Host "Podaj nazwę modułu"
            Start-Module -ModuleName $modName
            Pause
        }
        "2" {
            $modName = Read-Host "Podaj nazwę modułu"
            Stop-Module -ModuleName $modName
            Pause
        }
        "3" {
            Write-Host "Dostępne moduły: $($Modules -join ', ')"
            Pause
        }
        "4" {
            break
        }
        default {
            Write-Host "Nieprawidłowa opcja."
            Pause
        }
    }
}

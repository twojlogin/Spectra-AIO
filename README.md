# Spectra-AIO

Lekki, lokalny toolkit OSINT/recon z backendem FastAPI, modułami, **CLI** i prostym **web UI** (bez ciężkich frameworków frontendowych).

> Używaj tylko do legalnych, autoryzowanych badań bezpieczeństwa i analizy własnego śladu cyfrowego.

> 🐱 Kotki. Projekt rozwijany iteracyjnie w długiej sesji roboczej (ponad 10 godzin).

## Co zawiera

- **FastAPI backend** (`backend/main_backend.py`) z dynamicznym ładowaniem modułów z `backend/modules/`
- **Web UI** pod `/ui` (statyczny HTML/CSS/JS, bez React/MUI/builda)
- **CLI** (`cli.py`) na `argparse` + `requests`
- **SQLite** na profile (`backend/db.py`)
- **Tor SOCKS5h** dla modułów sieciowych (konfigurowalne przez env)
- **auto_full_recon.py** - CLI raportu przez API

## Lekkość / bezpieczeństwo

- Brak ciężkiego frontendu (zero npm build, zero React/MUI).
- Minimalne zależności Pythona: FastAPI, uvicorn, requests[socks], bs4, dotenv, aiofiles.
- Domyślnie bind na `127.0.0.1`, CORS ograniczony przez env.
- Podstawowe hardeningi: walidacja inputów, limity rozmiaru avatarów, SSRF guard na avatar URL, retry/backoff dla Wayback.

## Szybki start

Jeden punkt wejścia: `scripts/bootstrap.py` (wykrywa OS/arch/distro/Pythona, sprawdza Tora/proxy, tworzy `.venv`, instaluje deps, robi szybki scan, czyści cache).

### Linux / macOS
```bash
./scripts/bootstrap.sh
./scripts/run.sh
```

### Windows (PowerShell)
```powershell
.\scripts\bootstrap.ps1
.\scripts\run.ps1
```

Backend: `http://127.0.0.1:8000`  
Web UI: `http://127.0.0.1:8000/ui`

## CLI

```bash
source .venv/bin/activate  # Linux
# lub .venv\Scripts\Activate.ps1 na Windows

python cli.py status
python cli.py ui
python cli.py recon chaturbate example_user
python cli.py profiles list
python cli.py profiles add --name "Test" --platform "x" --url "https://example.com"
python cli.py server --host 127.0.0.1 --port 8000
```

## Konfiguracja (.env)

- `SPECTRA_HOST`, `SPECTRA_PORT`
- `SPECTRA_PROXY_MODE` (`tor`/`direct`/`custom`), `SPECTRA_TOR_PROXY`, `SPECTRA_PROXY_URL`
- `SPECTRA_REQUEST_TIMEOUT`
- `SPECTRA_CORS_ORIGINS`
- `SPECTRA_DB_PATH`, `SPECTRA_AVATARS_DIR`

## Ograniczenia

- Wayback ma limity i timeouty - moduł używa retry/backoff i limitów, ale wyniki mogą być niepełne.
- Wyniki OSINT są heurystyczne (możliwe false positive/negative).
- Nie wystawiaj backendu publicznie bez auth/reverse proxy.

## Kontrola techniczna

```bash
python3 -m compileall -q backend cli.py auto_full_recon.py scripts/bootstrap.py
PYTHONPATH=. .venv/bin/python -c "import backend.main_backend, cli, auto_full_recon; print('OK')"
```

## Struktura

```text
backend/
  main_backend.py
  db.py
  requirements.txt
  static/          # lekki web UI
  modules/         # moduły OSINT
  utils/
cli.py
auto_full_recon.py
setup.sh / setup.ps1
run_backend.sh / run_backend.ps1
```

## Historia kotkowa

- 🐱 **Kot 1**: obudził się w repo i zobaczył bałagan po starych skryptach.
- 🐱 **Kot 2**: przyniósł lekki UI, CLI i bootstrap, żeby wszystko dało się odpalić.
- 🐱 **Kot 3**: wyrzucił ciężkie śmieci, ogarnął proxy `direct/tor/custom` i posprzątał ścieżki.
- 🐱 **Kot 4**: dodał `reason` do sprawdzania loginów, żeby nie miauczeć „FOUND” bez dowodu.
- 🐱 **Kot 5**: zmienił kolory pod nastrój, dodał pulsowanie i zostawił ślad łapki w README.

> Napisane kotkowo przy udziale modelu AI Iceman Free (OpenCode).

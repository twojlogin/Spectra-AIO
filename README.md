# Spectra-AIO

Lekki, lokalny toolkit OSINT/recon z backendem FastAPI, modułami, **CLI** i prostym **web UI** (bez ciężkich frameworków frontendowych).

> Używaj tylko do legalnych, autoryzowanych badań bezpieczeństwa i analizy własnego śladu cyfrowego.

> 🐱 Kotki. Projekt rozwijany iteracyjnie w długiej sesji roboczej (ponad 10 godzin).

## Co zawiera

- **FastAPI backend** (`backend/main_backend.py`) - dynamiczne ładowanie modułów z `backend/modules/`, endpointy `/health`, `/api/stats`, `/api/network/status`, profile i recon.
- **Web UI** pod `/ui` - statyczny HTML/CSS/JS, bez React/MUI/builda; panel statusu/proxy.
- **CLI** (`cli.py`) na `argparse` + `requests` oraz `auto_full_recon.py` do raportu przez API.
- **SQLite** na profile (`backend/db.py`), lokalny plik DB poza gitem.
- **Proxy**: `SPECTRA_PROXY_MODE=tor|direct|custom` + obsługa SOCKS5h/URL proxy; tryb `direct` bez Tora.
- **Skrypty**: `scripts/bootstrap.*` (wykrycie OS/Pythona, venv, deps, szybki check) i `scripts/run.*`.
- **Kontrola**: compileall + smoke import (sekcja poniżej).

## Lekkość / bezpieczeństwo

- Brak ciężkiego frontendu (zero npm build, zero React/MUI).
- Minimalne zależności Pythona: FastAPI, uvicorn, requests[socks], bs4, dotenv, aiofiles.
- Domyślnie bind na `127.0.0.1`, CORS ograniczony przez env.
- Podstawowe hardeningi w jądrze: walidacja inputów, bezpieczniejsze domyślne CORS/bind, limit/throttling checków sieciowych.

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
python cli.py profiles list
python cli.py profiles add --name "Test" --platform "x" --url "https://example.com"
python cli.py server --host 127.0.0.1 --port 8000
# python cli.py recon <site> <username>  # wymaga włączonych modułów OSINT w backend/modules/
```

## Konfiguracja (.env)

- `SPECTRA_HOST`, `SPECTRA_PORT`
- `SPECTRA_PROXY_MODE` (`tor`/`direct`/`custom`), `SPECTRA_TOR_PROXY`, `SPECTRA_PROXY_URL`
- `SPECTRA_REQUEST_TIMEOUT`
- `SPECTRA_CORS_ORIGINS`
- `SPECTRA_DB_PATH`, `SPECTRA_AVATARS_DIR`

## Ograniczenia

- Moduły OSINT są obecnie wyłączone (`backend/modules/_disabled/`) - rdzeń działa, recon/moduły wymagają świadomego włączenia i weryfikacji.
- Wyniki OSINT są heurystyczne (możliwe false positive/negative).
- Nie wystawiaj backendu publicznie bez auth/reverse proxy.

## Szybka kontrola (czy wszystko działa)

Uruchom te dwie komendy w katalogu projektu:

```bash
# 1) Sprawdza, czy pliki Pythona nie mają błędów składni
python3 -m compileall -q backend cli.py auto_full_recon.py scripts/bootstrap.py

# 2) Sprawdza, czy główne pliki da się zaimportować
PYTHONPATH=. .venv/bin/python -c "import backend.main_backend, cli, auto_full_recon; print('OK')"
```

Jeśli nie ma błędu i druga komenda wypisze `OK`, podstawy projektu działają.

## Struktura

```text
backend/
  main_backend.py
  db.py
  requirements.txt
  static/          # lekki web UI
  modules/         # aktywne moduły (obecnie puste), _disabled/ dla wyłączonych
  utils/
scripts/           # bootstrap/run
cli.py
auto_full_recon.py
DOCS.md
SECURITY.md
```

## Historia kotkowa

- 🐱 **Kot 1**: obudził się w repo i zobaczył bałagan po starych skryptach.
- 🐱 **Kot 2**: przyniósł lekki UI, CLI i bootstrap - wyglądało, że wszystko działa.
- 🐱 **Kot 3**: posprzątał część śmieci i proxy, ale pod dywanem zostały dziury.
- 🐱 **Kot 4**: dostał mleczko, ale miał nietolerancję laktozy - poprawki wyglądały lepiej, niż działały.
- 🐱 **Kot 5**: dopiero po twardym sprzątaniu, wyłączeniu modułów i audycie jądro zaczęło wyglądać uczciwie.

> Napisane kotkowo przy udziale modelu AI Iceman Free (OpenCode).

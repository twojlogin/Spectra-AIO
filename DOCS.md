# Dokumentacja techniczna - Spectra-AIO

## Wymagania
- Python 3.10+
- pip / venv
- (opcjonalnie) Tor lub własny proxy

## Instalacja i uruchomienie

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

Domyślnie: `http://127.0.0.1:8000` (UI: `/ui`).

## Konfiguracja (.env)
- `SPECTRA_HOST`, `SPECTRA_PORT` - adres/port backendu
- `SPECTRA_PROXY_MODE` - `tor` | `direct` | `custom`
- `SPECTRA_TOR_PROXY` - np. `socks5h://127.0.0.1:9050`
- `SPECTRA_PROXY_URL` - URL proxy dla trybu `custom`
- `SPECTRA_REQUEST_TIMEOUT` - timeout requestów (s)
- `SPECTRA_CORS_ORIGINS` - dozwolone originy (CSV)
- `SPECTRA_DB_PATH`, `SPECTRA_AVATARS_DIR` - ścieżki danych

## Główne endpointy
- `GET /health` - status
- `GET /api/stats` - statystyki/moduły/profile/proxy
- `GET /api/network/status` - konfiguracja sieci/proxy
- `GET /api/profiles` - lista profili
- `POST /api/profiles/add` - dodanie profilu (parametry: name, platform, url, description, metadata)
- `GET /osint/check-user/{username}` - sprawdzenie loginu (Reddit, GitLab) z `status/reason`

## Moduły
Moduły są ładowane dynamicznie z `backend/modules/`. Moduły wyłączone można trzymać w `backend/modules/_disabled/`.

## Bezpieczeństwo
- Nie wystawiaj publicznie bez auth/reverse proxy.
- Nie commituj `.env`, kluczy, baz lokalnych.
- Wyniki OSINT traktuj jako heurystyczne - weryfikuj ręcznie.

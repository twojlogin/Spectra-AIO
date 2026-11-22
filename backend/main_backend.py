"""Spectra-AIO FastAPI backend."""

from __future__ import annotations

import importlib
import logging
import os
import re
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure repo root is importable when started from different working dirs.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except Exception:
    # python-dotenv is optional at runtime; env vars still work.
    pass

from backend.db import add_profile, get_all_profiles, init_db  # noqa: E402
from backend.utils.tor_client import get_tor_session, tor_proxy_config, tor_unavailable_message  # noqa: E402

logging.basicConfig(level=os.getenv("SPECTRA_LOG_LEVEL", "INFO").upper())
logger = logging.getLogger("spectra")

# Simple in-memory cooldown for network checks (per client IP)
_NETWORK_CHECK_COOLDOWN_S = 10.0
_network_check_last: dict[str, float] = {}


def _parse_origins(value: str | None) -> list[str]:
    if not value:
        return ["http://127.0.0.1:3000", "http://localhost:3000"]
    origins = [o.strip() for o in value.split(",") if o.strip()]
    return origins or ["http://127.0.0.1:3000", "http://localhost:3000"]


def load_modules(app: FastAPI) -> list[str]:
    modules_dir = Path(__file__).resolve().parent / "modules"
    modules_dir.mkdir(parents=True, exist_ok=True)
    loaded: list[str] = []

    for file in sorted(modules_dir.glob("*.py")):
        if file.name.startswith("_"):
            continue
        module_name = file.stem
        module_path = f"backend.modules.{module_name}"
        try:
            mod = importlib.import_module(module_path)
            register = getattr(mod, "register", None)
            if callable(register):
                register(app)
                loaded.append(module_name)
                logger.info("Loaded module: %s", module_name)
            else:
                logger.debug("Skipped module without register(): %s", module_name)
        except Exception:
            logger.exception("Failed to load module: %s", module_name)
    return loaded


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    app.state.loaded_modules = load_modules(app)
    logger.info("Spectra-AIO backend started. Modules: %s", app.state.loaded_modules)
    yield


app = FastAPI(title="SpectraCam-AIO Backend", version="1.1.0", lifespan=lifespan)

origins = _parse_origins(os.getenv("SPECTRA_CORS_ORIGINS"))
allow_credentials = os.getenv("SPECTRA_CORS_CREDENTIALS", "false").lower() == "true"
# Browsers reject wildcard origin with credentials; enforce safe behavior.
if "*" in origins:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/ui/static", StaticFiles(directory=str(STATIC_DIR)), name="ui-static")


@app.get("/ui")
def ui_index():
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(str(index))


class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    platform: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=2000)
    metadata: dict | str | None = None


SAFE_TEXT_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean_text(value: str, max_len: int) -> str:
    value = SAFE_TEXT_RE.sub("", (value or "")).strip()
    return value[:max_len]


@app.get("/")
def root():
    return {
        "status": "SpectraCam-AIO backend active",
        "version": app.version,
        "modules": getattr(app.state, "loaded_modules", []),
        "ui": "/ui",
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/stats")
def stats():
    return {
        "ok": True,
        "version": app.version,
        "modules": getattr(app.state, "loaded_modules", []),
        "module_count": len(getattr(app.state, "loaded_modules", [])),
        "profiles_count": len(get_all_profiles()),
        "tor": tor_proxy_config(),
    }


@app.get("/api/tor/status")
@app.get("/api/network/status")
def tor_status(request: Request, check: bool = Query(False)):
    cfg = tor_proxy_config()
    result = {"config": cfg, "ok": True}
    if not check:
        return result

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    last = _network_check_last.get(client_ip, 0.0)
    if now - last < _NETWORK_CHECK_COOLDOWN_S:
        retry_after = int(_NETWORK_CHECK_COOLDOWN_S - (now - last)) + 1
        return {"config": cfg, "ok": False, "check": {"ok": False, "error": "rate_limited", "message": f"Poczekaj {retry_after}s przed kolejnym sprawdzeniem.", "retry_after_s": retry_after}}
    _network_check_last[client_ip] = now

    mode = cfg.get("mode", "tor")
    if mode == "direct":
        result["check"] = {"ok": True, "mode": "direct", "message": "Tryb direct: requesty bez proxy."}
        try:
            s = get_tor_session(timeout=10)
            r = s.get("https://api.ipify.org?format=json", timeout=10)
            if r.status_code == 200:
                result["check"]["ip_info"] = r.json()
        except Exception as e:
            logger.warning("Direct network check failed: %s", e)
            result["check"]["ip_error"] = "check_failed"
        return result

    try:
        s = get_tor_session(timeout=10)
        r = s.get("https://check.torproject.org/api/ip", timeout=12)
        r.raise_for_status()
        data = r.json()
        is_tor = bool(data.get("IsTor"))
        msg = "Połączenie przez Tor OK." if is_tor else "Połączenie przez proxy działa, ale Tor check zwraca IsTor=false (to może być zwykły VPN/custom proxy)."
        result["check"] = {"ok": True, "mode": mode, "ip_info": data, "is_tor": is_tor, "message": msg}
    except Exception as e:
        logger.warning("Network check failed (%s): %s", mode, e)
        result["ok"] = False
        result["check"] = {"ok": False, "mode": mode, "error": "check_failed", "message": tor_unavailable_message(e)}
    return result


@app.get("/api/profiles")
def list_profiles():
    return get_all_profiles()


@app.post("/api/profiles/add")
def save_profile(profile: ProfileCreate):
    name = _clean_text(profile.name, 200)
    platform = _clean_text(profile.platform, 100)
    url = _clean_text(profile.url, 500)
    description = _clean_text(profile.description, 2000)
    if not (name and platform and url):
        raise HTTPException(status_code=400, detail="name, platform, url are required")
    if not re.match(r"^https?://", url, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="url must start with http:// or https://")
    success = add_profile(name=name, platform=platform, url=url, description=description, metadata=profile.metadata)
    if not success:
        raise HTTPException(status_code=400, detail="Profile already exists or invalid data.")
    return {"status": "ok", "message": f"Added: {name} ({platform})"}


# Legacy query-param endpoint kept for backward compatibility with existing scripts/UI.
@app.post("/api/profiles/add_legacy")
def save_profile_legacy(
    name: str = Query(..., min_length=1, max_length=200),
    platform: str = Query(..., min_length=1, max_length=100),
    url: str = Query(..., min_length=1, max_length=500),
    description: str = Query("", max_length=2000),
):
    return save_profile(ProfileCreate(name=name, platform=platform, url=url, description=description))


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("SPECTRA_HOST", "127.0.0.1")
    port = int(os.getenv("SPECTRA_PORT", "8000"))
    uvicorn.run("backend.main_backend:app", host=host, port=port, reload=False)

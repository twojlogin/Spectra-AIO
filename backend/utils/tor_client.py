"""HTTP session helpers with configurable proxy routing.

Env:
- SPECTRA_PROXY_MODE: tor (default) | direct | custom
- SPECTRA_USE_TOR: backward-compat bool; if 0 and no PROXY_MODE, mode=direct
- SPECTRA_TOR_PROXY / SPECTRA_PROXY_URL: proxy URL (socks5h://..., socks5://..., http://...)
- SPECTRA_TOR_HOST / SPECTRA_TOR_PORT: tor host/port fallback
- SPECTRA_USER_AGENT, SPECTRA_REQUEST_TIMEOUT
"""

from __future__ import annotations

import os
from typing import Optional

import requests

DEFAULT_TOR_HOST = "127.0.0.1"
DEFAULT_TOR_PORT = "9050"
DEFAULT_TIMEOUT = 15.0
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
TOR_DOWNLOAD_URL = "https://www.torproject.org/download/"
PROTON_VPN_URL = "https://protonvpn.com/download"
WARP_URL = "https://one.one.one.one/"


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_proxy_mode() -> str:
    mode = (os.getenv("SPECTRA_PROXY_MODE") or "").strip().lower()
    if mode in {"tor", "direct", "custom"}:
        return mode
    # backward compat
    if not _env_bool("SPECTRA_USE_TOR", True):
        return "direct" if not os.getenv("SPECTRA_PROXY_URL") else "custom"
    return "tor"


def tor_enabled() -> bool:
    return get_proxy_mode() == "tor"


def get_proxy_url() -> str | None:
    mode = get_proxy_mode()
    if mode == "direct":
        return None
    proxy = os.getenv("SPECTRA_PROXY_URL") or os.getenv("SPECTRA_TOR_PROXY")
    if proxy and proxy.strip():
        return proxy.strip()
    host = os.getenv("SPECTRA_TOR_HOST", DEFAULT_TOR_HOST).strip()
    port = os.getenv("SPECTRA_TOR_PORT", DEFAULT_TOR_PORT).strip()
    return f"socks5h://{host}:{port}"


# Backward-compatible name
def get_tor_proxy_url() -> str:
    return get_proxy_url() or ""


def get_default_timeout() -> float:
    return _env_float("SPECTRA_REQUEST_TIMEOUT", DEFAULT_TIMEOUT)


def get_user_agent() -> str:
    return os.getenv("SPECTRA_USER_AGENT", DEFAULT_USER_AGENT).strip() or DEFAULT_USER_AGENT


def proxy_unavailable_message(err: Exception | str | None = None) -> str:
    mode = get_proxy_mode()
    proxy = get_proxy_url()
    detail = f" ({err})" if err else ""
    if mode == "direct":
        return f"Direct connection failed{detail}."
    if mode == "tor":
        return (
            f"Tor/proxy unavailable at {proxy}{detail}. "
            f"Start Tor or install: {TOR_DOWNLOAD_URL} . "
            "Alternatives: Proton VPN ({PROTON_VPN_URL}) or Cloudflare WARP ({WARP_URL}) - configure as SOCKS/HTTP proxy and set SPECTRA_PROXY_MODE=custom + SPECTRA_PROXY_URL=... "
            "Or set SPECTRA_PROXY_MODE=direct (less private)."
        )
    return (
        f"Custom proxy unavailable at {proxy}{detail}. "
        "Check SPECTRA_PROXY_URL / VPN app proxy settings. "
        f"Tor option: {TOR_DOWNLOAD_URL}"
    )


# Backward-compatible name
def tor_unavailable_message(err: Exception | str | None = None) -> str:
    return proxy_unavailable_message(err)


def get_tor_session(timeout: Optional[float] = None) -> requests.Session:
    """Return requests session using configured proxy mode."""
    session = requests.Session()
    proxy = get_proxy_url()
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    session.headers.update(
        {
            "User-Agent": get_user_agent(),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    session.default_timeout = get_default_timeout() if timeout is None else float(timeout)
    return session


def tor_proxy_config() -> dict:
    mode = get_proxy_mode()
    return {
        "mode": mode,
        "enabled": mode != "direct",
        "proxy": get_proxy_url(),
        "timeout": get_default_timeout(),
        "user_agent": get_user_agent(),
        "download_url": TOR_DOWNLOAD_URL,
        "alternatives": [
            {"name": "Proton VPN", "url": PROTON_VPN_URL, "note": "Może udostępniać lokalny proxy/VPN; ustaw jako custom proxy jeśli dostępny."},
            {"name": "Cloudflare WARP", "url": WARP_URL, "note": "Klient WARP; dla trybu proxy ustaw SPECTRA_PROXY_MODE=custom i SPECTRA_PROXY_URL."},
            {"name": "Direct (no proxy)", "url": "", "note": "SPECTRA_PROXY_MODE=direct - mniej prywatne, ale bez Tora."},
        ],
    }

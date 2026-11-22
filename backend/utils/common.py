"""Shared helpers for Spectra-AIO modules."""

from __future__ import annotations

import os
import re
import time
from typing import Any, Callable

import requests

try:
    from backend.utils.tor_client import get_proxy_mode, tor_unavailable_message
except Exception:  # pragma: no cover
    def get_proxy_mode() -> str: return "tor"
    def tor_unavailable_message(err=None) -> str: return f"Proxy unavailable: {err}"


SAFE_HANDLE_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def sanitize_handle(value: str) -> str:
    value = (value or "").strip()
    if not SAFE_HANDLE_RE.match(value):
        # Be permissive but safe: strip dangerous chars, keep reasonable length.
        value = re.sub(r"[^A-Za-z0-9._-]+", "", value)[:64]
    return value


def env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    try:
        return float(v)
    except ValueError:
        return default


def request_with_retry(
    session: requests.Session,
    method: str,
    url: str,
    *,
    timeout: float | None = None,
    retries: int = 2,
    backoff: float = 0.8,
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
    **kwargs: Any,
) -> requests.Response:
    last_exc: Exception | None = None
    timeout = timeout if timeout is not None else getattr(session, "default_timeout", 15)
    for attempt in range(retries + 1):
        try:
            resp = session.request(method, url, timeout=timeout, **kwargs)
            if resp.status_code in retry_statuses and attempt < retries:
                sleep_for = backoff * (2 ** attempt)
                ra = resp.headers.get("Retry-After")
                if ra and ra.isdigit():
                    sleep_for = max(sleep_for, float(ra))
                time.sleep(min(sleep_for, 8.0))
                continue
            return resp
        except requests.exceptions.ProxyError as e:
            # Clear message when Tor/SOCKS proxy is missing.
            raise requests.exceptions.ConnectionError(tor_unavailable_message(e)) from e
        except requests.RequestException as e:
            last_exc = e
            msg = str(e).lower()
            if get_proxy_mode() != "direct" and ("connection refused" in msg or "failed to establish a new connection" in msg) and ("socks" in msg or "proxy" in msg):
                raise requests.exceptions.ConnectionError(tor_unavailable_message(e)) from e
            if attempt >= retries:
                raise
            time.sleep(min(backoff * (2 ** attempt), 8.0))
    assert last_exc is not None
    raise last_exc

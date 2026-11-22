from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session

MAX_AVATAR_BYTES = int(os.getenv("SPECTRA_AVATAR_MAX_BYTES", str(5 * 1024 * 1024)))
ALLOWED_IMAGE_CT = ("image/jpeg", "image/png", "image/webp", "image/gif", "image/jpg")


def _safe_filename(site: str, username: str) -> str:
    site = re.sub(r"[^A-Za-z0-9._-]+", "_", (site or "").strip())[:40] or "site"
    user = sanitize_handle(username) or "user"
    return f"{site}_{user}.jpg"


def _is_allowed_avatar_url(url: str) -> bool:
    try:
        p = urlparse(url)
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = (p.hostname or "").lower()
    if not host:
        return False
    # Block obvious local/internal targets.
    if host in {"localhost", "127.0.0.1", "::1"}:
        return False
    if host.endswith(".local") or host.endswith(".internal"):
        return False
    # Block private IPv4 literals
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", host)
    if m:
        octets = [int(x) for x in m.groups()]
        if any(o > 255 for o in octets):
            return False
        a, b, *_ = octets
        if a in (10, 127, 0) or (a == 169 and b == 254) or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168):
            return False
    return True


def analyze_avatar(site: str, username: str, avatar_url: str) -> dict:
    session = get_tor_session()
    site_clean = sanitize_handle(site) or "site"
    user_clean = sanitize_handle(username)
    if not user_clean:
        return {"error": "Invalid username"}
    if not avatar_url or not _is_allowed_avatar_url(avatar_url):
        return {"error": "Invalid or disallowed avatar_url"}

    avatars_dir = Path(os.getenv("SPECTRA_AVATARS_DIR", Path(__file__).resolve().parents[1] / "avatars"))
    avatars_dir.mkdir(parents=True, exist_ok=True)
    file_path = avatars_dir / _safe_filename(site_clean, user_clean)

    try:
        r = request_with_retry(session, "GET", avatar_url, retries=1, stream=True)
        if r.status_code != 200:
            return {"error": "Avatar fetch failed", "status_code": r.status_code}

        ct = (r.headers.get("Content-Type") or "").lower().split(";")[0].strip()
        if ct and not any(ct.startswith(a) for a in ALLOWED_IMAGE_CT):
            return {"error": "URL does not look like an image", "content_type": ct}

        content = bytearray()
        for chunk in r.iter_content(chunk_size=8192):
            if not chunk:
                continue
            content.extend(chunk)
            if len(content) > MAX_AVATAR_BYTES:
                return {"error": "Avatar too large", "limit_bytes": MAX_AVATAR_BYTES}

        file_path.write_bytes(bytes(content))
        img_hash = hashlib.sha256(content).hexdigest()
        reverse_links = {
            "Yandex": f"https://yandex.com/images/search?url={avatar_url}&rpt=imageview",
            "GoogleLens": f"https://lens.google.com/uploadbyurl?url={avatar_url}",
        }
        return {
            "username": user_clean,
            "site": site_clean,
            "avatar_sha256": img_hash,
            "local_path": str(file_path),
            "content_type": ct or "unknown",
            "bytes": len(content),
            "reverse_search_ready": reverse_links,
        }
    except Exception as e:
        return {"error": str(e)}


def register(app):
    @app.get("/osint/avatar-check/{site}/{username}")
    def api_avatar(site: str, username: str, avatar_url: str):
        return analyze_avatar(site, username, avatar_url)

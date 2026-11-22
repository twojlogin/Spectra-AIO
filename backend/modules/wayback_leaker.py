from __future__ import annotations

import re

from backend.modules.cam_mapper import extract_socials
from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session


def extract_ghosts(text: str) -> dict[str, list[str]]:
    patterns = {
        "Email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "Skype": r"skype:\s*([A-Za-z0-9._-]+)",
    }
    found: dict[str, list[str]] = {}
    for label, regex in patterns.items():
        matches = re.findall(regex, text or "", re.IGNORECASE)
        if not matches:
            continue
        # re.findall with group returns group strings; normalize
        if matches and isinstance(matches[0], tuple):
            flat = [m[0] for m in matches if m and m[0]]
        else:
            flat = [m for m in matches if isinstance(m, str)]
        cleaned = sorted({m.strip() for m in flat if m and m.strip()})
        if cleaned:
            found[label] = cleaned
    return found


def scan_historical_leaks(site: str, username: str, limit: int = 5) -> dict:
    session = get_tor_session()
    site = (site or "").strip().lower()
    username = sanitize_handle(username)
    if not username:
        return {"error": "Invalid username"}

    targets = {
        "chaturbate": f"chaturbate.com/{username}/",
        "mfc": f"profiles.myfreecams.com/{username}",
    }
    if site not in targets:
        return {"error": "Unsupported site", "supported_sites": sorted(targets.keys())}

    target_url = targets[site]
    # Filter to HTML and successful snapshots; collapse to reduce duplicates.
    cdx_url = (
        "https://web.archive.org/cdx/search/cdx"
        f"?url={target_url}&output=json&fl=timestamp,original,statuscode,mimetype"
        "&filter=statuscode:200&filter=mimetype:text/html"
        "&collapse=timestamp:6"
        f"&limit={max(1, min(int(limit), 20))}"
    )

    try:
        r_cdx = request_with_retry(session, "GET", cdx_url, retries=3, backoff=1.0)
        if r_cdx.status_code != 200:
            return {"error": "WAYBACK_CDX_ERROR", "status_code": r_cdx.status_code}
        try:
            snapshots = r_cdx.json()
        except Exception:
            return {"error": "WAYBACK_CDX_INVALID_JSON"}
        if not isinstance(snapshots, list) or len(snapshots) <= 1:
            return {"status": "NO_HISTORY", "target": username, "site": site}

        rows = snapshots[1:]  # skip header
        # Pick a small sample: oldest and newest among returned rows
        sample = [rows[0]]
        if len(rows) > 1 and rows[-1] != rows[0]:
            sample.append(rows[-1])

        all_leaks: dict[str, set[str]] = {}
        fetched = 0
        for snap in sample:
            if not isinstance(snap, list) or len(snap) < 2:
                continue
            ts = str(snap[0])
            orig = str(snap[1])
            raw_url = f"https://web.archive.org/web/{ts}id_/{orig}"
            r_snap = request_with_retry(session, "GET", raw_url, retries=2, backoff=1.0)
            fetched += 1
            if r_snap.status_code != 200:
                continue
            ghosts = extract_ghosts(r_snap.text)
            socials = extract_socials(r_snap.text)
            for label, items in {**ghosts, **socials}.items():
                if not items:
                    continue
                all_leaks.setdefault(label, set()).update(items)

        return {
            "target": username,
            "site": site,
            "history_depth": len(rows),
            "snapshots_fetched": fetched,
            "leaks_discovered": {k: sorted(v) for k, v in all_leaks.items()},
        }
    except Exception as e:
        return {"error": str(e), "target": username, "site": site}


def register(app):
    @app.get("/osint/ghost-scan/{site}/{username}")
    def api_ghost(site: str, username: str, limit: int = 5):
        return scan_historical_leaks(site, username, limit=limit)

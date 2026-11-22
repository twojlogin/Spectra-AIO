from __future__ import annotations

import time

from backend.modules.wayback_leaker import scan_historical_leaks
from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session


def check_email_leak(session, email: str) -> dict | None:
    """Best-effort check against a public leak-lookup endpoint.

    This is optional and may be unavailable/rate-limited; failures are non-fatal.
    """
    url = f"https://leak-lookup.com/api/search?type=email_address&query={email}"
    try:
        r = request_with_retry(session, "GET", url, retries=1, backoff=1.0)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("error") == "false" and data.get("message"):
            return data.get("message")
    except Exception:
        return None
    return None


def register(app):
    @app.get("/osint/master-recon/{site}/{username}")
    def master_recon(site: str, username: str):
        session = get_tor_session()
        site = (site or "").strip().lower()
        username = sanitize_handle(username)
        if not username:
            return {"error": "Invalid username"}

        history = scan_historical_leaks(site, username)
        if not isinstance(history, dict):
            return {"error": "Unexpected history response"}
        if "error" in history or history.get("status") == "NO_HISTORY":
            return history

        emails = history.get("leaks_discovered", {}).get("Email", []) or []
        leaks_report = {}

        for email in emails[:10]:  # cap to avoid long blocking requests
            found_leaks = check_email_leak(session, email)
            if found_leaks:
                leaks_report[email] = found_leaks
            time.sleep(0.5)

        return {
            "target": username,
            "platform": site,
            "emails_found": emails,
            "pwned_leaks": leaks_report,
            "verdict": "POTENTIAL_LEAKS_FOUND" if leaks_report else "NO_LEAKS_DETECTED",
            "note": "Leak lookup is best-effort and may be incomplete.",
        }

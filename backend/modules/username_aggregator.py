from __future__ import annotations

import re
from urllib.parse import quote_plus

from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session


# Keep this small and honest. Better fewer reliable checks than many noisy ones.
PLATFORMS = [
    {
        "name": "Reddit",
        "url": "https://www.reddit.com/user/{u}/about.json",
        "json_found_key": "name",
        "json_not_found": [404, "404", "not found"],
    },
    {
        "name": "GitLab",
        "url": "https://gitlab.com/{u}",
        "not_found_markers": ["page not found", "the page could not be found"],
        "found_markers": ["@{u}", "personal projects", "activity"],
    },
]


def _status_from_response(resp, platform: dict, username: str) -> tuple[str, str]:
    code = resp.status_code
    body = resp.text or ""
    body_l = body.lower()
    url_l = (resp.url or "").lower()

    if code == 404:
        return "NOT_FOUND", "http_404"
    if code in {429, 403}:
        return "BLOCKED", f"http_{code}"
    if code >= 500:
        return f"ERROR_{code}", f"http_{code}"
    if "captcha" in body_l or "verify you are human" in body_l:
        return "BLOCKED_OR_LOGIN", "captcha_detected"
    if "/login" in url_l and code == 200:
        return "BLOCKED_OR_LOGIN", "redirected_to_login"

    # JSON-specific (Reddit about.json, GitHub API, etc.)
    if platform.get("json_found_key") or platform.get("json_found_any"):
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "json" in ctype or body_l.lstrip().startswith("{"):
            try:
                data = resp.json()
            except Exception:
                return "UNKNOWN", "json_parse_error"
            if isinstance(data, dict) and "error" in data:
                if data.get("error") == 404:
                    return "NOT_FOUND", "json_error_404"
                return "UNKNOWN", f"json_error_{data.get('error')}"
            if isinstance(data, dict) and str(data.get("message", "")).lower() == "not found":
                return "NOT_FOUND", "json_message_not_found"
            # Reddit-like: data.name
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
                if data["data"].get("name"):
                    return "FOUND", "json_user_found"
            # GitHub-like: top-level login/id
            for k in platform.get("json_found_any", []):
                if isinstance(data, dict) and data.get(k):
                    return "FOUND", f"json_found:{k}"
            if platform.get("json_found_key") and isinstance(data, dict) and data.get(platform["json_found_key"]):
                return "FOUND", "json_user_found"
            return "UNKNOWN", "json_no_user_field"
        return "UNKNOWN", "expected_json"

    not_found_markers = [m.lower().format(u=username.lower()) for m in platform.get("not_found_markers", [])]
    found_markers = [m.lower().format(u=username.lower()) for m in platform.get("found_markers", [])]

    for m in not_found_markers:
        if m in body_l:
            return "NOT_FOUND", f"marker_not_found:{m[:40]}"
    for m in found_markers:
        if m in body_l:
            return "FOUND", f"marker_found:{m[:40]}"

    if code == 200:
        return "UNKNOWN", "http_200_no_strong_marker"
    return f"ERROR_{code}", f"http_{code}"


def register(app):
    @app.get("/osint/check-user/{username}")
    def check_user_global(username: str):
        """Check username presence on a small set of platforms with honest statuses."""
        username = sanitize_handle(username)
        if not username:
            return {"error": "Invalid username"}

        session = get_tor_session()
        results = []
        for p in PLATFORMS:
            url = p["url"].format(u=username)
            try:
                headers = {"Accept": "application/json,text/html;q=0.9,*/*;q=0.8"}
                if p["name"] == "Reddit":
                    headers["Accept"] = "application/json"
                    headers["User-Agent"] = "Spectra-AIO/1.1 (username-check)"
                resp = request_with_retry(session, "GET", url, retries=1, headers=headers)
                status, reason = _status_from_response(resp, p, username)
                results.append({
                    "platform": p["name"],
                    "url": url,
                    "status": status,
                    "reason": reason,
                    "http_status": resp.status_code,
                })
            except Exception as e:
                results.append({
                    "platform": p["name"],
                    "url": url,
                    "status": "CONNECTION_ERROR",
                    "reason": "connection_error",
                    "error": str(e),
                })

        q = quote_plus(username)
        search_links = [
            {"name": "Google", "url": f"https://www.google.com/search?q=%22{q}%22", "status": "MANUAL"},
            {"name": "DuckDuckGo", "url": f"https://duckduckgo.com/?q=%22{q}%22", "status": "MANUAL"},
        ]
        return {
            "username": username,
            "results": results,
            "search_links": search_links,
            "note": "Statuses are conservative: FOUND/NOT_FOUND/BLOCKED/UNKNOWN. MANUAL links are for human verification only.",
        }

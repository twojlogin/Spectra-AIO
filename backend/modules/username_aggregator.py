from __future__ import annotations

import re

from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session


# Keep this small and honest. Better fewer reliable checks than many noisy ones.
PLATFORMS = [
    {
        "name": "GitHub",
        "url": "https://github.com/{u}",
        "not_found_markers": ["not found", "this is not the web page you are looking for"],
        "found_markers": ["repositories", "followers", "following", "p-nickname"],
    },
    {
        "name": "Reddit",
        "url": "https://www.reddit.com/user/{u}/about.json",
        "json_found_key": "name",
        "json_not_found": ["404", "not found"],
    },
    {
        "name": "GitLab",
        "url": "https://gitlab.com/{u}",
        "not_found_markers": ["page not found", "the page could not be found"],
        "found_markers": ["@{u}", "personal projects", "activity"],
    },
]


def _status_from_response(name: str, resp, platform: dict, username: str) -> str:
    code = resp.status_code
    body = resp.text or ""
    body_l = body.lower()
    url_l = (resp.url or "").lower()

    if code == 404:
        return "NOT_FOUND"
    if code in {429, 403}:
        return "BLOCKED"
    if code >= 500:
        return f"ERROR_{code}"
    if "captcha" in body_l or "verify you are human" in body_l or "/login" in url_l:
        return "BLOCKED_OR_LOGIN"

    # JSON-specific (Reddit about.json)
    if platform.get("json_found_key"):
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "json" in ctype or body_l.lstrip().startswith("{"):
            try:
                data = resp.json()
            except Exception:
                return "UNKNOWN"
            if isinstance(data, dict) and "error" in data:
                if data.get("error") == 404:
                    return "NOT_FOUND"
                return "UNKNOWN"
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
                if data["data"].get("name"):
                    return "FOUND"
            return "UNKNOWN"
        return "UNKNOWN"

    not_found_markers = [m.lower().format(u=username.lower()) for m in platform.get("not_found_markers", [])]
    found_markers = [m.lower().format(u=username.lower()) for m in platform.get("found_markers", [])]

    if any(m in body_l for m in not_found_markers):
        return "NOT_FOUND"
    if any(m in body_l for m in found_markers):
        return "FOUND"

    # 200 without strong markers is not reliable enough.
    if code == 200:
        return "UNKNOWN"
    return f"ERROR_{code}"


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
                resp = request_with_retry(session, "GET", url, retries=1, headers=headers)
                status = _status_from_response(p["name"], resp, p, username)
                results.append({"platform": p["name"], "url": url, "status": status, "http_status": resp.status_code})
            except Exception as e:
                results.append({"platform": p["name"], "url": url, "status": "CONNECTION_ERROR", "error": str(e)})
        return {"username": username, "results": results, "note": "Statuses are conservative: FOUND/NOT_FOUND/BLOCKED/UNKNOWN."}

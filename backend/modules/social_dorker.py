from __future__ import annotations

import time

from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session


def register(app):
    @app.get("/osint/dork/{handle}")
    def dork_socials(handle: str):
        handle = sanitize_handle(handle)
        if not handle:
            return {"error": "Invalid handle"}

        platforms = {
            "OnlyFans": f"https://onlyfans.com/{handle}",
            "Fansly": f"https://fansly.com/{handle}",
            "X": f"https://x.com/{handle}",
            "Instagram": f"https://instagram.com/{handle}",
            "TikTok": f"https://tiktok.com/@{handle}",
        }

        results = []
        session = get_tor_session()

        for name, url in platforms.items():
            try:
                resp = request_with_retry(session, "HEAD", url, retries=1, allow_redirects=True)
                status = "LIVE" if resp.status_code == 200 else f"HTTP_{resp.status_code}"
                results.append({"platform": name, "url": url, "status": status})
                time.sleep(0.2)
            except Exception as e:
                results.append({"platform": name, "url": url, "status": "ERROR", "error": str(e)})

        quoted = f'"{handle}"'
        return {
            "handle": handle,
            "results": results,
            "dorks": {
                "google": f"https://www.google.com/search?q=site:onlyfans.com+OR+site:fansly.com+{quoted}",
                "duckduckgo": f"https://duckduckgo.com/?q=site:instagram.com+{quoted}",
            },
        }

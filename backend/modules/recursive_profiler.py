from __future__ import annotations

from backend.modules.cam_mapper import extract_socials
from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session


def register(app):
    @app.get("/osint/deep-scan/{username}")
    def deep_scan(username: str):
        session = get_tor_session()
        username = sanitize_handle(username)
        if not username:
            return {"error": "Invalid username"}

        identity_map = {
            "primary_handle": username,
            "discovered_nodes": {},
            "errors": [],
        }

        sources = [
            f"https://chaturbate.com/{username}/",
            f"https://profiles.myfreecams.com/{username}",
        ]

        for url in sources:
            try:
                r = request_with_retry(session, "GET", url, retries=1)
                if r.status_code != 200:
                    continue
                found = extract_socials(r.text)
                for platform, links in (found or {}).items():
                    identity_map["discovered_nodes"].setdefault(platform, [])
                    for link in links:
                        if link not in identity_map["discovered_nodes"][platform]:
                            identity_map["discovered_nodes"][platform].append(link)
            except Exception as e:
                identity_map["errors"].append({"url": url, "error": str(e)})

        return {"status": "COMPLETED", "identity_tree": identity_map}

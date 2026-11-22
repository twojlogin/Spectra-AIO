from __future__ import annotations

import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session


def register(app):
    @app.get("/osint/search/{query}")
    def global_search(query: str):
        """Search public web results via DuckDuckGo HTML endpoint through Tor."""
        session = get_tor_session()
        query_clean = sanitize_handle(query) or (query or "").strip()[:64]
        if not query_clean:
            return {"error": "Invalid query"}

        full_query = (
            f'"{query_clean}" (site:x.com OR site:twitter.com OR site:instagram.com '
            f'OR site:linktr.ee OR site:onlyfans.com OR site:fansly.com)'
        )
        url = f"https://html.duckduckgo.com/html/?q={quote(full_query)}"

        try:
            r = request_with_retry(session, "GET", url, retries=2, backoff=1.0)
            if r.status_code != 200:
                return {"error": "Search provider error", "status_code": r.status_code}

            soup = BeautifulSoup(r.text, "html.parser")
            found_socials: dict[str, set[str]] = {}
            patterns = {
                "Twitter": r"(?:x\.com|twitter\.com)/[A-Za-z0-9_]+",
                "Instagram": r"instagram\.com/[A-Za-z0-9_.]+",
                "OnlyFans": r"onlyfans\.com/[A-Za-z0-9_.]+",
                "Fansly": r"fansly\.com/[A-Za-z0-9_.]+",
                "Linktree": r"linktr\.ee/[A-Za-z0-9_.]+",
            }

            anchors = soup.select("a.result__a[href], a.result__url[href], a[href]")
            seen_hrefs = set()
            for a in anchors:
                href = (a.get("href") or "").strip()
                if not href or href in seen_hrefs:
                    continue
                seen_hrefs.add(href)
                href_l = href.lower()
                for platform, regex in patterns.items():
                    m = re.search(regex, href_l)
                    if m:
                        found_socials.setdefault(platform, set()).add("https://" + m.group(0))

            return {
                "query": query_clean,
                "discovered_via_search": {k: sorted(v) for k, v in found_socials.items()},
                "raw_results_count": len(seen_hrefs),
            }
        except Exception as e:
            return {"error": str(e), "query": query_clean}

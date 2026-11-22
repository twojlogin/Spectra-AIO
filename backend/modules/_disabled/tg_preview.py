from __future__ import annotations

import re

from bs4 import BeautifulSoup

from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session

BLACKLIST_EXT = (".exe", ".scr", ".vbs", ".bat", ".zip", ".rar", ".7z", ".cmd", ".js", ".msi")
BLACKLIST_DOMAINS = ("mega.nz", "mediafire.com", "zippyshare.com", "anonfiles.com")


def _is_blacklisted(text: str) -> bool:
    t = (text or "").lower()
    return any(ext in t for ext in BLACKLIST_EXT) or any(dom in t for dom in BLACKLIST_DOMAINS)


def register(app):
    @app.get("/osint/telegram/{channel}")
    def scan_tg_channel(channel: str):
        """Passive scan of public Telegram channel preview (t.me/s/<channel>)."""
        session = get_tor_session()
        channel = sanitize_handle(channel)
        if not channel:
            return {"error": "Invalid channel name"}

        url = f"https://t.me/s/{channel}"
        try:
            r = request_with_retry(session, "GET", url, retries=2)
            if r.status_code != 200:
                return {"error": "Channel not available or request blocked", "status_code": r.status_code}

            soup = BeautifulSoup(r.text, "html.parser")
            about = soup.find("div", class_="tgme_channel_info_description")
            counters = soup.find_all("div", class_="tgme_channel_info_counter")
            subscribers = counters[0].text.strip() if counters else "Hidden"

            video_leaks: list[str] = []
            safe_links: list[str] = []

            for msg in soup.find_all("div", class_="tgme_widget_message"):
                text_node = msg.find("div", class_="tgme_widget_message_text")
                text = text_node.get_text(" ", strip=True) if text_node else ""
                links = []
                for a in msg.find_all("a", href=True):
                    href = a.get("href", "").strip()
                    if href.startswith("http"):
                        links.append(href)

                # Skip whole message if it contains clearly unsafe artifacts.
                combined = " ".join([text, *links])
                if _is_blacklisted(combined):
                    continue

                if any(ext in text.lower() for ext in (".mp4", ".mkv", ".mov", ".avi", ".webm")):
                    video_leaks.append((text[:150] + "...") if len(text) > 150 else text)

                for link in links:
                    if not _is_blacklisted(link):
                        safe_links.append(link)

            # Deduplicate while preserving order
            seen = set()
            dedup_links = []
            for link in safe_links:
                if link not in seen:
                    seen.add(link)
                    dedup_links.append(link)

            return {
                "channel": channel,
                "about": about.text.strip() if about else "No description",
                "subscribers": subscribers,
                "video_mentions": video_leaks[:20],
                "recent_external_links": dedup_links[:20],
            }
        except Exception as e:
            return {"error": str(e), "channel": channel}

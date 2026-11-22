from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session


SOCIAL_PATTERNS = {
    "Twitter": r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,30})",
    "Instagram": r"(?:https?://)?(?:www\.)?instagram\.com/([A-Za-z0-9_.]{1,30})",
    "OnlyFans": r"(?:https?://)?(?:www\.)?onlyfans\.com/([A-Za-z0-9_.]{1,64})",
    "Fansly": r"(?:https?://)?(?:www\.)?fansly\.com/([A-Za-z0-9_.]{1,64})",
    "Linktree": r"(?:https?://)?(?:www\.)?linktr\.ee/([A-Za-z0-9_.]{1,64})",
    "TikTok": r"(?:https?://)?(?:www\.)?tiktok\.com/@([A-Za-z0-9_.]{1,64})",
    "AllMyLinks": r"(?:https?://)?(?:www\.)?allmylinks\.com/([A-Za-z0-9_.]{1,64})",
    "Beacons": r"(?:https?://)?(?:www\.)?beacons\.ai/([A-Za-z0-9_.]{1,64})",
}

PLATFORM_BASE = {
    "Twitter": "https://x.com/",
    "Instagram": "https://instagram.com/",
    "OnlyFans": "https://onlyfans.com/",
    "Fansly": "https://fansly.com/",
    "Linktree": "https://linktr.ee/",
    "TikTok": "https://tiktok.com/@",
    "AllMyLinks": "https://allmylinks.com/",
    "Beacons": "https://beacons.ai/",
}


def _to_soup(value: Any) -> BeautifulSoup:
    if isinstance(value, BeautifulSoup):
        return value
    if hasattr(value, "text") and not isinstance(value, (str, bytes)):
        # requests.Response-like
        return BeautifulSoup(getattr(value, "text", ""), "html.parser")
    return BeautifulSoup(str(value or ""), "html.parser")


def extract_socials(soup_or_text: Any, raw_text: str | None = None) -> dict[str, list[str]]:
    """Extract social/profile links from HTML soup or raw text.

    Backward compatible with old signature extract_socials(soup, raw_text).
    """
    soup = _to_soup(soup_or_text)
    text_blob = raw_text if isinstance(raw_text, str) else soup.get_text(" ", strip=True)
    found: dict[str, set[str]] = {}

    def add(platform: str, handle: str) -> None:
        handle = handle.strip("/").split("?")[0].split("#")[0]
        if not handle or handle.lower() in {"share", "intent", "home"}:
            return
        url = PLATFORM_BASE.get(platform, "https://") + handle
        found.setdefault(platform, set()).add(url)

    # Scan anchor hrefs
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not href:
            continue
        for platform, regex in SOCIAL_PATTERNS.items():
            m = re.search(regex, href, re.IGNORECASE)
            if m:
                add(platform, m.group(1))

    # Fallback scan in text
    for platform, regex in SOCIAL_PATTERNS.items():
        for m in re.finditer(regex, text_blob, re.IGNORECASE):
            add(platform, m.group(1))

    return {k: sorted(v) for k, v in found.items()}


def map_cam_model(site: str, username: str) -> dict:
    session = get_tor_session()
    site = (site or "").strip().lower()
    username = sanitize_handle(username)
    if not username:
        return {"error": "Invalid username"}

    targets = {
        "chaturbate": f"https://chaturbate.com/{username}/",
        "mfc": f"https://profiles.myfreecams.com/{username}",
    }
    if site not in targets:
        return {"error": "Unsupported site", "supported_sites": sorted(targets.keys())}

    url = targets[site]
    try:
        r = request_with_retry(session, "GET", url, retries=2)
        if r.status_code != 200:
            return {"status": "BLOCKED_OR_NOT_FOUND", "code": r.status_code, "url": url}

        soup = BeautifulSoup(r.text, "html.parser")
        bio_section = soup.find("div", class_="user-bio")
        scan_text = bio_section.get_text(" ", strip=True) if bio_section else soup.get_text(" ", strip=True)
        socials = extract_socials(soup, scan_text)

        avatar_url = None
        if site == "chaturbate":
            if bio_section:
                img = bio_section.find("img")
                if img and img.get("src") and "logo" not in str(img.get("src")).lower():
                    avatar_url = img.get("src")
            if not avatar_url or "logo" in str(avatar_url).lower():
                # Best-effort deterministic avatar URL; may not exist for all users.
                avatar_url = f"https://roomimg.stream.highwebmedia.com/ri/{username}.jpg"
        elif site == "mfc":
            img = soup.find("img", class_="profile-photo")
            if img and img.get("src"):
                avatar_url = img.get("src")

        return {
            "target": username,
            "site": site,
            "profile_url": url,
            "avatar_url": avatar_url,
            "discovered_socials": socials,
        }
    except Exception as e:
        return {"error": str(e), "site": site, "target": username}


def register(app):
    @app.get("/osint/cam-map/{site}/{username}")
    def api_map_cam(site: str, username: str):
        return map_cam_model(site, username)

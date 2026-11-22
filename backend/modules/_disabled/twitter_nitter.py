from __future__ import annotations

import os
import random

from bs4 import BeautifulSoup

from backend.utils.common import request_with_retry, sanitize_handle
from backend.utils.tor_client import get_tor_session

DEFAULT_NITTER_INSTANCES = [
    "nitter.poast.org",
    "nitter.privacyredirect.com",
    "nitter.space",
    "nitter.tiekoetter.com",
    "nitter.net",
]


def get_nitter_instances() -> list[str]:
    raw = os.getenv("SPECTRA_NITTER_INSTANCES", "")
    if raw.strip():
        items = [x.strip().strip("/") for x in raw.split(",") if x.strip()]
        # Keep only hostname-like values
        cleaned = [x for x in items if x and "/" not in x]
        if cleaned:
            return cleaned
    return DEFAULT_NITTER_INSTANCES.copy()


def scan_twitter_nitter(handle: str) -> dict:
    session = get_tor_session()
    handle = sanitize_handle(handle)
    if not handle:
        return {"error": "Invalid handle"}

    instances = get_nitter_instances()
    random.shuffle(instances)
    errors = []

    for instance in instances:
        url = f"https://{instance}/{handle}"
        try:
            r = request_with_retry(session, "GET", url, retries=1, backoff=0.7)
            if r.status_code == 404:
                return {"status": "NOT_FOUND", "handle": handle, "instance": instance}
            if r.status_code != 200:
                errors.append({"instance": instance, "status_code": r.status_code})
                continue

            soup = BeautifulSoup(r.text, "html.parser")
            bio = soup.find("div", class_="profile-bio")
            fullname = soup.find("a", class_="profile-card-fullname")
            location = soup.find("div", class_="profile-location")
            if not fullname and not bio:
                errors.append({"instance": instance, "error": "Unrecognized response layout"})
                continue
            return {
                "handle": handle,
                "instance": instance,
                "status": "OK",
                "fullname": fullname.get_text(" ", strip=True) if fullname else "Hidden",
                "bio": bio.get_text(" ", strip=True) if bio else "No bio",
                "location": location.get_text(" ", strip=True) if location else None,
                "url": url,
            }
        except Exception as e:
            errors.append({"instance": instance, "error": str(e)})
            continue

    return {
        "error": "No working Nitter instance responded",
        "handle": handle,
        "tried_instances": instances,
        "details": errors[:10],
        "hint": "Set SPECTRA_NITTER_INSTANCES to a comma-separated list of working instances.",
    }


def register(app):
    @app.get("/osint/twitter/{handle}")
    def api_twitter(handle: str):
        return scan_twitter_nitter(handle)

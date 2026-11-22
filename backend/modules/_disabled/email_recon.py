from __future__ import annotations

import hashlib
import re

from backend.utils.common import request_with_retry
from backend.utils.tor_client import get_tor_session

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def register(app):
    @app.get("/osint/email-recon/{email}")
    def email_recon(email: str):
        session = get_tor_session()
        email = (email or "").strip().lower()
        if not EMAIL_RE.match(email):
            return {"error": "Invalid email format"}

        md5 = hashlib.md5(email.encode("utf-8")).hexdigest()
        results = {"email": email, "md5": md5, "profiles": [], "dorks": {}}

        try:
            r = request_with_retry(session, "GET", f"https://en.gravatar.com/{md5}.json", retries=1)
            if r.status_code == 200:
                data = r.json().get("entry", [{}])[0]
                results["profiles"].append(
                    {
                        "site": "Gravatar",
                        "username": data.get("preferredUsername"),
                        "display_name": data.get("displayName"),
                        "about": data.get("aboutMe"),
                        "profile_url": data.get("profileUrl"),
                    }
                )
        except Exception as e:
            results["gravatar_error"] = str(e)

        quoted = f'"{email}"'
        results["dorks"] = {
            "LinkedIn": f"https://www.google.com/search?q=site:linkedin.com+{quoted}",
            "Facebook": f"https://www.google.com/search?q=site:facebook.com+{quoted}",
            "X": f"https://www.google.com/search?q=site:x.com+{quoted}",
        }
        return results

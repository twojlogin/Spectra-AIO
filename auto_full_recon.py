#!/usr/bin/env python3
"""CLI recon orchestrator for Spectra-AIO backend.

This script calls the local backend API and writes a text report.
It is intended for authorized OSINT/security research workflows.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import requests

DEFAULT_API_URL = os.getenv("SPECTRA_API_URL", "http://127.0.0.1:8000")
DEFAULT_TIMEOUT = float(os.getenv("SPECTRA_REQUEST_TIMEOUT", "20"))


def sanitize_name(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    value = value.strip("._-")
    return value[:80] or "target"


def api_get(base_url: str, path: str, timeout: float) -> dict:
    url = f"{base_url.rstrip('/')}{path}"
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"raw": r.text, "status_code": r.status_code}


def generate_report(username: str, site: str, api_url: str = DEFAULT_API_URL, timeout: float = DEFAULT_TIMEOUT) -> Path:
    safe_user = sanitize_name(username)
    safe_site = sanitize_name(site)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = Path(f"REPORT_{safe_site}_{safe_user}_{timestamp}.txt").resolve()

    print(f"\n[!!!] H5N1 TOTAL RECON: {username} @ {site}")
    print(f"[*] API: {api_url}")

    report: list[str] = []
    report.append(f"=== RAPORT OSINT H5N1: {username} ({site}) ===")
    report.append(f"Data: {datetime.now().isoformat()}")
    report.append(f"API: {api_url}")
    report.append("-" * 50)

    try:
        # 1. CAM PROFILE MAP
        print("[1/5] Skanowanie bezpośredniego profilu...")
        cam_data = api_get(api_url, f"/osint/cam-map/{quote(site, safe='')}/{quote(username, safe='')}", timeout)
        avatar_url = cam_data.get("avatar_url") if isinstance(cam_data, dict) else None
        discovered_socials = cam_data.get("discovered_socials", {}) if isinstance(cam_data, dict) else {}

        # 1a. Fallback search
        if not discovered_socials:
            print("[!] Bezpośredni skan pusty. Odpalam search...")
            search_data = api_get(api_url, f"/osint/search/{quote(username, safe='')}", timeout)
            discovered_socials = search_data.get("discovered_via_search", {}) if isinstance(search_data, dict) else {}
            report.append(f"[!] WYKRYTO PRZEZ SEARCH-INDEX: {json.dumps(discovered_socials, indent=2, ensure_ascii=False)}")
        else:
            report.append(f"[+] ZNALEZIONE NA PROFILU: {json.dumps(discovered_socials, indent=2, ensure_ascii=False)}")

        # 2. WAYBACK / GHOST
        print("[2/5] Wskrzeszanie historii (Ghost Scan)...")
        history = api_get(api_url, f"/osint/ghost-scan/{quote(site, safe='')}/{quote(username, safe='')}", timeout)
        emails_found: list[str] = []
        if isinstance(history, dict) and "error" not in history and history.get("status") != "NO_HISTORY":
            leaks = history.get("leaks_discovered", {}) or {}
            emails_found = leaks.get("Email", []) or []
            report.append(f"[+] HISTORIA: Znaleziono {history.get('history_depth', 0)} wersji.")
            report.append(f"[+] MAILE: {', '.join(emails_found) if emails_found else '-'}")

        # 3. EMAIL RECON
        if emails_found:
            print("[3/5] Analiza maili...")
            for email in emails_found:
                try:
                    e_data = api_get(api_url, f"/osint/email-recon/{quote(email, safe='@.')}", timeout)
                except Exception as e:
                    report.append(f"  [!] EMAIL-RECON ERROR ({email}): {e}")
                    continue
                profiles = e_data.get("profiles", []) if isinstance(e_data, dict) else []
                if profiles:
                    p = profiles[0]
                    report.append(
                        f"  [+] GRAVATAR ({email}): {p.get('display_name', '-')} | {p.get('username', '-')}"
                    )
                time.sleep(0.5)

        # 4. OMNI
        print("[4/5] Zwiad ogólny (Omni-Check)...")
        omni = api_get(api_url, f"/osint/check-user/{quote(username, safe='')}", timeout)
        report.append("\n=== OMNI-RECON ===")
        for res in (omni.get("results", []) if isinstance(omni, dict) else []):
            report.append(f"  [{res.get('status', '?')}] {res.get('platform', '?')}")

        # 5. AVATAR
        if avatar_url:
            print("[5/5] Analiza wizualna...")
            try:
                ava = api_get(
                    api_url,
                    f"/osint/avatar-check/{quote(site, safe='')}/{quote(username, safe='')}?avatar_url={quote(str(avatar_url), safe='')}",
                    timeout,
                )
                if isinstance(ava, dict) and "error" not in ava:
                    report.append(f"\n=== AVATAR HASH: {ava.get('avatar_sha256', '-')} ===")
                    reverse = ava.get("reverse_search_ready", {}) or {}
                    report.append(f"[!] YANDEX: {reverse.get('Yandex', '-')}")
            except Exception as e:
                report.append(f"[!] AVATAR ERROR: {e}")

        report_file.write_text("\n".join(report) + "\n", encoding="utf-8")
        print(f"\n[✓] ZAKOŃCZONO. Raport: {report_file}")
        return report_file

    except requests.RequestException as e:
        print(f"\n[!!!] BŁĄD API/SIECI: {e}")
        raise
    except Exception as e:
        print(f"\n[!!!] BŁĄD SYSTEMOWY: {e}")
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Spectra-AIO auto recon CLI")
    parser.add_argument("site", help="Target site/platform, e.g. chaturbate")
    parser.add_argument("username", help="Target username/handle")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help=f"Backend API URL (default: {DEFAULT_API_URL})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP timeout in seconds")
    args = parser.parse_args()

    try:
        generate_report(args.username, args.site, api_url=args.api_url, timeout=args.timeout)
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

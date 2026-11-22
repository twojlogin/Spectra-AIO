#!/usr/bin/env python3
"""Spectra-AIO lightweight CLI (stdlib argparse + requests)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.parse import quote

import requests

DEFAULT_API = os.getenv("SPECTRA_API_URL", "http://127.0.0.1:8000")
DEFAULT_TIMEOUT = float(os.getenv("SPECTRA_REQUEST_TIMEOUT", "20"))


def api_get(api: str, path: str, timeout: float) -> dict:
    r = requests.get(f"{api.rstrip('/')}{path}", timeout=timeout)
    r.raise_for_status()
    return r.json()


def api_post(api: str, path: str, payload: dict, timeout: float) -> dict:
    r = requests.post(f"{api.rstrip('/')}{path}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def cmd_status(args: argparse.Namespace) -> int:
    data = api_get(args.api, "/", args.timeout)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_recon(args: argparse.Namespace) -> int:
    # Reuse auto_full_recon logic by importing if available
    from auto_full_recon import generate_report

    generate_report(args.username, args.site, api_url=args.api, timeout=args.timeout)
    return 0


def cmd_profiles_list(args: argparse.Namespace) -> int:
    data = api_get(args.api, "/api/profiles", args.timeout)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_profiles_add(args: argparse.Namespace) -> int:
    payload = {
        "name": args.name,
        "platform": args.platform,
        "url": args.url,
        "description": args.description or "",
    }
    data = api_post(args.api, "/api/profiles/add", payload, args.timeout)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_ui(args: argparse.Namespace) -> int:
    print(f"{args.api.rstrip('/')}/ui")
    return 0


def cmd_server(args: argparse.Namespace) -> int:
    import uvicorn

    host = args.host or os.getenv("SPECTRA_HOST", "127.0.0.1")
    port = args.port or int(os.getenv("SPECTRA_PORT", "8000"))
    uvicorn.run("backend.main_backend:app", host=host, port=port, reload=args.reload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="spectra", description="Spectra-AIO CLI")
    p.add_argument("--api", default=DEFAULT_API, help=f"Backend API URL (default: {DEFAULT_API})")
    p.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP timeout seconds")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("status", help="Show backend status")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("ui", help="Print web UI URL")
    s.set_defaults(func=cmd_ui)

    s = sub.add_parser("recon", help="Run full recon via backend and write report")
    s.add_argument("site")
    s.add_argument("username")
    s.set_defaults(func=cmd_recon)

    sp = sub.add_parser("profiles", help="Profile operations")
    sp_sub = sp.add_subparsers(dest="profiles_cmd", required=True)
    spl = sp_sub.add_parser("list", help="List profiles")
    spl.set_defaults(func=cmd_profiles_list)
    spa = sp_sub.add_parser("add", help="Add profile")
    spa.add_argument("--name", required=True)
    spa.add_argument("--platform", required=True)
    spa.add_argument("--url", required=True)
    spa.add_argument("--description", default="")
    spa.set_defaults(func=cmd_profiles_add)

    ss = sub.add_parser("server", help="Run backend server")
    ss.add_argument("--host", default=None)
    ss.add_argument("--port", type=int, default=None)
    ss.add_argument("--reload", action="store_true")
    ss.set_defaults(func=cmd_server)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except requests.RequestException as e:
        print(f"[API ERROR] {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

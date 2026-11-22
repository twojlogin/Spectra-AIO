#!/usr/bin/env python3
"""Spectra-AIO bootstrap - detect environment, verify deps, setup venv, basic checks, cleanup."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / ".venv"
REQ_FILE = ROOT / "backend" / "requirements.txt"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"


def info(msg): print(f"[INFO] {msg}")
def ok(msg): print(f"[OK]   {msg}")
def warn(msg): print(f"[WARN] {msg}")
def err(msg): print(f"[ERR]  {msg}")


def detect_platform() -> dict:
    data = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "python_ok": sys.version_info >= (3, 10),
        "distro": "",
        "pkg_manager": "",
    }
    if data["system"] == "Linux":
        os_release = Path("/etc/os-release")
        if os_release.exists():
            for line in os_release.read_text(errors="ignore").splitlines():
                if line.startswith("PRETTY_NAME="):
                    data["distro"] = line.split("=", 1)[1].strip().strip('"')
                    break
        for pm in ["apt", "dnf", "pacman", "zypper", "apk"]:
            if shutil.which(pm):
                data["pkg_manager"] = pm
                break
    elif data["system"] == "Windows":
        data["pkg_manager"] = "winget/choco/scoop (manual)"
    elif data["system"] == "Darwin":
        data["pkg_manager"] = "brew" if shutil.which("brew") else ""
    return data


def check_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def check_port(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def run(cmd: list[str], cwd: Path = ROOT) -> int:
    info("$ " + " ".join(cmd))
    return subprocess.call(cmd, cwd=str(cwd))


def venv_python() -> Path:
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_env() -> None:
    if not ENV_FILE.exists() and ENV_EXAMPLE.exists():
        shutil.copy2(ENV_EXAMPLE, ENV_FILE)
        ok("Utworzono .env z .env.example")
    elif ENV_FILE.exists():
        ok(".env istnieje")
    else:
        warn("Brak .env i .env.example")


def cleanup_artifacts() -> None:
    removed = 0
    for p in ROOT.rglob("__pycache__"):
        if ".venv" in p.parts or "legacy" in p.parts:
            continue
        shutil.rmtree(p, ignore_errors=True)
        removed += 1
    for pat in ["*.pyc", "*.pyo"]:
        for p in ROOT.rglob(pat):
            if ".venv" in p.parts or "legacy" in p.parts:
                continue
            try:
                p.unlink()
                removed += 1
            except OSError:
                pass
    ok(f"Wyczyszczono artefakty cache: {removed}")


def security_quick_scan() -> int:
    issues = 0
    # obvious junk that should not be committed
    for name in [".env", ".venv"]:
        if (ROOT / name).exists():
            info(f"Obecny lokalnie: {name} (ok lokalnie, ale musi być w .gitignore)")
    if (ROOT / ".env").exists():
        # ensure gitignore covers .env
        gi = ROOT / ".gitignore"
        if not gi.exists() or ".env" not in gi.read_text(errors="ignore"):
            warn(".env istnieje, ale .gitignore nie zawiera .env")
            issues += 1
    # simple secret pattern scan in tracked-like source files
    patterns = ["BEGIN PRIVATE KEY", "AKIA", "ghp_", "glpat-", "xoxb-"]
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in {".venv", ".git", "tor", "legacy", "__pycache__"} for part in p.parts):
            continue
        if p.suffix.lower() not in {".py", ".js", ".ps1", ".sh", ".md", ".txt", ".toml", ".json", ".yml", ".yaml", ".env"}:
            continue
        if p.name in {"bootstrap.py", "security_check.py", "security_check.sh", "security_check.ps1"}:
            continue
        try:
            textf = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in patterns:
            if pat in textf and "security_check" not in p.name:
                warn(f"Możliwy sekret/wzorzec '{pat}' w {p.relative_to(ROOT)}")
                issues += 1
                break
    if issues == 0:
        ok("Szybki scan bezpieczeństwa: brak oczywistych problemów")
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Spectra-AIO bootstrap")
    ap.add_argument("--skip-install", action="store_true", help="Nie instaluj zależności")
    ap.add_argument("--no-clean", action="store_true", help="Nie czyść __pycache__")
    ap.add_argument("--check-only", action="store_true", help="Tylko diagnostyka")
    args = ap.parse_args()

    info(f"Root: {ROOT}")
    env = detect_platform()
    info(f"System: {env['system']} {env['release']} ({env['machine']})")
    if env["distro"]:
        info(f"Distro: {env['distro']}")
    if env["pkg_manager"]:
        info(f"Package manager: {env['pkg_manager']}")
    info(f"Python: {env['python']}")

    if not env["python_ok"]:
        err("Wymagany Python 3.10+")
        return 1
    ok("Python wersja OK")

    for cmd in ["git", "curl"]:
        (ok if check_cmd(cmd) else warn)(f"{cmd}: {'jest' if check_cmd(cmd) else 'brak'}")

    tor_9050 = check_port("127.0.0.1", 9050)
    tor_9150 = check_port("127.0.0.1", 9150)
    if tor_9050:
        ok("Tor/proxy port 9050: nasłuchuje")
    elif tor_9150:
        warn("Wykryto port 9150 (Tor Browser). Ustaw SPECTRA_TOR_PROXY=socks5h://127.0.0.1:9150")
    else:
        warn("Brak nasłuchu na 9050/9150. Możesz uruchomić Tora albo ustawić SPECTRA_PROXY_MODE=direct/custom")

    ensure_env()
    sec_issues = security_quick_scan()

    if args.check_only:
        return 1 if sec_issues else 0

    if not VENV_DIR.exists():
        rc = run([sys.executable, "-m", "venv", str(VENV_DIR)])
        if rc != 0:
            err("Nie udało się utworzyć .venv")
            return rc
        ok("Utworzono .venv")
    else:
        ok(".venv już istnieje")

    py = venv_python()
    if not py.exists():
        err(f"Brak python w venv: {py}")
        return 1

    if not args.skip_install:
        if not REQ_FILE.exists():
            err(f"Brak {REQ_FILE}")
            return 1
        rc = run([str(py), "-m", "pip", "install", "--upgrade", "pip"])
        if rc != 0:
            return rc
        rc = run([str(py), "-m", "pip", "install", "-r", str(REQ_FILE)])
        if rc != 0:
            return rc
        ok("Zależności zainstalowane")

    if not args.no_clean:
        cleanup_artifacts()

    print("\n=== GOTOWE ===")
    print(f"Uruchom backend: {py} -m uvicorn backend.main_backend:app --host 127.0.0.1 --port 8000")
    print("UI: http://127.0.0.1:8000/ui")
    return 1 if sec_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())

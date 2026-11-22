import importlib


MODULES = [
    "backend.main_backend",
    "backend.db",
    "backend.utils.tor_client",
    "backend.utils.common",
    "cli",
    "auto_full_recon",
]


def test_imports():
    for m in MODULES:
        importlib.import_module(m)

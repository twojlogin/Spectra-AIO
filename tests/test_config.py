import os
from backend.utils.tor_client import get_proxy_mode, get_proxy_url, tor_proxy_config


def test_proxy_mode_direct(monkeypatch):
    monkeypatch.setenv("SPECTRA_PROXY_MODE", "direct")
    assert get_proxy_mode() == "direct"
    assert get_proxy_url() is None


def test_proxy_mode_tor_default(monkeypatch):
    monkeypatch.delenv("SPECTRA_PROXY_MODE", raising=False)
    monkeypatch.delenv("SPECTRA_USE_TOR", raising=False)
    monkeypatch.setenv("SPECTRA_TOR_PROXY", "socks5h://127.0.0.1:9050")
    assert get_proxy_mode() == "tor"
    assert get_proxy_url() == "socks5h://127.0.0.1:9050"


def test_proxy_mode_custom(monkeypatch):
    monkeypatch.setenv("SPECTRA_PROXY_MODE", "custom")
    monkeypatch.setenv("SPECTRA_PROXY_URL", "http://127.0.0.1:8080")
    assert get_proxy_mode() == "custom"
    assert get_proxy_url() == "http://127.0.0.1:8080"


def test_tor_proxy_config_shape(monkeypatch):
    monkeypatch.setenv("SPECTRA_PROXY_MODE", "direct")
    cfg = tor_proxy_config()
    assert cfg["mode"] == "direct"
    assert "enabled" in cfg
    assert "timeout" in cfg

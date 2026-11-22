from backend.utils.tor_client import (
    get_proxy_mode, get_proxy_url, tor_enabled, get_default_timeout,
    tor_proxy_config, proxy_unavailable_message, get_tor_session,
)


def test_mode_direct(monkeypatch):
    monkeypatch.setenv("SPECTRA_PROXY_MODE", "direct")
    assert get_proxy_mode() == "direct"
    assert get_proxy_url() is None
    assert tor_enabled() is False


def test_mode_tor(monkeypatch):
    monkeypatch.setenv("SPECTRA_PROXY_MODE", "tor")
    monkeypatch.setenv("SPECTRA_TOR_PROXY", "socks5h://127.0.0.1:9050")
    assert get_proxy_mode() == "tor"
    assert tor_enabled() is True
    assert get_proxy_url() == "socks5h://127.0.0.1:9050"


def test_mode_custom(monkeypatch):
    monkeypatch.setenv("SPECTRA_PROXY_MODE", "custom")
    monkeypatch.setenv("SPECTRA_PROXY_URL", "http://proxy:8080")
    assert get_proxy_mode() == "custom"
    assert get_proxy_url() == "http://proxy:8080"


def test_use_tor_false(monkeypatch):
    monkeypatch.delenv("SPECTRA_PROXY_MODE", raising=False)
    monkeypatch.setenv("SPECTRA_USE_TOR", "false")
    assert get_proxy_mode() == "direct"


def test_default_timeout(monkeypatch):
    monkeypatch.setenv("SPECTRA_REQUEST_TIMEOUT", "7")
    assert get_default_timeout() == 7.0


def test_proxy_config_keys(monkeypatch):
    monkeypatch.setenv("SPECTRA_PROXY_MODE", "direct")
    cfg = tor_proxy_config()
    for k in ["mode", "enabled", "proxy", "timeout"]:
        assert k in cfg


def test_proxy_unavailable_message():
    msg = proxy_unavailable_message("boom")
    assert isinstance(msg, str)
    assert "boom" in msg


def test_session_has_defaults(monkeypatch):
    monkeypatch.setenv("SPECTRA_PROXY_MODE", "direct")
    s = get_tor_session()
    assert hasattr(s, "default_timeout")
    assert s.proxies == {}

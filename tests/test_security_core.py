from fastapi.testclient import TestClient
from backend.main_backend import app
import backend.main_backend as mb


client = TestClient(app)


def test_profile_add_rejects_non_http_url():
    r = client.post("/api/profiles/add", json={
        "name": "n", "platform": "p", "url": "javascript:alert(1)", "description": ""
    })
    assert r.status_code == 400
    assert "http" in r.json().get("detail", "").lower()


def test_profile_add_rejects_missing_fields():
    r = client.post("/api/profiles/add", json={"name": "", "platform": "p", "url": "https://x.com"})
    assert r.status_code == 422  # pydantic min_length


def test_profile_add_accepts_valid_http_url(tmp_path, monkeypatch):
    db = tmp_path / "p.db"
    monkeypatch.setenv("SPECTRA_DB_PATH", str(db))
    from backend.db import init_db
    init_db()
    r = client.post("/api/profiles/add", json={
        "name": "ok", "platform": "web", "url": "https://example.com/u", "description": "d"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


def test_network_status_no_check_does_not_require_outbound(monkeypatch):
    # should just return config, no check
    monkeypatch.setattr(mb, "get_tor_session", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("should not be called")))
    r = client.get("/api/network/status")
    assert r.status_code == 200
    data = r.json()
    assert "config" in data
    assert "check" not in data


def test_network_check_rate_limit_and_no_leak(monkeypatch):
    mb._network_check_last.clear()
    monkeypatch.setattr(mb, "_NETWORK_CHECK_COOLDOWN_S", 60.0)
    monkeypatch.setattr(mb, "tor_proxy_config", lambda: {"mode": "direct", "enabled": False, "proxy": None, "timeout": 10, "user_agent": "ua"})

    class BadSession:
        def get(self, *args, **kwargs):
            raise RuntimeError("SECRET_INTERNAL_DETAIL")

    monkeypatch.setattr(mb, "get_tor_session", lambda timeout=10: BadSession())
    r1 = client.get("/api/network/status?check=true")
    assert r1.status_code == 200
    d1 = r1.json()
    assert "SECRET_INTERNAL_DETAIL" not in str(d1)
    assert d1["check"]["error"] == "check_failed"

    r2 = client.get("/api/network/status?check=true")
    d2 = r2.json()
    assert d2["check"]["error"] == "rate_limited"
    assert "SECRET_INTERNAL_DETAIL" not in str(d2)


def test_profiles_list_returns_array():
    r = client.get("/api/profiles")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_legacy_profile_add_rejects_bad_url(tmp_path, monkeypatch):
    db = tmp_path / "p2.db"
    monkeypatch.setenv("SPECTRA_DB_PATH", str(db))
    from backend.db import init_db
    init_db()
    r = client.post("/api/profiles/add_legacy", params={
        "name": "n", "platform": "p", "url": "ftp://bad", "description": ""
    })
    assert r.status_code == 400


def test_stats_has_required_keys():
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    for k in ["ok", "version", "modules", "module_count", "profiles_count", "tor"]:
        assert k in data


def test_tor_mode_check_error_does_not_leak_secret(monkeypatch):
    mb._network_check_last.clear()
    monkeypatch.setattr(mb, "_NETWORK_CHECK_COOLDOWN_S", 0.0)
    monkeypatch.setattr(mb, "tor_proxy_config", lambda: {"mode": "tor", "enabled": True, "proxy": "socks5h://127.0.0.1:9050", "timeout": 10, "user_agent": "ua"})

    class BadSession:
        def get(self, *args, **kwargs):
            raise RuntimeError("SECRET_INTERNAL_DETAIL")

    monkeypatch.setattr(mb, "get_tor_session", lambda timeout=10: BadSession())
    r = client.get("/api/network/status?check=true")
    data = r.json()
    assert "SECRET_INTERNAL_DETAIL" not in str(data)
    assert data["check"]["error"] == "check_failed"


def test_network_check_rate_limit_returns_retry_after(monkeypatch):
    mb._network_check_last.clear()
    monkeypatch.setattr(mb, "_NETWORK_CHECK_COOLDOWN_S", 60.0)
    monkeypatch.setattr(mb, "tor_proxy_config", lambda: {"mode": "direct", "enabled": False, "proxy": None, "timeout": 10, "user_agent": "ua"})

    class OkSession:
        def get(self, *args, **kwargs):
            class R:
                status_code = 200
                def json(self):
                    return {"ip": "1.2.3.4"}
            return R()

    monkeypatch.setattr(mb, "get_tor_session", lambda timeout=10: OkSession())
    assert client.get("/api/network/status?check=true").status_code == 200
    r2 = client.get("/api/network/status?check=true")
    data = r2.json()
    assert data["check"]["error"] == "rate_limited"
    assert isinstance(data["check"].get("retry_after_s"), int)
    assert data["check"]["retry_after_s"] >= 1


def test_profile_add_rejects_javascript_url():
    r = client.post("/api/profiles/add", json={
        "name": "x", "platform": "p", "url": "javascript:alert(1)", "description": ""
    })
    assert r.status_code == 400


def test_profile_add_rejects_data_url():
    r = client.post("/api/profiles/add", json={
        "name": "x", "platform": "p", "url": "data:text/html,hi", "description": ""
    })
    assert r.status_code == 400


def test_profile_add_rejects_file_url():
    r = client.post("/api/profiles/add", json={
        "name": "x", "platform": "p", "url": "file:///etc/passwd", "description": ""
    })
    assert r.status_code == 400


def test_stats_modules_count_matches_list():
    r = client.get("/api/stats")
    data = r.json()
    assert data["module_count"] == len(data["modules"])


def test_network_status_config_has_mode():
    r = client.get("/api/network/status")
    data = r.json()
    assert "config" in data
    assert "mode" in data["config"]


def test_profile_add_rejects_too_long_name():
    r = client.post("/api/profiles/add", json={
        "name": "a" * 500, "platform": "p", "url": "https://example.com", "description": ""
    })
    assert r.status_code == 422


def test_ui_static_css_served():
    r = client.get("/ui/static/style.css")
    assert r.status_code == 200
    assert "body" in r.text


def test_network_status_check_ok_flag_false_on_rate_limit(monkeypatch):
    mb._network_check_last.clear()
    monkeypatch.setattr(mb, "_NETWORK_CHECK_COOLDOWN_S", 60.0)
    monkeypatch.setattr(mb, "tor_proxy_config", lambda: {"mode": "direct", "enabled": False, "proxy": None, "timeout": 10, "user_agent": "ua"})

    class OkSession:
        def get(self, *args, **kwargs):
            class R:
                status_code = 200
                def json(self):
                    return {"ip": "1.2.3.4"}
            return R()

    monkeypatch.setattr(mb, "get_tor_session", lambda timeout=10: OkSession())
    client.get("/api/network/status?check=true")
    r2 = client.get("/api/network/status?check=true")
    assert r2.json()["ok"] is False


def test_legacy_profile_add_accepts_valid_url(tmp_path, monkeypatch):
    db = tmp_path / "p3.db"
    monkeypatch.setenv("SPECTRA_DB_PATH", str(db))
    from backend.db import init_db
    init_db()
    r = client.post("/api/profiles/add_legacy", params={
        "name": "ok", "platform": "web", "url": "https://example.com/ok", "description": "d"
    })
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_health_endpoint_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True

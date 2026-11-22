from fastapi.testclient import TestClient
from backend.main_backend import app
import backend.main_backend as mb


client = TestClient(app)


def test_network_check_rate_limited(monkeypatch):
    # reset cooldown map
    mb._network_check_last.clear()
    monkeypatch.setattr(mb, "_NETWORK_CHECK_COOLDOWN_S", 60.0)

    # avoid real outbound calls by forcing direct mode and making session.get return simple object
    class FakeResp:
        status_code = 200
        def json(self):
            return {"ip": "1.2.3.4"}

    class FakeSession:
        def get(self, *args, **kwargs):
            return FakeResp()

    monkeypatch.setattr(mb, "tor_proxy_config", lambda: {"mode": "direct", "enabled": False, "proxy": None, "timeout": 10, "user_agent": "ua"})
    monkeypatch.setattr(mb, "get_tor_session", lambda timeout=10: FakeSession())

    r1 = client.get("/api/network/status?check=true")
    assert r1.status_code == 200
    r2 = client.get("/api/network/status?check=true")
    assert r2.status_code == 200
    data = r2.json()
    assert data["ok"] is False
    assert data["check"]["error"] == "rate_limited"


def test_network_check_error_does_not_leak_exception(monkeypatch):
    mb._network_check_last.clear()
    monkeypatch.setattr(mb, "_NETWORK_CHECK_COOLDOWN_S", 0.0)
    monkeypatch.setattr(mb, "tor_proxy_config", lambda: {"mode": "direct", "enabled": False, "proxy": None, "timeout": 10, "user_agent": "ua"})

    class BadSession:
        def get(self, *args, **kwargs):
            raise RuntimeError("SECRET_INTERNAL_DETAIL")

    monkeypatch.setattr(mb, "get_tor_session", lambda timeout=10: BadSession())

    r = client.get("/api/network/status?check=true")
    assert r.status_code == 200
    data = r.json()
    assert data["check"]["error"] == "check_failed"
    assert "SECRET_INTERNAL_DETAIL" not in str(data)

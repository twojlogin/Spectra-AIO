from fastapi.testclient import TestClient
from backend.main_backend import app


client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"]
    assert "ui" in data


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_stats():
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert "modules" in data
    assert "profiles_count" in data
    assert "tor" in data


def test_network_status():
    r = client.get("/api/network/status")
    assert r.status_code == 200
    data = r.json()
    assert "config" in data


def test_ui_served():
    r = client.get("/ui")
    assert r.status_code == 200
    assert "Spectra-AIO" in r.text


def test_profiles_list():
    r = client.get("/api/profiles")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

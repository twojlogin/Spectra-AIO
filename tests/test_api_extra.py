from fastapi.testclient import TestClient
from backend.main_backend import app


client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_stats_shape():
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["modules"], list)
    assert isinstance(data["module_count"], int)
    assert isinstance(data["profiles_count"], int)


def test_network_status_shape():
    r = client.get("/api/network/status")
    assert r.status_code == 200
    data = r.json()
    assert "config" in data
    assert "mode" in data["config"]


def test_profiles_add_rejects_missing():
    r = client.post("/api/profiles/add", params={"name": "", "platform": "", "url": ""})
    # endpoint returns {error: ...} or rejects; should not be 200-ok success
    assert r.status_code in (200, 400, 422)
    if r.status_code == 200:
        data = r.json()
        assert data.get("success") is False or "error" in data


def test_nonexistent_route_404():
    r = client.get("/nope/does-not-exist")
    assert r.status_code == 404

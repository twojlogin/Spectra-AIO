from backend.modules.username_aggregator import _status_from_response


class FakeResp:
    def __init__(self, status_code=200, text="", headers=None, url="https://example.com/u", json_data=None):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self.url = url
        self._json = json_data

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


def test_404_is_not_found():
    r = FakeResp(status_code=404)
    status, reason = _status_from_response(r, {}, "u")
    assert status == "NOT_FOUND"
    assert reason == "http_404"


def test_403_is_blocked():
    r = FakeResp(status_code=403)
    status, reason = _status_from_response(r, {}, "u")
    assert status == "BLOCKED"
    assert reason == "http_403"


def test_200_with_found_marker():
    r = FakeResp(status_code=200, text="Repositories followers overview")
    p = {"found_markers": ["repositories"], "not_found_markers": ["not found"]}
    status, reason = _status_from_response(r, p, "u")
    assert status == "FOUND"
    assert "marker_found" in reason


def test_200_with_not_found_marker():
    r = FakeResp(status_code=200, text="Page not found")
    p = {"found_markers": ["repositories"], "not_found_markers": ["not found"]}
    status, reason = _status_from_response(r, p, "u")
    assert status == "NOT_FOUND"
    assert "marker_not_found" in reason


def test_200_without_markers_is_unknown():
    r = FakeResp(status_code=200, text="random page")
    p = {"found_markers": ["repositories"], "not_found_markers": ["not found"]}
    status, reason = _status_from_response(r, p, "u")
    assert status == "UNKNOWN"
    assert reason == "http_200_no_strong_marker"


def test_reddit_json_found():
    r = FakeResp(status_code=200, headers={"Content-Type": "application/json"}, json_data={"data": {"name": "u"}})
    p = {"json_found_key": "name"}
    status, reason = _status_from_response(r, p, "u")
    assert status == "FOUND"
    assert reason == "json_user_found"

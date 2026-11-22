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
    assert _status_from_response("X", r, {}, "u") == "NOT_FOUND"


def test_403_is_blocked():
    r = FakeResp(status_code=403)
    assert _status_from_response("X", r, {}, "u") == "BLOCKED"


def test_200_with_found_marker():
    r = FakeResp(status_code=200, text="Repositories followers overview")
    p = {"found_markers": ["repositories"], "not_found_markers": ["not found"]}
    assert _status_from_response("GitHub", r, p, "u") == "FOUND"


def test_200_with_not_found_marker():
    r = FakeResp(status_code=200, text="Page not found")
    p = {"found_markers": ["repositories"], "not_found_markers": ["not found"]}
    assert _status_from_response("GitHub", r, p, "u") == "NOT_FOUND"


def test_200_without_markers_is_unknown():
    r = FakeResp(status_code=200, text="random page")
    p = {"found_markers": ["repositories"], "not_found_markers": ["not found"]}
    assert _status_from_response("GitHub", r, p, "u") == "UNKNOWN"


def test_reddit_json_found():
    r = FakeResp(status_code=200, headers={"Content-Type": "application/json"}, json_data={"data": {"name": "u"}})
    p = {"json_found_key": "name"}
    assert _status_from_response("Reddit", r, p, "u") == "FOUND"

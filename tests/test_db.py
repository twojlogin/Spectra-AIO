import os
import sqlite3
from backend.db import add_profile, get_all_profiles, init_db, _normalize_metadata, get_db_path


def test_db_path_from_env(monkeypatch):
    monkeypatch.setenv("SPECTRA_DB_PATH", "/tmp/spectra-test.db")
    assert get_db_path() == "/tmp/spectra-test.db"


def test_normalize_metadata_none():
    assert _normalize_metadata(None) == "{}"


def test_normalize_metadata_dict():
    import json
    out = json.loads(_normalize_metadata({"a": 1}))
    assert out["a"] == 1


def test_normalize_metadata_json_string():
    out = _normalize_metadata('{"a": 1}')
    assert '"a"' in out


def test_normalize_metadata_bad_string():
    import json
    out = json.loads(_normalize_metadata("not-json"))
    assert out["raw"] == "not-json"


def test_add_and_list_profiles(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    monkeypatch.setenv("SPECTRA_DB_PATH", str(db))
    init_db()
    ok = add_profile("Alice", "github", "https://github.com/alice", "desc", {"k": "v"})
    assert ok is True
    # duplicate
    ok2 = add_profile("Alice2", "github", "https://github.com/alice", "desc2")
    assert ok2 is False
    profiles = get_all_profiles()
    assert len(profiles) == 1
    assert profiles[0]["name"] == "Alice"
    assert profiles[0]["metadata"]["k"] == "v"


def test_add_profile_rejects_missing_fields(tmp_path, monkeypatch):
    db = tmp_path / "t2.db"
    monkeypatch.setenv("SPECTRA_DB_PATH", str(db))
    init_db()
    assert add_profile("", "github", "https://x") is False
    assert add_profile("n", "", "https://x") is False
    assert add_profile("n", "p", "") is False

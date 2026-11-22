import pytest
from backend.utils.common import sanitize_handle, env_float


def test_sanitize_handle_clean():
    assert sanitize_handle("user.name_1-2") == "user.name_1-2"


def test_sanitize_handle_strips_bad_chars():
    assert sanitize_handle("user name!@#") == "username"


def test_sanitize_handle_empty():
    assert sanitize_handle("") == ""
    assert sanitize_handle(None) == ""


def test_sanitize_handle_too_long_truncated():
    long = "a" * 200
    out = sanitize_handle(long)
    assert len(out) <= 64


def test_env_float_default(monkeypatch):
    monkeypatch.delenv("X_FLOAT_TEST", raising=False)
    assert env_float("X_FLOAT_TEST", 1.5) == 1.5


def test_env_float_value(monkeypatch):
    monkeypatch.setenv("X_FLOAT_TEST", "2.5")
    assert env_float("X_FLOAT_TEST", 1.0) == 2.5


def test_env_float_bad_value(monkeypatch):
    monkeypatch.setenv("X_FLOAT_TEST", "nope")
    assert env_float("X_FLOAT_TEST", 3.0) == 3.0

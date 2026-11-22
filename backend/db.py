"""SQLite storage for Spectra-AIO profiles."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Any

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "profiles.db")


def get_db_path() -> str:
    return os.getenv("SPECTRA_DB_PATH", DEFAULT_DB_PATH)


@contextmanager
def get_connection():
    conn = sqlite3.connect(get_db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                description TEXT,
                last_scraped DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
            """
        )


def _normalize_metadata(metadata: Any) -> str:
    if metadata is None:
        return "{}"
    if isinstance(metadata, str):
        metadata = metadata.strip()
        if not metadata:
            return "{}"
        try:
            json.loads(metadata)
            return metadata
        except json.JSONDecodeError:
            return json.dumps({"raw": metadata})
    try:
        return json.dumps(metadata, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps({"raw": str(metadata)})


def add_profile(name: str, platform: str, url: str, description: str = "", metadata: Any = None) -> bool:
    name = (name or "").strip()
    platform = (platform or "").strip()
    url = (url or "").strip()
    description = (description or "").strip()
    if not name or not platform or not url:
        return False
    with get_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO profiles (name, platform, url, description, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, platform, url, description, _normalize_metadata(metadata)),
            )
            return True
        except sqlite3.IntegrityError:
            return False


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    raw_metadata = data.get("metadata")
    if isinstance(raw_metadata, str) and raw_metadata:
        try:
            data["metadata"] = json.loads(raw_metadata)
        except json.JSONDecodeError:
            pass
    return data


def get_all_profiles() -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM profiles ORDER BY last_scraped DESC").fetchall()
    return [_row_to_dict(row) for row in rows]

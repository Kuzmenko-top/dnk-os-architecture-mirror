# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_database"
# purpose: "High-performance SQLite WAL persistent database for Visual Shell & Canvas Engine"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-06"
# --- END DNK-MRH-HEADER ---

import os
import json
import sqlite3
import threading
from pathlib import Path
from collections.abc import MutableMapping
from typing import Dict, Any, List, Optional, Iterator

from core.atomic_store import atomic_json_read, atomic_json_write

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "visual_shell_db.json")
SQLITE_DB_PATH = str(BASE_DIR / "visual_shell.db")

_db_lock = threading.RLock()


def _get_connection(db_path: str = SQLITE_DB_PATH) -> sqlite3.Connection:
    """Creates a thread-safe connection with SQLite WAL enabled and busy timeout."""
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=15000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _init_sqlite_schema(db_path: str = SQLITE_DB_PATH) -> None:
    """Initializes tables for canvases, artifacts, and runs."""
    with _db_lock:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS canvases (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()


class SQLiteTableDict(MutableMapping):
    """Dictionary-like interface mapped to an SQLite table with WAL support."""

    def __init__(self, db_path: str, table_name: str, lock: threading.RLock):
        self.db_path = db_path
        self.table_name = table_name
        self._lock = lock

    def _conn(self) -> sqlite3.Connection:
        return _get_connection(self.db_path)

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            with self._conn() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT data FROM {self.table_name} WHERE id = ?", (str(key),))
                row = cursor.fetchone()
                if not row:
                    raise KeyError(key)
                return json.loads(row[0])

    def __setitem__(self, key: str, value: Any) -> None:
        val_json = json.dumps(value)
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    f"INSERT INTO {self.table_name} (id, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
                    f"ON CONFLICT(id) DO UPDATE SET data=excluded.data, updated_at=CURRENT_TIMESTAMP",
                    (str(key), val_json)
                )
                conn.commit()

    def __delitem__(self, key: str) -> None:
        with self._lock:
            with self._conn() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (str(key),))
                conn.commit()
                if cursor.rowcount == 0:
                    raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        with self._lock:
            with self._conn() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT id FROM {self.table_name}")
                keys = [row[0] for row in cursor.fetchall()]
        return iter(keys)

    def __len__(self) -> int:
        with self._lock:
            with self._conn() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                row = cursor.fetchone()
                return row[0] if row else 0

    def clear(self) -> None:
        with self._lock:
            with self._conn() as conn:
                conn.execute(f"DELETE FROM {self.table_name}")
                conn.commit()

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            with self._conn() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT id, data FROM {self.table_name}")
                return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}


# Initialize schema on load
_init_sqlite_schema()

# Provide dictionary-like _data for 100% backward compatibility
_data: Dict[str, SQLiteTableDict] = {
    "canvases": SQLiteTableDict(SQLITE_DB_PATH, "canvases", _db_lock),
    "artifacts": SQLiteTableDict(SQLITE_DB_PATH, "artifacts", _db_lock),
    "runs": SQLiteTableDict(SQLITE_DB_PATH, "runs", _db_lock),
}

_is_loaded = False


def _migrate_json_to_sqlite() -> None:
    """Migrates existing visual_shell_db.json into SQLite tables if empty."""
    if os.path.exists(DB_PATH):
        try:
            loaded = atomic_json_read(DB_PATH, default=None)
            if loaded and isinstance(loaded, dict):
                for table_key in ["canvases", "artifacts", "runs"]:
                    table_dict = _data.get(table_key)
                    if table_dict is not None and len(table_dict) == 0:
                        records = loaded.get(table_key, {})
                        if isinstance(records, dict):
                            for k, v in records.items():
                                table_dict[k] = v
        except Exception:
            pass


def load_db(force: bool = False) -> None:
    """Initializes and migrates database state if needed."""
    global _is_loaded
    if not _is_loaded or force:
        _init_sqlite_schema()
        _migrate_json_to_sqlite()
        _is_loaded = True


def save_db() -> None:
    """Exports SQLite tables to visual_shell_db.json as an asynchronous backup snapshot."""
    try:
        snapshot = {
            "canvases": _data["canvases"].to_dict(),
            "artifacts": _data["artifacts"].to_dict(),
            "runs": _data["runs"].to_dict(),
        }
        atomic_json_write(DB_PATH, snapshot)
    except Exception:
        pass


def get_canvas(canvas_id: str) -> Any:
    load_db()
    return _data["canvases"].get(canvas_id)


def set_canvas(canvas_id: str, canvas_data: Any) -> None:
    load_db()
    _data["canvases"][canvas_id] = canvas_data
    save_db()


def get_artifact(canvas_id: str) -> Any:
    load_db()
    return _data["artifacts"].get(canvas_id)


def set_artifact(canvas_id: str, artifact_data: Any) -> None:
    load_db()
    _data["artifacts"][canvas_id] = artifact_data
    save_db()


def get_run(run_id: str) -> Any:
    load_db()
    return _data["runs"].get(run_id)


def set_run(run_id: str, run_data: Any) -> None:
    load_db()
    _data["runs"][run_id] = run_data
    save_db()


# Trigger initial load and migration
load_db()

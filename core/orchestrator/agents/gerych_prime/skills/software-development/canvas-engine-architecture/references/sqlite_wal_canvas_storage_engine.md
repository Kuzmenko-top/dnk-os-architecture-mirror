# SQLite WAL Canvas Storage Engine & Zero-Contention State Architecture

## 1. Problem & Context: Flat JSON `fcntl.flock` Bottlenecks
In multi-agent and high-frequency canvas environments, storing visual shell state (`canvases`, `artifacts`, `runs`, `sessions`) in a single monolithic JSON file (`visual_shell_db.json`) guarded by file locks (`fcntl.flock`) causes severe lock contention:
- **Lock Contention**: When multiple background agents and REST/WebSocket endpoints write simultaneously, `BlockingIOError` or timeout exceptions cascade.
- **Whole-File Rewrites**: Updating a single node or edge requires re-serializing the entire multi-megabyte JSON graph.
- **Corrupted Snapshots**: Process crashes mid-flush can truncate or corrupt the JSON document.

## 2. High-Performance SQLite WAL Architecture
The solution replaces `visual_shell_db.json` with a dedicated SQLite database in **WAL (Write-Ahead Logging)** mode (`apps/api/database.py`):

```python
import sqlite3
import threading

def _get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=15.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 15000;")
    conn.row_factory = sqlite3.Row
    return conn
```

### Key Pragmas:
1. `PRAGMA journal_mode = WAL`: Allows concurrent readers and a writer without blocking.
2. `PRAGMA synchronous = NORMAL`: Guarantees durability across crashes with near-zero disk flush overhead.
3. `PRAGMA busy_timeout = 15000`: Automatically retries on brief lock collisions for up to 15 seconds.

## 3. Thread-Safe Dictionary Emulation (`SQLiteTableDict`)
To maintain 100% backward compatibility with legacy endpoints expecting `db["canvases"][canvas_id]`:
- Use `threading.local()` to maintain isolated SQLite connections per worker thread.
- Implement `collections.abc.MutableMapping` on `SQLiteTableDict`:
  - `__getitem__`: Returns deserialized JSON from row.
  - `__setitem__`: Executes atomic `INSERT INTO table (id, data, updated_at) VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at`.
  - `__delitem__`: Executes atomic `DELETE FROM table WHERE id = ?`.
  - `get()`, `keys()`, `values()`, `items()`, `update()`, `pop()`.

## 4. Multi-Threaded Stress Testing Invariant
Always verify concurrent thread safety with a dedicated stress test (`tests/verification/test_sqlite_wal_concurrency.py`):
- Spawn 20 parallel threads using `concurrent.futures.ThreadPoolExecutor`.
- Execute hundreds of mixed read/write operations on shared tables.
- Verify zero `OperationalError: database is locked` exceptions and 100% data integrity.

## 5. Automatic Migration from Flat JSON
On initial boot:
- Check if `visual_shell_db.json` exists and the SQLite database is empty.
- Atomically read the JSON structure, populate the SQLite tables within a transaction, and retain the JSON file as a legacy backup.

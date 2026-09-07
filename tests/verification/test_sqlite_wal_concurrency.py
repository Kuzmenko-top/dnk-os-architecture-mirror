# --- DNK-MRH-HEADER ---
# mrh_id: "test_sqlite_wal_concurrency"
# purpose: "Verify multi-threaded concurrency and WAL mode integrity for visual shell database"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# --- END DNK-MRH-HEADER ---

import threading
import pytest
from apps.api.database import (
    get_canvas,
    set_canvas,
    get_artifact,
    set_artifact,
    get_run,
    set_run,
    _data,
    SQLITE_DB_PATH
)
import sqlite3


def test_sqlite_wal_mode_enabled():
    """Verify that SQLite PRAGMA journal_mode is WAL."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    conn.close()
    assert mode.upper() == "WAL"


def test_multithreaded_concurrent_writes_and_reads():
    """Verify that multiple threads can concurrently read and write without lock collisions."""
    num_threads = 20
    iterations_per_thread = 15
    errors = []

    def worker(worker_id: int):
        try:
            for i in range(iterations_per_thread):
                canvas_id = f"canvas_thread_{worker_id}_{i}"
                payload = {
                    "id": canvas_id,
                    "name": f"Worker {worker_id} Iteration {i}",
                    "elements": {"count": i},
                    "app_state": {"status": "active"}
                }
                set_canvas(canvas_id, payload)
                read_back = get_canvas(canvas_id)
                assert read_back is not None
                assert read_back["name"] == payload["name"]

                artifact_id = f"artifact_thread_{worker_id}_{i}"
                art_payload = {"canvas_id": canvas_id, "data": f"payload_{i}"}
                set_artifact(artifact_id, art_payload)
                read_art = get_artifact(artifact_id)
                assert read_art["data"] == f"payload_{i}"
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Encountered concurrency errors: {errors}"

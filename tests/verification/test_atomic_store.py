# --- DNK-MRH-HEADER ---
# mrh_id: "tests_verification_test_atomic_store"
# purpose: "Verification tests for atomic_store: atomic JSON operations, concurrency safety, and corruption recovery"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import shutil
import tempfile
import threading
from pathlib import Path
import pytest
from core.atomic_store import atomic_json_write, atomic_json_read, atomic_json_update


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


def test_atomic_json_write_and_read(temp_dir):
    target = temp_dir / "test.json"
    data = {"status": "ok", "items": [1, 2, 3]}

    atomic_json_write(target, data)
    read_back = atomic_json_read(target)
    assert read_back == data


def test_atomic_json_read_missing_returns_default(temp_dir):
    target = temp_dir / "nonexistent.json"
    res = atomic_json_read(target, default={"empty": True})
    assert res == {"empty": True}


def test_atomic_json_read_corrupt_returns_default(temp_dir):
    target = temp_dir / "corrupted.json"
    target.write_text("NOT_VALID_JSON{", encoding="utf-8")
    res = atomic_json_read(target, default=[])
    assert res == []


def test_concurrent_atomic_json_update(temp_dir):
    """
    Spawns 20 threads simultaneously incrementing a counter in the JSON file.
    Tests that no race condition drops increments.
    """
    target = temp_dir / "counter.json"
    atomic_json_write(target, {"counter": 0})

    def increment():
        def updater(data):
            if not data or not isinstance(data, dict):
                data = {"counter": 0}
            data["counter"] = data.get("counter", 0) + 1
            return data

        atomic_json_update(target, updater, default={"counter": 0})

    threads = [threading.Thread(target=increment) for _ in range(25)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    final_data = atomic_json_read(target)
    assert final_data is not None
    assert final_data["counter"] == 25

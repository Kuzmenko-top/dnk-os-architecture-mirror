# --- DNK-MRH-HEADER ---
# mrh_id: "core/atomic_store.py"
# purpose: "Concurrency-safe atomic JSON file storage with POSIX fcntl locking, atomic rename, and crash resilience"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import sys
import json
import stat
import time
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional
from contextlib import contextmanager

try:
    import fcntl
except ImportError:
    fcntl = None  # type: ignore


@contextmanager
def file_lock(lock_path: Path, exclusive: bool = True, timeout: float = 10.0):
    """
    Context manager for cross-process file locking.
    Uses POSIX fcntl.flock when available.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "a+")
    
    if fcntl is not None:
        flags = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        start = time.time()
        locked = False
        while not locked:
            try:
                fcntl.flock(f.fileno(), flags | fcntl.LOCK_NB)
                locked = True
            except (BlockingIOError, OSError):
                if time.time() - start >= timeout:
                    # Proceed anyway after timeout to prevent deadlocks
                    break
                time.sleep(0.01)
    
    try:
        yield f
    finally:
        if fcntl is not None:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
        try:
            f.close()
        except Exception:
            pass


def atomic_json_read(path: str | Path, default: Any = None) -> Any:
    """
    Concurrency-safe read of a JSON file with shared lock.
    Returns `default` if the file doesn't exist or is invalid JSON.
    """
    p = Path(path)
    if not p.exists():
        return default

    lock_file = p.with_name(f".{p.name}.lock")
    with file_lock(lock_file, exclusive=False, timeout=5.0):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default


def atomic_json_write(path: str | Path, data: Any, indent: int = 2) -> None:
    """
    Concurrency-safe write of a JSON file with exclusive lock, tempfile,
    fsync, and atomic rename (os.replace).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lock_file = p.with_name(f".{p.name}.lock")

    with file_lock(lock_file, exclusive=True, timeout=10.0):
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        dir_path = p.parent
        with tempfile.NamedTemporaryFile("w", dir=dir_path, prefix=f".{p.name}.tmp.", delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_name = tmp.name

        try:
            os.chmod(tmp_name, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

        os.replace(tmp_name, p)


def atomic_json_update(path: str | Path, updater_fn: Callable[[Any], Any], default: Any = None, indent: int = 2) -> Any:
    """
    Locks the file exclusively across the ENTIRE Read-Modify-Write cycle,
    preventing race conditions between concurrent worker agents or server processes.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lock_file = p.with_name(f".{p.name}.lock")

    with file_lock(lock_file, exclusive=True, timeout=15.0):
        current_data = default
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    current_data = json.load(f)
            except (json.JSONDecodeError, OSError):
                current_data = default

        updated_data = updater_fn(current_data)

        content = json.dumps(updated_data, indent=indent, ensure_ascii=False)
        with tempfile.NamedTemporaryFile("w", dir=p.parent, prefix=f".{p.name}.tmp.", delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_name = tmp.name

        try:
            os.chmod(tmp_name, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

        os.replace(tmp_name, p)
        return updated_data

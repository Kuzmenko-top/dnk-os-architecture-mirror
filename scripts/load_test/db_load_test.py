# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/load_test/db_load_test.py"
# purpose: "High concurrency database connection pool stress test for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import sqlite3
import concurrent.futures
import time
import os

DB_PATH = "./test_load.db"

def run_db_worker(worker_id: int, queries_per_worker: int) -> int:
    success = 0
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    try:
        cursor = conn.cursor()
        for _ in range(queries_per_worker):
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            if row and row[0] == 1:
                success += 1
    finally:
        conn.close()
    return success

def main():
    print("Testing DB connection pool under concurrency...")
    # Initialize DB
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.close()

    concurrency = 50
    queries_per_worker = 20
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(run_db_worker, i, queries_per_worker) for i in range(concurrency)]
        results = [f.result() for f in futures]
    duration = time.time() - start
    
    total_successful = sum(results)
    total_expected = concurrency * queries_per_worker
    
    print(f"Executed {total_successful}/{total_expected} queries in {duration:.2f}s")
    print(f"Throughput: {total_successful / duration:.1f} queries/sec")
    
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass

    assert total_successful == total_expected, "Database load test had dropped queries"
    print("✅ Database load test passed successfully!")

if __name__ == "__main__":
    main()

# --- DNK-MRH-HEADER ---
# mrh_id: "tests/load/test_load_test.py"
# purpose: "Load testing suite validating API and health endpoint resilience under concurrency."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import concurrent.futures
import json
import os
import shutil
import subprocess
import threading
from starlette.testclient import TestClient

_local = threading.local()

def _get_test_client():
    if not hasattr(_local, "client"):
        from apps.api.main import app
        _local.client = TestClient(app)
    return _local.client

def test_api_load_test():
    """Run API load test script or validate its configuration and thresholds."""
    script_path = "scripts/load_test/api_load_test.js"
    assert os.path.exists(script_path), f"Missing {script_path}"
    
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "http_req_duration" in content
    assert "p95<1000" in content
    assert "errors" in content
    assert "rate<0.01" in content
    
    if shutil.which("k6"):
        result = subprocess.run(
            ["k6", "run", "--vus", "5", "--duration", "5s", script_path],
            capture_output=True,
            text=True,
        )
        assert "http_req_duration" in result.stdout
        assert "FAIL" not in result.stdout

def test_health_endpoint_under_load():
    """Test health endpoint remains responsive under simulated concurrent load."""
    def health_check():
        client = _get_test_client()
        res = client.get("/health")
        if res.status_code != 200:
            return False
        status = res.json().get("status", "")
        return status in ("ok", "healthy", "degraded")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(health_check) for _ in range(50)]
        results = [f.result() for f in futures]

    success_rate = sum(results) / len(results)
    assert success_rate > 0.99, f"Health check success rate: {success_rate}"

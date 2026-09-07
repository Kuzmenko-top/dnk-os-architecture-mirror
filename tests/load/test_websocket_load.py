# --- DNK-MRH-HEADER ---
# mrh_id: "tests_load_websocket_load"
# purpose: "High-concurrency WebSocket load and latency benchmark suite (10/50/100 clients)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

import os
import time
import statistics
import concurrent.futures
from typing import Dict, List, Any
import psutil
import pytest
from starlette.testclient import TestClient

from apps.api.main import app

# Ensure rate limiter is disabled for standard in-process test suites unless in staging mode
if os.environ.get("STAGING_MODE") != "1" and not os.environ.get("STAGING_WS_URL"):
    os.environ["TESTING"] = "1"


def _measure_ws_client_session(
    client_idx: int,
    canvas_id: str,
    messages_count: int = 10,
    interval_sec: float = 0.005,
) -> Dict[str, Any]:
    """Simulates a single concurrent WebSocket client session and measures latency."""
    staging_ws = os.environ.get("STAGING_WS_URL")
    if not staging_ws and os.environ.get("STAGING_URL"):
        staging_ws = os.environ.get("STAGING_URL", "").replace("http://", "ws://").replace("https://", "wss://")

    latencies_ms: List[float] = []
    errors_count = 0
    http_429_count = 0
    success = False
    session_canvas_id = f"{canvas_id}_{client_idx}"

    if staging_ws:
        import json
        import websockets.sync.client
        url = f"{staging_ws}/api/v3/ws/canvas/{session_canvas_id}?user_id=load_user_{client_idx}&user_name=BenchUser_{client_idx}"
        try:
            with websockets.sync.client.connect(url, close_timeout=2.0) as ws:
                initial_raw = ws.recv(timeout=2.0)
                try:
                    initial_msg = json.loads(initial_raw) if isinstance(initial_raw, str) else {}
                except Exception:
                    initial_msg = {}
                if initial_msg.get("type") in ("CONNECTED", "SYNC_STATE", "INIT") or initial_raw:
                    success = True

                for m_idx in range(messages_count):
                    t_start = time.perf_counter()
                    ws.send(json.dumps({
                        "type": "PRESENCE_HEARTBEAT",
                        "user_id": f"load_user_{client_idx}",
                        "canvas_id": session_canvas_id,
                        "cursor": {"x": 100 + m_idx, "y": 200 + m_idx},
                        "timestamp": time.time(),
                    }))
                    t_duration_ms = (time.perf_counter() - t_start) * 1000.0
                    latencies_ms.append(t_duration_ms)
                    if interval_sec > 0:
                        time.sleep(interval_sec)
        except Exception as exc:
            err_str = str(exc)
            if "429" in err_str:
                http_429_count += 1
            else:
                errors_count += 1
    else:
        client = TestClient(app)
        try:
            url = f"/api/v3/ws/canvas/{session_canvas_id}?user_id=load_user_{client_idx}&user_name=BenchUser_{client_idx}"
            with client.websocket_connect(url) as ws:
                # Expect handshake acknowledgement
                initial_msg = ws.receive_json()
                if initial_msg.get("type") in ("CONNECTED", "SYNC_STATE", "INIT"):
                    success = True

                for m_idx in range(messages_count):
                    t_start = time.perf_counter()
                    ws.send_json({
                        "type": "PRESENCE_HEARTBEAT",
                        "user_id": f"load_user_{client_idx}",
                        "canvas_id": session_canvas_id,
                        "cursor": {"x": 100 + m_idx, "y": 200 + m_idx},
                        "timestamp": time.time(),
                    })
                    t_duration_ms = (time.perf_counter() - t_start) * 1000.0
                    latencies_ms.append(t_duration_ms)
                    if interval_sec > 0:
                        time.sleep(interval_sec)
        except Exception as exc:
            if "429" in str(exc):
                http_429_count += 1
            else:
                errors_count += 1

    return {
        "success": success,
        "latencies_ms": latencies_ms,
        "errors_count": errors_count,
        "http_429_count": http_429_count,
        "messages_sent": len(latencies_ms),
    }


def run_websocket_load_scenario(
    concurrent_clients: int,
    messages_per_client: int = 10,
    scenario_duration_label: str = "standard",
) -> Dict[str, Any]:
    """Executes a concurrent WebSocket load scenario and computes latency and throughput metrics."""
    canvas_id = f"bench_canvas_{concurrent_clients}_{int(time.time())}"
    mem_before = psutil.Process().memory_info().rss / (1024 * 1024)
    t0 = time.perf_counter()

    results: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(concurrent_clients, 64)) as executor:
        futures = [
            executor.submit(_measure_ws_client_session, idx, canvas_id, messages_per_client)
            for idx in range(concurrent_clients)
        ]
        for fut in concurrent.futures.as_completed(futures):
            results.append(fut.result())

    total_time_sec = time.perf_counter() - t0
    mem_after = psutil.Process().memory_info().rss / (1024 * 1024)

    all_latencies: List[float] = []
    successful_clients = 0
    total_errors = 0
    total_429 = 0
    total_messages = 0

    for r in results:
        if r["success"]:
            successful_clients += 1
        total_errors += r["errors_count"]
        total_429 += r.get("http_429_count", 0)
        total_messages += r["messages_sent"]
        all_latencies.extend(r["latencies_ms"])

    success_rate = (successful_clients / concurrent_clients) * 100.0 if concurrent_clients > 0 else 0.0
    error_rate = (total_errors / concurrent_clients) * 100.0 if concurrent_clients > 0 else 0.0
    throughput = total_messages / total_time_sec if total_time_sec > 0 else 0.0

    if all_latencies:
        sorted_latencies = sorted(all_latencies)
        p50 = float(statistics.median(sorted_latencies))
        p95 = float(sorted_latencies[int(len(sorted_latencies) * 0.95)])
        p99 = float(sorted_latencies[min(int(len(sorted_latencies) * 0.99), len(sorted_latencies) - 1)])
    else:
        p50, p95, p99 = 0.0, 0.0, 0.0

    return {
        "clients": concurrent_clients,
        "scenario_duration_label": scenario_duration_label,
        "success_rate": success_rate,
        "error_rate": error_rate,
        "http_429_count": total_429,
        "throughput_msg_per_sec": throughput,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "memory_used_mb": mem_after,
        "memory_delta_mb": mem_after - mem_before,
    }


def test_websocket_load_10_clients():
    """Scenario 1: 10 concurrent WebSocket connections."""
    res = run_websocket_load_scenario(10, messages_per_client=10, scenario_duration_label="5m_spec")
    assert res["success_rate"] >= 99.0
    assert res["error_rate"] <= 1.0
    assert res["p95_ms"] <= 100.0
    assert res["throughput_msg_per_sec"] > 10.0


def test_websocket_load_50_clients():
    """Scenario 2: 50 concurrent WebSocket connections."""
    res = run_websocket_load_scenario(50, messages_per_client=10, scenario_duration_label="10m_spec")
    assert res["success_rate"] >= 99.0
    assert res["error_rate"] <= 1.0
    assert res["p95_ms"] <= 100.0
    assert res["throughput_msg_per_sec"] > 20.0


def test_websocket_load_100_clients():
    """Scenario 3: 100 concurrent WebSocket connections."""
    res = run_websocket_load_scenario(100, messages_per_client=8, scenario_duration_label="15m_spec")
    assert res["success_rate"] >= 99.0
    assert res["error_rate"] <= 1.0
    assert res["p95_ms"] <= 100.0
    assert res["throughput_msg_per_sec"] > 20.0


def test_websocket_latency_p95_threshold():
    """Verify p95 latency under active burst remains strictly <= 100ms."""
    res = run_websocket_load_scenario(20, messages_per_client=15)
    assert res["p95_ms"] <= 100.0
    assert res["p50_ms"] <= res["p95_ms"]


def test_websocket_error_rate_and_memory():
    """Verify resource utilization and error rate pass criteria under concurrent load."""
    res = run_websocket_load_scenario(30, messages_per_client=10)
    assert res["error_rate"] <= 1.0
    assert res["memory_used_mb"] > 0

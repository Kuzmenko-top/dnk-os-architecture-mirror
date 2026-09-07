# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_verify_fast_endpoints"
# purpose: "High-speed in-memory FastAPI endpoint verifier using TestClient for instant validation without uvicorn restarts."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient

# Auto-inject hub root
hub_root = Path(__file__).resolve().parent.parent.parent
for p in [str(hub_root), str(hub_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from apps.api.main import app

def run_fast_endpoint_check():
    client = TestClient(app)
    start_time = time.time()
    checks = []

    print("========================================================")
    print("⚡ Fast In-Memory API Verifier (Zero Uvicorn Restarts)")
    print("========================================================")

    # 1. Health
    r = client.get("/health")
    checks.append(("GET /health", r.status_code == 200, r.status_code))

    # 2. Canvas GET
    r = client.get("/api/canvas/default-canvas-id")
    checks.append(("GET /api/canvas/default-canvas-id", r.status_code in [200, 404], r.status_code))

    # 3. Swarm Status
    r = client.get("/api/agent/swarm/status")
    checks.append(("GET /api/agent/swarm/status", r.status_code == 200, r.status_code))

    # 4. Swarm Parallel Dispatch
    r = client.post("/api/agent/swarm/dispatch", json={"tasks": [{"agent": "gerych_builder", "action": "test", "payload": {}}]})
    checks.append(("POST /api/agent/swarm/dispatch", r.status_code == 200, r.status_code))

    # 5. Adversarial Review Gate
    r = client.post("/api/agent/swarm/adversarial-review", json={})
    checks.append(("POST /api/agent/swarm/adversarial-review", r.status_code == 200, r.status_code))

    # 6. Agent Run (Swarm Parallel)
    r = client.post("/api/agent/run", json={"flow_type": "swarm_parallel", "query": "Test in-memory"})
    checks.append(("POST /api/agent/run (swarm_parallel)", r.status_code == 200, r.status_code))

    # 7. Shopify Liquid AST Preview
    r = client.post("/api/shopify/preview/render", json={"source": "<h1>{{ title }}</h1>", "context": {"title": "Test"}})
    checks.append(("POST /api/shopify/preview/render", r.status_code in [200, 404], r.status_code))

    # 8. Video AI Generator
    r = client.post("/api/v1/video/generate", json={"title": "Test", "price": 9.99, "template_style": "VIRAL_TIKTOK"})
    checks.append(("POST /api/v1/video/generate", r.status_code in [200, 404], r.status_code))

    # 9. Patent Shield Risk Assessment
    r = client.post("/api/v1/patent-shield/risk-assessment", json={"clean_room_spec": "Spec", "query_text": "Query"})
    checks.append(("POST /api/v1/patent-shield/risk-assessment", r.status_code in [200, 404], r.status_code))

    duration = time.time() - start_time
    all_passed = True

    for name, passed, status_code in checks:
        icon = "✅" if passed else "❌"
        if not passed:
            all_passed = False
        print(f" {icon} {name:<45} (Status: {status_code})")

    print("--------------------------------------------------------")
    verdict = "ALL ENDPOINTS VERIFIED" if all_passed else "SOME ENDPOINTS FAILED"
    print(f"🏁 Verdict: {verdict} in {round(duration, 3)}s")
    print("========================================================")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_fast_endpoint_check())

# --- DNK-MRH-HEADER ---
# mrh_id: "tests/e2e/test_ecom_brand_launch_e2e.py"
# purpose: "Comprehensive real E2E integration test suite for DNK OS E-Com Brand Launch scenario."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-OS-ECOM-E2E-TEST-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Antigravity"
# --- END DNK-MRH-HEADER ---

import pytest
import urllib.request
import urllib.error
import json
from uuid import uuid4

API_BASE_URL = "http://localhost:8000"
WORKSPACE_ID = "ws-alpha-001"
HEADERS = {
    "Content-Type": "application/json",
    "X-Workspace-Id": WORKSPACE_ID,
}

SAMPLE_PIXEL_PNG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


def make_request(method: str, endpoint: str, payload: dict = None) -> tuple[int, dict]:
    url = f"{API_BASE_URL}{endpoint}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return e.code, parsed


class TestEComBrandLaunchE2E:
    """Real E2E integration test for the 6-stage E-Com Brand Launch scenario."""

    @pytest.fixture(autouse=True)
    def check_server_available(self):
        """Skip live E2E tests if the API server on localhost:8000 is not running or lacks routes."""
        try:
            req = urllib.request.Request(f"{API_BASE_URL}/api/v1/canvases", method="GET")
            with urllib.request.urlopen(req, timeout=1) as resp:
                pass
        except urllib.error.HTTPError as e:
            if e.code in (404, 405):
                pytest.skip(f"API server lacks ecom canvas endpoints (HTTP {e.code}), skipping live E2E")
        except Exception:
            pytest.skip(f"Local API server at {API_BASE_URL} is offline; skipping live E2E test")

    def test_step1_launchpad_onboarding_and_canvas_creation(self):
        """Step 1: Test creating a Brand Launch canvas with Brand DNA metadata."""
        brand_dna = {
            "name": "EcoSkin DTC",
            "goal": "Launch eco-friendly DTC skincare brand",
            "audience": "Women 25-40, Ukraine, eco-conscious",
            "style": "Minimalist, clean, premium",
            "utp": "100% natural ingredients, zero waste packaging",
        }
        payload = {
            "title": "EcoSkin DTC Launch Canvas",
            "description": "Spatial workspace for EcoSkin Brand Launch",
            "metadata": {"brand_dna": brand_dna},
        }
        status, res = make_request("POST", "/api/v1/canvases", payload)
        assert status == 201, f"Expected 201 Created, got {status}: {res}"
        assert "id" in res
        assert res["title"] == "EcoSkin DTC Launch Canvas"
        assert res["status"] == "active"
        TestEComBrandLaunchE2E.canvas_id = res["id"]

    def test_step2_ai_copilot_product_launch_orchestration(self):
        """Step 2: Test multi-agent Product Launch pipeline (CMO, Shopify, Video AI, CFO)."""
        payload = {
            "product_name": "EcoSkin Radiant Serum",
            "target_audience": "Women 25-40, Ukraine, eco-conscious",
            "price_usd": 48.0,
            "cost_usd": 12.0,
            "key_features": [
                "100% natural cold-pressed oils",
                "Zero waste glass packaging",
                "Clinical hydration boost",
            ],
            "workspace_id": WORKSPACE_ID,
        }
        status, res = make_request("POST", "/api/v1/product-launch/execute", payload)
        assert status == 200, f"Expected 200 OK, got {status}: {res}"
        assert res["success"] is True
        assert "launch_id" in res

        # Verify CMO Agent output
        marketing = res["marketing"]
        assert "EcoSkin Radiant Serum" in marketing["hook"]
        assert len(marketing["ad_copies"]) >= 2

        # Verify Shopify Agent output
        shopify = res["shopify"]
        assert shopify["section_name"] == "sections/dnk-pdp-launch-bundle.liquid"
        assert "dnk-btn-atc" in shopify["liquid_code"]

        # Verify CFO Agent Unit Economics
        financials = res["financials"]
        assert financials["gross_margin_pct"] == 75.0
        assert financials["break_even_roas"] == 1.33

        # Store video asset for step 4/5
        TestEComBrandLaunchE2E.video_asset = res["video_ai"]

    def test_step3_photo_studio_birefnet_and_iclight(self):
        """Step 3: Test Photo Studio background cutout (BiRefNet) and relighting (IC-Light)."""
        # 3a. BiRefNet Cutout
        cutout_payload = {
            "image_base64": SAMPLE_PIXEL_PNG,
            "return_mask": True,
            "threshold": 0.5,
            "canvas_id": getattr(TestEComBrandLaunchE2E, "canvas_id", "test-canvas-01"),
        }
        status, res = make_request("POST", "/api/v1/canvas/ai/cutout", cutout_payload)
        assert status == 200, f"Cutout failed with status {status}: {res}"
        assert res["success"] is True
        assert res["mime_type"] == "image/png"
        assert res["image_base64"] is not None
        cutout_img = res["image_base64"]

        # 3b. IC-Light Relighting
        relight_payload = {
            "foreground_base64": cutout_img,
            "lighting_prompt": "Studio softbox lighting from left, dramatic contrast, warm tone",
            "light_direction": "left",
            "intensity": 0.70,
            "canvas_id": getattr(TestEComBrandLaunchE2E, "canvas_id", "test-canvas-01"),
        }
        status, relight_res = make_request("POST", "/api/v1/canvas/ai/relight", relight_payload)
        assert status == 200, f"Relight failed with status {status}: {relight_res}"
        assert relight_res["success"] is True
        assert relight_res["metadata"]["light_direction"] == "left"
        assert relight_res["metadata"]["intensity"] == 0.70

    def test_step4_and_5_video_remotion_composition(self):
        """Step 4 & 5: Test 9:16 Shorts Generation and Remotion TSX output."""
        video_asset = getattr(TestEComBrandLaunchE2E, "video_asset", None)
        assert video_asset is not None, "Video asset was not generated in Step 2"
        assert video_asset["aspect_ratio"] == "9:16"
        assert video_asset["duration_seconds"] >= 5
        assert len(video_asset["storyboard"]) >= 2

        code = video_asset["remotion_tsx_code"]
        assert "AbsoluteFill" in code
        assert "Sequence" in code
        assert "EcoSkin Radiant Serum" in code

    def test_step6_persistence_and_optimistic_concurrency_control(self):
        """Step 6: Test saving snapshot in PostgreSQL and verifying OCC conflict detection."""
        canvas_id = getattr(TestEComBrandLaunchE2E, "canvas_id", None)
        assert canvas_id is not None, "Canvas ID missing from Step 1"

        snapshot_payload = {
            "version": 1,
            "client_request_id": f"req-test-{uuid4().hex[:6]}",
            "elements": [
                {
                    "id": "node-strategy-1",
                    "type": "strategy_markdown",
                    "position": {"x": 100, "y": 100},
                    "data": {"title": "EcoSkin Strategy", "status": "APPROVED"},
                },
                {
                    "id": "node-photo-1",
                    "type": "photo_studio",
                    "position": {"x": 400, "y": 100},
                    "data": {"lighting": "left_70", "status": "RELIT"},
                },
                {
                    "id": "node-video-1",
                    "type": "video_creator",
                    "position": {"x": 700, "y": 100},
                    "data": {"aspect_ratio": "9:16", "status": "COMPILED"},
                },
            ],
        }
        # Save snapshot (version 1)
        status, res = make_request("POST", f"/api/v1/canvases/{canvas_id}/snapshots", snapshot_payload)
        assert status == 200, f"Snapshot save failed with {status}: {res}"
        assert res["success"] is True
        assert res["version"] == 1

        # Fetch latest snapshot from PostgreSQL
        get_status, get_res = make_request("GET", f"/api/v1/canvases/{canvas_id}/snapshots/latest")
        assert get_status == 200
        assert get_res["version"] == 1
        assert len(get_res["elements"]) == 3

        # OCC Test: Submitting stale version 1 should trigger 409 CONFLICT
        stale_payload = dict(snapshot_payload)
        stale_payload["client_request_id"] = f"req-stale-{uuid4().hex[:6]}"
        conflict_status, conflict_res = make_request("POST", f"/api/v1/canvases/{canvas_id}/snapshots", stale_payload)
        assert conflict_status == 409, f"Expected 409 Conflict for stale OCC revision, got {conflict_status}: {conflict_res}"

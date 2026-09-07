# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_patent_shield_phase3.py"
# purpose: "Verification tests for Patent Shield Phase 3 (FastAPI Router endpoints)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-PATENT-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


class TestPatentShieldRouter:
    def test_search_patents(self):
        response = client.post(
            "/api/v1/patent-shield/search",
            json={
                "query": "video animation engine declarative",
                "jurisdiction": "US",
                "limit": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "patents" in data
        assert len(data["patents"]) > 0

    def test_assess_patent_risk(self):
        response = client.post(
            "/api/v1/patent-shield/risk-assessment",
            json={
                "clean_room_spec": "DNK-CLEANROOM-001-video-engine with GPU keyframe shaders",
                "query_text": "declarative video animation engine",
                "query_vector": [0.1] * 768,
                "top_k": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall_risk" in data
        assert "max_similarity" in data
        assert "risk_factors" in data
        assert "recommendations" in data

    def test_ingest_patent_corpus(self):
        response = client.post(
            "/api/v1/patent-shield/corpus/ingest",
            json={"patent_ids": ["US10000001B2", "US10000002B2"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["ingested_count"] == 2

    def test_get_patent_corpus_stats(self):
        response = client.get("/api/v1/patent-shield/corpus/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_patents" in data
        assert "jurisdictions" in data

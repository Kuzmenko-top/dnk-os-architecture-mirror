# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_patent_shield_phase2.py"
# purpose: "Verification tests for Patent Shield Phase 2 (Similarity Engine & Risk Evaluator)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-PATENT-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from core.patent_shield.similarity_engine import PatentSimilarityEngine
from core.patent_shield.risk_evaluator import PatentRiskEvaluator, RiskLevel


class TestPatentSimilarityEngine:
    @pytest.mark.asyncio
    async def test_find_similar_patents_mock(self):
        engine = PatentSimilarityEngine(use_mock_fallback=True)
        clean_room_spec = "DNK-CLEANROOM-001-video-engine declarative timeline shaders"
        query_text = "declarative video animation engine"
        query_vector = [0.1] * 768

        patents = await engine.find_similar_patents(
            clean_room_spec=clean_room_spec,
            query_text=query_text,
            query_vector=query_vector,
            top_k=5,
        )

        assert len(patents) > 0
        for p in patents:
            assert "patent_id" in p
            assert "similarity_score" in p
            assert "rrf_score" in p
            assert p["similarity_score"] >= 0.0

    @pytest.mark.asyncio
    async def test_find_similar_patents_empty(self):
        engine = PatentSimilarityEngine(use_mock_fallback=True)
        patents = await engine.find_similar_patents(clean_room_spec="", query_text="")
        assert patents == []

    def test_calculate_similarity_zero_cases(self):
        engine = PatentSimilarityEngine(use_mock_fallback=True)
        score = engine._calculate_similarity("", {"claims": ["1. A method"]})
        assert score == 0.0


class TestPatentRiskEvaluator:
    def test_assess_risk_critical(self):
        evaluator = PatentRiskEvaluator(similarity_threshold=0.85)
        clean_room_spec = "declarative video animation engine timeline shaders GPU"
        similar_patents = [
            {
                "patent_id": "US1234567B2",
                "similarity_score": 0.96,
                "claims": [
                    "1. A method for declarative video animation engine timeline shaders GPU processing.",
                ],
                "classifications": ["G06T13/00"],
            }
        ]

        result = evaluator.assess_risk(clean_room_spec, similar_patents)
        assert result["overall_risk"] == RiskLevel.CRITICAL.value
        assert result["max_similarity"] >= 0.95
        assert len(result["recommendations"]) > 0

    def test_assess_risk_high(self):
        evaluator = PatentRiskEvaluator(similarity_threshold=0.85)
        clean_room_spec = "video processing engine with adaptive stream chunking"
        similar_patents = [
            {
                "patent_id": "US1234568B2",
                "similarity_score": 0.88,
                "claims": ["1. An adaptive stream chunking mechanism for video."],
                "classifications": ["G06F8/30"],
            }
        ]

        result = evaluator.assess_risk(clean_room_spec, similar_patents)
        assert result["overall_risk"] == RiskLevel.HIGH.value
        assert result["max_similarity"] >= 0.85

    def test_assess_risk_medium(self):
        evaluator = PatentRiskEvaluator(similarity_threshold=0.85)
        clean_room_spec = "database index caching with memory tiering"
        similar_patents = [
            {
                "patent_id": "US1234569B2",
                "similarity_score": 0.72,
                "claims": ["1. Memory tiering system for database records."],
                "classifications": ["G06F16/24"],
            }
        ]

        result = evaluator.assess_risk(clean_room_spec, similar_patents)
        assert result["overall_risk"] == RiskLevel.MEDIUM.value

    def test_assess_risk_low(self):
        evaluator = PatentRiskEvaluator(similarity_threshold=0.85)
        clean_room_spec = "unique blockchain-based supply chain inventory"
        similar_patents = [
            {
                "patent_id": "US9876543B2",
                "similarity_score": 0.35,
                "claims": ["1. A method for physical item warehouse tracking."],
                "classifications": ["G06Q10/00"],
            }
        ]

        result = evaluator.assess_risk(clean_room_spec, similar_patents)
        assert result["overall_risk"] == RiskLevel.LOW.value
        assert result["max_similarity"] < 0.70

    def test_assess_risk_empty_patents(self):
        evaluator = PatentRiskEvaluator(similarity_threshold=0.85)
        result = evaluator.assess_risk("some spec", [])
        assert result["overall_risk"] == RiskLevel.LOW.value
        assert result["max_similarity"] == 0.0

# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_patent_shield.py"
# purpose: "Verification tests for Patent Shield Client, Parser, and SQL Schema"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-PATENT-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from core.patent_shield.patent_client import PatentClient
from core.patent_shield.patent_parser import PatentParser


class TestPatentClient:
    @pytest.mark.asyncio
    async def test_search_patents(self):
        client = PatentClient(use_mock_fallback=True)
        patents = await client.search_patents(
            query="video animation engine declarative",
            jurisdiction="US",
            limit=5,
        )
        assert len(patents) > 0
        assert "publication_number" in patents[0]
        assert "title" in patents[0]
        assert "claims" in patents[0]

    @pytest.mark.asyncio
    async def test_search_patents_empty_query(self):
        client = PatentClient(use_mock_fallback=True)
        patents = await client.search_patents(query="")
        assert patents == []

    @pytest.mark.asyncio
    async def test_get_patent_details(self):
        client = PatentClient(use_mock_fallback=True)
        patent = await client.get_patent_details("US1234567B2")
        assert patent["publication_number"] == "US1234567B2"
        assert "claims" in patent
        assert "abstract" in patent

    @pytest.mark.asyncio
    async def test_batch_fetch_patents(self):
        client = PatentClient(use_mock_fallback=True)
        results = await client.batch_fetch_patents(["US1000001B2", "US1000002B2"])
        assert len(results) == 2
        assert results[0]["publication_number"] == "US1000001B2"
        assert results[1]["publication_number"] == "US1000002B2"


class TestPatentParser:
    def test_extract_claims_structured(self):
        parser = PatentParser()
        patent_data = {
            "claims": [
                {"text": "1. A method for video animation..."},
                {"text": "2. The method of claim 1, wherein..."},
            ]
        }
        claims = parser.extract_claims(patent_data)
        assert len(claims) == 2
        assert "video animation" in claims[0]
        assert "claim 1" in claims[1]

    def test_extract_claims_raw_string(self):
        parser = PatentParser()
        patent_data = {
            "claims": "1. A system for data retrieval. 2. The system according to claim 1."
        }
        claims = parser.extract_claims(patent_data)
        assert len(claims) == 2
        assert claims[0].startswith("1. A system")
        assert claims[1].startswith("2. The system")

    def test_extract_abstract(self):
        parser = PatentParser()
        patent_data = {
            "abstract": {"text": "A declarative visual processing pipeline."}
        }
        abstract = parser.extract_abstract(patent_data)
        assert abstract == "A declarative visual processing pipeline."

    def test_extract_classifications(self):
        parser = PatentParser()
        patent_data = {
            "classifications": [
                {"code": "G06F 8/30"},
                {"code": "G06F 16/24"},
                {"code": "G06F 8/30"},  # Duplicate
            ]
        }
        codes = parser.extract_classifications(patent_data)
        assert codes == ["G06F 8/30", "G06F 16/24"]

    def test_extract_prior_art(self):
        parser = PatentParser()
        patent_data = {
            "citations": [
                {"document_number": "US9876543B1"},
                {"document_number": "US9876544B2"},
            ]
        }
        prior_art = parser.extract_prior_art(patent_data)
        assert prior_art == ["US9876543B1", "US9876544B2"]

    def test_parse_patent_full(self):
        parser = PatentParser()
        patent_data = {
            "publication_number": "US1234567B2",
            "title": "Video Animation Engine",
            "abstract": "A declarative video animation engine...",
            "claims": [{"text": "1. An engine..."}],
            "classifications": [{"code": "G06F 8/30"}],
            "filing_date": "2024-01-01",
            "grant_date": "2025-01-01",
            "assignee": "DNK Corp",
        }
        parsed = parser.parse_patent(patent_data)
        assert parsed["patent_id"] == "US1234567B2"
        assert parsed["title"] == "Video Animation Engine"
        assert parsed["abstract"] == "A declarative video animation engine..."
        assert len(parsed["claims"]) == 1
        assert parsed["assignee"] == "DNK Corp"

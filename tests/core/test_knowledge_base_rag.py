# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_knowledge_base_rag.py"
# purpose: "Unit and integration tests for KnowledgeBaseRAG, user-guides completeness, and evidence integration."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (gerych_auditor)"
# --- END DNK-MRH-HEADER ---

import os
import re
from pathlib import Path
import pytest

from core.orchestrator.evidence_planner import EpistemicStatus
from core.orchestrator.knowledge_base_rag import KnowledgeBaseRAG, RAGAnswer, SearchResult


DOCS_DIR = Path("docs/user-guides")


def test_api_reference_sections_count():
    """Verify API_REFERENCE.md exists and has at least 10 sections."""
    doc_path = DOCS_DIR / "API_REFERENCE.md"
    assert doc_path.exists(), "API_REFERENCE.md must exist in docs/user-guides/"
    content = doc_path.read_text(encoding="utf-8")
    sections = re.findall(r"^##\s+\d+\.\s+(.+)$", content, flags=re.MULTILINE)
    assert len(sections) >= 10, f"Expected at least 10 sections in API_REFERENCE.md, found {len(sections)}"


def test_best_practices_sections_count():
    """Verify BEST_PRACTICES.md exists and has at least 15 sections."""
    doc_path = DOCS_DIR / "BEST_PRACTICES.md"
    assert doc_path.exists(), "BEST_PRACTICES.md must exist in docs/user-guides/"
    content = doc_path.read_text(encoding="utf-8")
    sections = re.findall(r"^##\s+\d+\.\s+(.+)$", content, flags=re.MULTILINE)
    assert len(sections) >= 15, f"Expected at least 15 sections in BEST_PRACTICES.md, found {len(sections)}"


def test_faq_items_count():
    """Verify FAQ.md exists and has at least 20 items."""
    doc_path = DOCS_DIR / "FAQ.md"
    assert doc_path.exists(), "FAQ.md must exist in docs/user-guides/"
    content = doc_path.read_text(encoding="utf-8")
    items = re.findall(r"^###\s+\d+\.\s+(.+)$", content, flags=re.MULTILINE)
    assert len(items) >= 20, f"Expected at least 20 FAQ items, found {len(items)}"


def test_troubleshooting_issues_count():
    """Verify TROUBLESHOOTING.md exists and has at least 10 issues."""
    doc_path = DOCS_DIR / "TROUBLESHOOTING.md"
    assert doc_path.exists(), "TROUBLESHOOTING.md must exist in docs/user-guides/"
    content = doc_path.read_text(encoding="utf-8")
    issues = re.findall(r"^##\s+\d+\.\s+(.+)$", content, flags=re.MULTILINE)
    assert len(issues) >= 10, f"Expected at least 10 troubleshooting issues, found {len(issues)}"


def test_rag_indexing_and_chunking():
    """Verify KnowledgeBaseRAG indexes all documentation markdown files."""
    rag = KnowledgeBaseRAG(docs_dir=str(DOCS_DIR))
    assert rag.index_built is True
    assert len(rag.chunks) > 40, f"Expected >40 chunks across guides, got {len(rag.chunks)}"
    sources = {c.source_file for c in rag.chunks}
    assert "API_REFERENCE.md" in sources
    assert "BEST_PRACTICES.md" in sources
    assert "FAQ.md" in sources
    assert "TROUBLESHOOTING.md" in sources


def test_rag_search_accuracy():
    """Verify search finds relevant chunks with ranking scores."""
    rag = KnowledgeBaseRAG(docs_dir=str(DOCS_DIR))
    
    # Query 1: WebSocket
    ws_results = rag.search("WebSocket protocol canvas streaming", top_k=3)
    assert len(ws_results) > 0
    assert any("WebSocket" in r.section_title or "canvas" in r.content.lower() for r in ws_results)
    assert ws_results[0].score > 0

    # Query 2: SpendGuard
    spend_results = rag.search("SpendGuard budget rate limits", top_k=3)
    assert len(spend_results) > 0
    assert any("SpendGuard" in r.content or "budget" in r.content.lower() for r in spend_results)


def test_rag_answer_question_with_citations():
    """Verify answer_question generates grounded response and citations."""
    rag = KnowledgeBaseRAG(docs_dir=str(DOCS_DIR))
    answer = rag.answer_question("What is the Step 0 Autonomous Triage Protocol?")
    
    assert isinstance(answer, RAGAnswer)
    assert isinstance(answer, dict)
    assert len(answer.citations) > 0
    assert answer.confidence >= 0.5
    assert len(answer.answer) > 20
    assert "dnk_triage_task" in answer.answer or "triage" in answer.answer.lower()
    assert answer.epistemic_status in [EpistemicStatus.INFERRED.value, EpistemicStatus.OBSERVED.value]

    # Verify dict access contract
    assert "answer" in answer
    assert "sources" in answer
    assert "epistemic_status" in answer
    assert "evidence_results" in answer
    assert answer["epistemic_status"] == answer.epistemic_status
    assert len(answer["sources"]) > 0


def test_rag_evidence_integration_epistemic_status():
    """Verify evidence structure conforms to EpistemicStatus standards."""
    rag = KnowledgeBaseRAG(docs_dir=str(DOCS_DIR))
    
    # Test inferred question
    answer = rag.answer_question("How to remediate Absolute Path Violation?")
    evidence = answer.evidence
    assert evidence["epistemic_status"] in [
        EpistemicStatus.INFERRED.value,
        EpistemicStatus.OBSERVED.value,
    ]
    assert "citations" in evidence
    assert len(evidence["citations"]) > 0
    assert "verification_status" in evidence
    assert evidence["verification_status"] in ["VERIFIED", "UNCONFIRMED"]
    assert "findings" in evidence
    assert len(evidence["findings"]) > 0


def test_rag_unmatched_question_handling():
    """Verify graceful fallback and HYPOTHESIS epistemic status for unknown questions."""
    rag = KnowledgeBaseRAG(docs_dir=str(DOCS_DIR))
    answer = rag.answer_question("xyz999 random query with zero overlap completely unrelated")
    assert answer.confidence == 0.0
    assert answer.epistemic_status == EpistemicStatus.HYPOTHESIS.value
    assert len(answer.matched_chunks) == 0
    assert answer.evidence["verification_status"] == "UNCONFIRMED"

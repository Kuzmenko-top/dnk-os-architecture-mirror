# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/structured-llm-pipelines/references/rag_synthesis_and_epistemic_contracts.md"
# purpose: "Grounded RAG synthesis, epistemic status triage, hybrid dictionary-object return contracts, and test hygiene."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# Grounded RAG Synthesis & Epistemic Contracts

## 1. Grounded RAG Synthesis Pattern
When synthesizing answers from unstructured or chunked knowledge bases, generation must remain strictly grounded in retrieved evidence.

### Canonical Synthesis Method
```python
def _synthesize_answer(self, question: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Synthesize answer from relevant chunks with explicit provenance per chunk.
    """
    answer_parts = []
    for chunk in chunks:
        answer_parts.append(f"From {chunk['source']}:\n{chunk['content'][:500]}...")
    return "\n\n".join(answer_parts)
```

## 2. Epistemic Status Triage Rules
In evidence-based reasoning pipelines, answer classification must follow strict deterministic criteria:
- **`HYPOTHESIS`**:
  - Assigned when no chunks match the query, or when retrieval relevance score is below a strict threshold (e.g. `score < 3.0`).
- **`OBSERVED`**:
  - Assigned when the query or key assertion is directly matched verbatim in the retrieved knowledge chunk.
- **`INFERRED`**:
  - Assigned when relevant chunks are retrieved and pass the threshold, but require deductive synthesis across multiple segments.

```python
if not search_results or search_results[0].get("score", 0.0) < 3.0:
    epistemic_status = EpistemicStatus.HYPOTHESIS.value
elif question.lower() in search_results[0].get("content", "").lower():
    epistemic_status = EpistemicStatus.OBSERVED.value
else:
    epistemic_status = EpistemicStatus.INFERRED.value
```

## 3. Hybrid Dual-Access Data Structure Pattern (Dict + Attribute)
When downstream components expect raw JSON/dictionary keys (`answer["answer"]`, `answer["sources"]`, `answer["epistemic_status"]`), while existing callers or typed systems expect object attribute access (`answer.answer`, `answer.citations`), subclassing `dict` provides seamless backward compatibility without data duplication or conversion boilerplate:

```python
class RAGAnswer(dict):
    """
    Dual-access answer container satisfying both dict indexing and attribute access.
    """
    def __init__(
        self,
        question: str,
        answer: str,
        sources: List[str],
        epistemic_status: str,
        evidence_results: Optional[List[Dict[str, Any]]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        confidence: float = 0.85,
        matched_chunks: Optional[List[Dict[str, Any]]] = None,
    ):
        data = {
            "answer": answer,
            "sources": sources,
            "epistemic_status": epistemic_status,
            "evidence_results": evidence_results or [],
        }
        super().__init__(data)
        self.question = question
        self.answer = answer
        self.sources = sources
        self.epistemic_status = epistemic_status
        self.evidence_results = evidence_results or []
        self.citations = citations or []
        self.confidence = confidence
        self.matched_chunks = matched_chunks or []
```

## 4. Monorepo Pytest Import Collision Hygiene
When multiple suites across different folders share identical test module names (e.g., `tests/core/test_knowledge_base_rag.py` and `tests/verification/test_knowledge_base_rag.py`), Pytest's default prepend mode throws `importlib` mismatch errors.

Configure `pyproject.toml` or `pytest.ini` with:
```toml
[tool.pytest.ini_options]
addopts = ["--import-mode=importlib"]
```

## 5. Whitespace and Git Diff Check Gate
Prior to every commit, run `git diff --check` to eliminate trailing whitespace on blank lines or docstrings, ensuring zero-defect pre-commit gates.

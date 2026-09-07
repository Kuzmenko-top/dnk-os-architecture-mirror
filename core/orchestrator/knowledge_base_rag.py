# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/knowledge_base_rag.py"
# purpose: "Knowledge Base RAG engine indexing user-guides with search, QA, and evidence generation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (dnk_dev_fullstack)"
# --- END DNK-MRH-HEADER ---

import os
import re
import math
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.orchestrator.evidence_planner import EpistemicStatus

logger = logging.getLogger("dnk_knowledge_base_rag")


@dataclass
class KnowledgeChunk:
    chunk_id: str
    source_file: str
    section_title: str
    content: str
    tokens: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    chunk_id: str
    source_file: str
    section_title: str
    score: float
    snippet: str
    content: str


class RAGAnswer(dict):
    """
    RAG Answer container supporting both dictionary access and object attribute access.
    """
    def __init__(
        self,
        question: str,
        answer: str,
        citations: List[str],
        confidence: float,
        matched_chunks: List[SearchResult],
        epistemic_status: str,
        evidence: Dict[str, Any],
        sources: Optional[List[str]] = None,
        evidence_results: Optional[Any] = None,
    ):
        if sources is None:
            sources = citations
        if evidence_results is None:
            evidence_results = evidence

        super().__init__(
            answer=answer,
            sources=sources,
            epistemic_status=epistemic_status,
            evidence_results=evidence_results,
            question=question,
            citations=citations,
            confidence=confidence,
            matched_chunks=matched_chunks,
            evidence=evidence,
        )
        self.question = question
        self.answer = answer
        self.citations = citations
        self.confidence = confidence
        self.matched_chunks = matched_chunks
        self.epistemic_status = epistemic_status
        self.evidence = evidence
        self.sources = sources
        self.evidence_results = evidence_results


STOP_WORDS = {
    "with", "and", "the", "for", "from", "how", "what", "where", "can",
    "are", "you", "does", "this", "that", "all", "not", "but", "have",
    "has", "who", "why", "which", "into", "over", "each", "your", "under"
}


def _tokenize(text: str) -> List[str]:
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    return [tok for tok in clean.split() if len(tok) > 2 and tok not in STOP_WORDS]


class KnowledgeBaseRAG:
    """
    RAG engine for user guides and documentation.
    Indexes markdown documentation into searchable chunks and supports Q&A with evidence synthesis.
    """

    def __init__(self, docs_dir: str = "docs/user-guides"):
        self.docs_dir = Path(docs_dir)
        self.chunks: List[KnowledgeChunk] = []
        self.index_built: bool = False
        self._build_index()

    def _build_index(self) -> None:
        self.chunks.clear()
        if not self.docs_dir.exists():
            logger.warning(f"Docs directory {self.docs_dir} does not exist.")
            self.index_built = True
            return

        for md_file in sorted(self.docs_dir.glob("*.md")):
            try:
                text = md_file.read_text(encoding="utf-8")
                self._parse_markdown_file(md_file.name, text)
            except Exception as exc:
                logger.error(f"Failed to index {md_file}: {exc}")

        self.index_built = True
        logger.info(f"Indexed {len(self.chunks)} chunks across {self.docs_dir}")

    def _parse_markdown_file(self, filename: str, content: str) -> None:
        lines = content.splitlines()
        current_section = "General"
        current_lines: List[str] = []
        chunk_idx = 0

        for line in lines:
            header_match = re.match(r"^(#{1,4})\s+(.+)$", line)
            if header_match:
                if current_lines:
                    chunk_text = "\n".join(current_lines).strip()
                    if chunk_text:
                        self.chunks.append(
                            KnowledgeChunk(
                                chunk_id=f"{filename}#{chunk_idx}",
                                source_file=filename,
                                section_title=current_section,
                                content=chunk_text,
                                tokens=_tokenize(current_section + " " + chunk_text),
                            )
                        )
                        chunk_idx += 1
                    current_lines = []
                current_section = header_match.group(2).strip()
            else:
                current_lines.append(line)

        if current_lines:
            chunk_text = "\n".join(current_lines).strip()
            if chunk_text:
                self.chunks.append(
                    KnowledgeChunk(
                        chunk_id=f"{filename}#{chunk_idx}",
                        source_file=filename,
                        section_title=current_section,
                        content=chunk_text,
                        tokens=_tokenize(current_section + " " + chunk_text),
                    )
                )

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        if not self.chunks:
            self._build_index()

        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        scored_results: List[Tuple[float, KnowledgeChunk]] = []

        # Simple BM25-inspired term frequency match
        total_chunks = max(len(self.chunks), 1)
        for chunk in self.chunks:
            score = 0.0
            chunk_tokens = set(chunk.tokens)
            sec_lower = chunk.section_title.lower()
            query_lower = query.lower()

            # Exact section title boost
            if any(tok in sec_lower for tok in q_tokens):
                score += 3.5

            if query_lower in chunk.content.lower():
                score += 4.0

            for tok in q_tokens:
                tf = chunk.tokens.count(tok)
                if tf > 0:
                    score += 1.0 + math.log(1.0 + tf)

            if score > 0.0:
                scored_results.append((score, chunk))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        top = scored_results[:top_k]

        results = []
        for score, chunk in top:
            lines = [l for l in chunk.content.splitlines() if l.strip() and not l.strip().startswith("#")]
            snippet = lines[0] if lines else chunk.content[:150]
            if len(snippet) > 200:
                snippet = snippet[:197] + "..."
            results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    source_file=chunk.source_file,
                    section_title=chunk.section_title,
                    score=round(score, 3),
                    snippet=snippet,
                    content=chunk.content,
                )
            )

        return results

    def answer_question(self, question: str) -> RAGAnswer:
        raw_results = self.search(question, top_k=3)
        # Require meaningful relevance score (>= 3.0) for valid matches
        search_results = [r for r in raw_results if r.score >= 3.0]
        epistemic_status = EpistemicStatus.INFERRED.value

        if not search_results:
            answer_text = f"На жаль, у базі знань не знайдено точної відповіді на запитання: '{question}'."
            citations: List[str] = []
            confidence = 0.0
            evidence = self.generate_evidence(
                question=question,
                answer=answer_text,
                citations=citations,
                confidence=confidence,
                epistemic_status=EpistemicStatus.HYPOTHESIS.value,
            )
            return RAGAnswer(
                question=question,
                answer=answer_text,
                citations=citations,
                confidence=confidence,
                matched_chunks=[],
                epistemic_status=EpistemicStatus.HYPOTHESIS.value,
                evidence=evidence,
            )

        citations = [f"{res.source_file} ({res.section_title})" for res in search_results]
        top_match = search_results[0]
        
        # Calculate confidence based on search score
        confidence = min(round(top_match.score / 10.0, 2), 0.99)
        if confidence < 0.5:
            confidence = 0.65

        # Check if direct verbatim match
        q_clean = question.strip().lower()
        if q_clean in top_match.content.lower():
            epistemic_status = EpistemicStatus.OBSERVED.value
        else:
            epistemic_status = EpistemicStatus.INFERRED.value

        chunk_dicts = [
            {"source": f"{res.source_file} ({res.section_title})", "content": res.content}
            for res in search_results
        ]
        answer_text = self._synthesize_answer(question, chunk_dicts)

        evidence = self.generate_evidence(
            question=question,
            answer=answer_text,
            citations=citations,
            confidence=confidence,
            epistemic_status=epistemic_status,
        )

        return RAGAnswer(
            question=question,
            answer=answer_text,
            sources=[chunk["source"] for chunk in chunk_dicts],
            epistemic_status=epistemic_status,
            evidence_results=evidence,
            citations=citations,
            confidence=confidence,
            matched_chunks=search_results,
            evidence=evidence,
        )

    def _synthesize_answer(self, question: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Synthesize answer from relevant chunks.
        """
        # Simple concatenation (can be enhanced with LLM summarization)
        answer_parts = []
        for chunk in chunks:
            answer_parts.append(f"From {chunk['source']}:\n{chunk['content'][:500]}...")
        return "\n\n".join(answer_parts)

    def generate_evidence(
        self,
        question: str,
        answer: str,
        citations: List[str],
        confidence: float,
        epistemic_status: str,
    ) -> Dict[str, Any]:
        """
        Creates an audit-ready evidence dictionary compliant with the Evidence Schema.
        """
        return {
            "query": question,
            "epistemic_status": epistemic_status,
            "confidence": confidence,
            "citations": citations,
            "findings": [
                {
                    "statement": answer.splitlines()[0] if answer else "",
                    "grounded_sources": citations,
                    "confidence_score": confidence,
                }
            ],
            "verification_status": "VERIFIED" if confidence >= 0.7 else "UNCONFIRMED",
        }

---
name: patent-analysis-and-ip-guard
description: "Use when parsing patents or evaluating clean-room IP risks."
version: 1.0.0
author: Gerych Core + Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [patents, ip-guard, clean-room, google-patents, uspto, claims-extraction, hybrid-search]
    category: research
    requires_toolsets: [terminal]
---

# Patent Analysis, Claims Extraction & Clean-Room IP Guard

A class-level architectural guide and pipeline for ingesting patent corpus data (Google Patents, USPTO), extracting structured claims and classifications, indexing via PostgreSQL Hybrid Search (tsvector + pgvector), and conducting clean-room IP infringement risk assessments.

## When to Use

Use this skill when:
- Parsing and structuring patent specifications, abstracts, claims trees, and prior art citations.
- Ingesting patent data from Google Patents API, USPTO Open Data, or EPO bulk sources.
- Designing high-dimensional vector embeddings and weighted full-text indexes for patent similarity search.
- Implementing automated Clean-Room IP Guard pipelines to evaluate infringement risk during architectural design.
- Setting up semantic threshold boundaries ($0.85$ cosine similarity) and claim-level overlap audits.

## 1. Patent Ingestion & Resilient Client Architecture

When querying external patent APIs (Google Patents, USPTO Bulk API), employ an asynchronous, non-blocking client with automatic mock fallbacks for isolated testing and CI/CD pipelines:

```python
import logging
from typing import Optional, List, Dict, Any

try:
    import aiohttp
except ImportError:
    aiohttp = None  # type: ignore

logger = logging.getLogger("dnk.patent_shield.client")

class PatentClient:
    def __init__(self, api_key: Optional[str] = None, use_mock_fallback: bool = True):
        self.api_key = api_key
        self.use_mock_fallback = use_mock_fallback
        self.base_url = "https://patents.google.com/api/v1"

    async def search_patents(self, query: str, jurisdiction: str = "US", limit: int = 50) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []
        if aiohttp is None or not self.api_key:
            if self.use_mock_fallback:
                return self._generate_mock_patents(query, jurisdiction, limit)
            return []
        # Query external API securely with redacted credentials
        ...
```

## 2. Patent Specification & Claims Parser

Patent documents contain nested independent and dependent claims, CPC/IPC classification codes, and citation graphs. Normalize them into structured dictionaries:

```python
import re
from typing import List, Dict, Any

class PatentParser:
    @staticmethod
    def extract_claims(patent_data: Dict[str, Any]) -> List[str]:
        raw_claims = patent_data.get("claims", [])
        if isinstance(raw_claims, list):
            return [
                c.get("text", "").strip() if isinstance(c, dict) else str(c).strip()
                for c in raw_claims
                if c
            ]
        elif isinstance(raw_claims, str):
            # Split claims by ordinal markers (e.g., '1. ', '2. ')
            claims = re.split(r'(?=\b\d+\.\s+)', raw_claims.strip())
            return [c.strip() for c in claims if c.strip()]
        return []

    @staticmethod
    def extract_classifications(patent_data: Dict[str, Any]) -> List[str]:
        classifications = patent_data.get("classifications", [])
        extracted = []
        for item in classifications:
            code = item.get("code") if isinstance(item, dict) else str(item)
            if code and code not in extracted:
                extracted.append(code)
        return extracted
```

## 3. PostgreSQL Hybrid Patent Schema (tsvector + pgvector)

Index patent title, abstract, and claims using weighted `tsvector` alongside `pgvector` HNSW cosine distance:

```sql
CREATE TABLE IF NOT EXISTS patent_corpus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patent_id VARCHAR(64) UNIQUE NOT NULL,
    jurisdiction VARCHAR(8) NOT NULL DEFAULT 'US',
    title TEXT NOT NULL,
    abstract TEXT,
    claims JSONB NOT NULL DEFAULT '[]'::jsonb,
    classifications TEXT[] DEFAULT '{}',
    prior_art TEXT[] DEFAULT '{}',
    embedding vector(768),
    search_vector tsvector,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Weighted GIN index: A (title), B (abstract), C (claims)
CREATE OR REPLACE FUNCTION update_patent_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.abstract, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.claims::text, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## 4. Hybrid Similarity Engine & Multi-Factor IP Risk Evaluator

To minimize false positives/negatives, combine dense/full-text RRF scores with explicit lexical claims Jaccard overlap:

$$\text{Similarity Score} = 0.6 \times \text{RRF Score} + 0.4 \times \text{Claims Jaccard Overlap}$$

### Similarity Engine

```python
class PatentSimilarityEngine:
    def __init__(self, pgvector_store=None, use_mock_fallback: bool = True):
        self.pgvector = pgvector_store
        self.use_mock_fallback = use_mock_fallback

    def _calculate_similarity(self, clean_room_spec: str, patent: dict) -> float:
        spec_words = set(clean_room_spec.lower().split())
        claims_text = " ".join(patent.get("claims", [])).lower()
        patent_words = set(claims_text.split())
        
        jaccard = len(spec_words & patent_words) / len(spec_words | patent_words) if spec_words | patent_words else 0.0
        rrf_score = patent.get("rrf_score", 0.5)
        return round(0.6 * rrf_score + 0.4 * jaccard, 4)
```

### Risk Evaluator (Multi-Factor Infringement Scoring)

Evaluate infringement risks across 4 distinct severity tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`):

```python
from enum import Enum
from typing import Dict, List, Any

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PatentRiskEvaluator:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def assess_risk(self, clean_room_spec: str, similar_patents: List[Dict[str, Any]]) -> Dict[str, Any]:
        risk_factors = []
        max_similarity = 0.0

        for patent in similar_patents:
            similarity = float(patent.get("similarity_score", 0.0))
            max_similarity = max(max_similarity, similarity)
            patent_id = patent.get("patent_id", "UNKNOWN")

            if similarity >= self.similarity_threshold:
                risk_factors.append({
                    "factor": "high_similarity",
                    "patent_id": patent_id,
                    "severity": "high" if similarity < 0.95 else "critical",
                })

            claims_overlap = self._analyze_claims_overlap(clean_room_spec, patent.get("claims", []))
            if claims_overlap["overlap_ratio"] > 0.4:
                risk_factors.append({
                    "factor": "claims_overlap",
                    "patent_id": patent_id,
                    "severity": "medium" if claims_overlap["overlap_ratio"] < 0.7 else "high",
                })

            if self._check_classification_match(clean_room_spec, patent):
                risk_factors.append({
                    "factor": "classification_match",
                    "patent_id": patent_id,
                    "severity": "low",
                })

        overall_risk = self._calculate_overall_risk(max_similarity, risk_factors)
        return {
            "overall_risk": overall_risk.value,
            "max_similarity": round(max_similarity, 4),
            "risk_factors": risk_factors,
            "recommendations": self._generate_recommendations(overall_risk, risk_factors),
        }
```

## 5. FastAPI Router & Generative UI Dashboard Integration

Expose patent search, risk assessment, and corpus batch-ingestion via FastAPI routers and connect to React/Next.js Generative UI dashboards:

### FastAPI Router Endpoints (`apps/api/routers/patent_shield.py`)

- `POST /api/v1/patent-shield/search`: Search patents via Google Patents / USPTO with mock fallback.
- `POST /api/v1/patent-shield/risk-assessment`: Perform multi-factor clean-room risk analysis ($0.6 \times \text{RRF} + 0.4 \times \text{Jaccard}$).
- `POST /api/v1/patent-shield/corpus/ingest`: Batch ingest patent details into `patent_corpus` (tsvector + pgvector).
- `GET /api/v1/patent-shield/corpus/stats`: Query database corpus statistics.

### Generative UI Dashboard Hook (`usePatentShield.ts`)

```typescript
export function usePatentShield() {
  const [assessment, setAssessment] = useState<RiskAssessmentResponse | null>(null);
  
  const assessRisk = useCallback(async (cleanRoomSpec: string, queryText: string) => {
    const res = await fetch('/api/v1/patent-shield/risk-assessment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clean_room_spec: cleanRoomSpec, query_text: queryText }),
    });
    const data = await res.json();
    setAssessment(data);
    return data;
  }, []);

  return { assessment, assessRisk };
}
```

## Pitfalls & Anti-Patterns

1. **Ignoring Claim Hierarchy**: Never treat dependent claims as separate standalone restrictions without evaluating their parent independent claim.
2. **Hardcoded API Credentials**: Always inject API keys via secure environment variables and sanitize logs with `[REDACTED]`.
3. **Single-Retriever Blindness**: Keyword matching alone misses synonymous algorithmic descriptions; dense embeddings alone miss exact technical terminology. Always use **Hybrid Search + RRF** for IP risk screening.

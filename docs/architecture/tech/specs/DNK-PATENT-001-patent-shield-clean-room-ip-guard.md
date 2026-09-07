# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-PATENT-001-patent-shield-clean-room-ip-guard.md"
# purpose: "System specification and architectural design for Patent Shield & Clean-Room IP Guard Engine"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-PATENT-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---

# 🛡️ DNK-PATENT-001: Patent Shield & Clean-Room IP Guard Architecture

## 1. Executive Summary
DNK Patent Shield provides automated intellectual property (IP) risk assessment, prior-art scanning, and patent infringement verification for clean-room reverse engineered software components. Integrated directly into the DNK OS continuous development lifecycle, it ensures that generated code and architecture designs do not violate registered patent claims.

## 2. Architectural Components

### 2.1 Patent Client (`core/patent_shield/patent_client.py`)
- Interfaces with Google Patents API, USPTO Open Data APIs, and local patent corpus fallback.
- Provides asynchronous patent retrieval, batch querying by keywords/jurisdictions, and robust offline mock generation for resilient CI/CD execution.

### 2.2 Patent Parser (`core/patent_shield/patent_parser.py`)
- Extracts independent and dependent claims, abstracts, classification codes (CPC/IPC), prior-art citations, assignees, and filing dates.
- Normalizes raw patent JSON/XML representations into structured `PatentData` schemas.

### 2.3 Storage & Retrieval (`apps/api/sql/002_patent_shield_schema.sql`)
- PostgreSQL `patent_corpus` table backing both sparse lexical search (`tsvector` with weighted title/abstract/claims) and dense semantic vector search (`pgvector` with cosine HNSW index).
- Full SQL Reciprocal Rank Fusion (RRF) compatibility.

## 3. Data Flow
1. **Clean-Room Specification** $\rightarrow$ AST & Functional feature extraction.
2. **Hybrid Patent Search** $\rightarrow$ Querying `patent_corpus` via tsvector + pgvector + RRF.
3. **Claim Matcher & Risk Scoring** $\rightarrow$ Comparing independent claims with specification AST nodes.
4. **Audit Report Generation** $\rightarrow$ Emitting automated IP compliance evidence and mitigation plans.

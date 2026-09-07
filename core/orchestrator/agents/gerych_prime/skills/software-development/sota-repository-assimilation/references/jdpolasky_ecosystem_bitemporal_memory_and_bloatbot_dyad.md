# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/sota-repository-assimilation/references/jdpolasky_ecosystem_bitemporal_memory_and_bloatbot_dyad.md"
# purpose: "SOTA Reference: jdpolasky Portfolio - Bitemporal Memory Architecture, BloatBot & BuildBot Dyad, and Anti-Bloat Governance"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "Gerych Prime & Maxim"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Reference: jdpolasky Ecosystem (Bitemporal Memory, BloatBot & BuildBot Dyad)

Assimilated from the complete open-source suite of **[jdpolasky](https://github.com/jdpolasky)** (`ai-chief-of-staff-engine`, `bloatbot`, `buildbot`, `ai-chief-of-staff`, `chief-of-staff-2`).

---

## 🏛️ 1. Bitemporal Memory Architecture (`ai-chief-of-staff-engine`)

### Why Bitemporal?
Standard LLM memory systems store single-timestamp facts or append unstructured text. When reality changes or when the system discovers a prior belief was mistaken, mutable updates destroy historical lineage.
Bitemporal storage separates:
- **Valid Time** (`valid_from` to `valid_to`): The interval during which the state or fact was true in the real world.
- **Transaction Time** (`tx_from` to `tx_to`): The interval during which the agent/system believed and recorded this fact.

### Canonical SQLite Schema
```sql
CREATE TABLE facts (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  content         TEXT    NOT NULL,
  category        TEXT    NOT NULL,
  valid_from      TEXT    NOT NULL,
  valid_to        TEXT,
  tx_from         TEXT    NOT NULL,
  tx_to           TEXT,
  supersedes_id   INTEGER REFERENCES facts(id),
  retracted       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_facts_active ON facts (valid_to, retracted);
CREATE VIRTUAL TABLE facts_fts USING fts5(content, tokenize='porter');
```

### Invariants:
1. **Never update or delete rows in place**.
2. **Supersession**: When a fact changes, close `tx_to = datetime('now')` on the previous record and insert a replacement record with `supersedes_id = old.id`.
3. **Retraction**: When a fact is refuted without replacement, set `retracted = 1` and close `tx_to`.

---

## 🛡️ 2. Write Contracts (JSON Schema Gate)

Every mutation to memory or session logs must validate against strict JSON Schemas before touching persistence:
- `fact_write.json`: enforces category, non-empty content, ISO-8601 timestamps, and retraction flags.
- `episode_write.json`: enforces task provenance, tool outcomes, and structured reflection.
- **Fail-Closed**: Any unvalidated or malformed write is rejected before executing SQL.

---

## ⚖️ 3. The BloatBot & BuildBot Equilibrium Dyad

System health degrades when the same agent that writes code also decides whether that code is necessary or clean.
The `jdpolasky` architecture splits construction and sanitation into two complementary personas:

| Attribute | `buildbot` (The Builder) | `bloatbot` (The Auditor) |
|---|---|---|
| **Mission** | Growth, synthesis, minimal working implementations | Pruning, token minimization, dead link elimination |
| **Prerequisite** | 1-page ratified blueprint before creating any file | Periodic passive scan across all system files |
| **Execution** | Builds smallest possible artifact; proves it live | Identifies top 5 cuts ranked by token payoff |
| **Boundary** | **Never certifies its own work** (submits to auditor) | **Touches zero files** without explicit, itemized confirmation |
| **Output** | Working tested artifact | Itemized diff proposals with exact token savings |

---

## 🔄 4. Three-Tier Context Retrieval

To avoid blowing context windows while keeping high recall:
1. **Tier 1 (Pinned Foundation)**: 5–10 critical invariants and active chair profiles (always injected, <500 tokens).
2. **Tier 2 (FTS5 / BM25 Search)**: Targeted lexical matching across active facts (`valid_to IS NULL AND retracted = 0`).
3. **Tier 3 (Deep Domain Archives)**: Dated transcripts in `Archive/` and specs in `Parts/` loaded strictly on demand (LOD).

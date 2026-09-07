<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "packages/video-audit-core/README.md"
# purpose: "Documentation & Architecture Overview for @dnk/video-audit-core Package."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---
-->

# @dnk/video-audit-core

Canonical Contract-First Video Intelligence & Niche Adaptation Engine for DNK OS.

## 🎯 Purpose

`packages/video-audit-core` is a **framework-agnostic TypeScript domain library** that defines the contracts, schemas, validators, evidence classification rules, and similarity risk governance for upstream reference video audits and niche script adaptations.

It produces standardized, versioned outputs (`ScriptDocument`, `ProsodyDocument`, `ShotList`) consumed downstream by `@dnk/teleprompter-core` and video rendering engines.

## 📦 Domain Contracts

- **`VideoAuditReport`** (`video-audit.v1`): Multimodal audit report (transcript, scenes, shots, audio features, narrative structure, visual analysis, retention risks, evidence items).
- **`AdaptationResult`** (`adaptation.v1`): Niche adaptation containing script, prosody, shot list, preserved mechanisms, changed elements, evidence, and similarity report.
- **`ScriptDocument`** (`script.v1`): Versioned script document with scenes, paragraphs, and timing boundaries.
- **`ProsodyDocument`** (`prosody.v1`): Vocal delivery cues (punches, holds, pauses, pitch shifts, gestures).
- **`ShotList`** (`shot-list.v1`): Recording and B-roll shot instructions.

## 🛡️ Governance & Safety Rules

1. **Evidence Classification**: Every claim is labeled as `observed` (measured), `inferred` (high-confidence AI deduction), or `hypothesized` (unverified engagement theory).
2. **Similarity Risk Policy**:
   - High **structural similarity** is allowed (format storytelling transfer).
   - High **lexical**, **visual**, **audio**, or **brand** similarity escalates risk to `high` or `critical_plagiarism`.

## 🚀 Running Tests

```bash
cd packages/video-audit-core
pnpm test
# or
npx vitest run
```

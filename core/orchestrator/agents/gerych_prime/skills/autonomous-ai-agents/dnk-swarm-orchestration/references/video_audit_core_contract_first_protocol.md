# Contract-First Video Intelligence & Adaptation Domain Protocol (@dnk/video-audit-core)

## Overview
This reference specifies the contract-first video intelligence domain architecture implemented in `@dnk/video-audit-core` (`packages/video-audit-core`).

## Upstream vs Downstream Domain Boundaries
```text
ReferenceAsset (URL / File)
   ↓
VideoAuditReport (Multimodal 6-Layer Analysis)
   ↓
AdaptationResult (Niche Adaptation & Similarity Guard)
   ↓
ScriptDocument (script.v1) + ProsodyDocument (prosody.v1) + ShotList (shot-list.v1)
   ↓
teleprompter-core (Execution Runtime Engine)
```

## Mandatory Contract Standards
1. **Schema Versioning**: Every contract payload MUST carry an explicit `schemaVersion` string (`script.v1`, `prosody.v1`, `shot-list.v1`, `video-audit.v1`, `adaptation.v1`).
2. **Zero Outer Dependencies**: `@dnk/video-audit-core` is a pure TypeScript contract package with Zod validation,Vitest test coverage, and zero DOM/React/FastAPI/Telegram dependencies.
3. **Evidence Governance**: Every audit insight must be classified as:
   - `observed` (deterministic measurement via WhisperX / FFmpeg / rule engines with $confidence \ge 0.7$);
   - `inferred` (multimodal AI model deduction via Gemini / Claude with $confidence \ge 0.4$);
   - `hypothesized` (unverified engagement or retention theories).
4. **Similarity & Plagiarism Risk Policy**:
   - `structural` similarity up to 1.0 is expected and allowed (format mechanism transfer);
   - `lexical` similarity > 30%, or high `visual`/`audio`/`brand` similarity raises risk level to `high` or `critical_plagiarism`.
5. **Fixtures as Validation Benchmarks**:
   - `talking-head`
   - `product-demo`
   - `educational-short`
   - `reburn-reference` (Full End-to-End fixture from ReferenceAsset → VideoAuditReport → AdaptationResult → ScriptDocument & ProsodyDocument).

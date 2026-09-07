# Multimodal Audit & Claim Validation Protocol (VIDEO-AUDIT-PIPELINE-001E)

## Overview
`VIDEO-AUDIT-PIPELINE-001E` introduces the evidence-backed multimodal audit, which converts normalized pipeline artifacts (`transcript.v1`, `scenes.v1`, `ocr.v1`, `audio-features.v1`, `multimodal-evidence.v1`, reference metadata) into a structured `VideoAuditReport` (`multimodal-audit.v1`).

---

## 🎯 1. Key Invariants & Architectural Rules

### A. Strict Claim Classification (Observed vs Inferred vs Hypothesized)
To maintain 100% traceability and prevent AI hallucination, all audit claims are classified into exactly three classes:
1. **`observed`**: Direct facts extracted from the media stream (e.g., spoken words, visible text, detected cut timestamps).
2. **`inferred`**: Deductions based on combining multiple observed facts (e.g., "The pace is slow because scenes average 15 seconds").
3. **`hypothesized`**: Speculative, high-level marketing or retention conclusions (e.g., "Retention drops here because the hook lacks a strong visual CTA").

**The Invariant:**
- **Observed claims MUST carry evidence links**: Any claim with `classification === 'observed'` must have at least one non-empty reference array inside `evidenceRefs` (`transcriptWordIndexes`, `sceneIndexes`, `ocrFrameIds`, `audioSegmentIndexes`, or `evidenceItemIds`).
- **Separated UI/Data treatment**: `hypothesized` claims must never be presented or styled as observed facts, and must not have a confidence score of `1.0`.

### B. Two-Pass Reasoning Engine (Strategic Decoupling)
- **Pass 1 — Evidence Synthesis**:
  - Consumes available source documents (`transcript`, `scenes`, `ocr`, `audioFeatures`).
  - Resolves temporal overlaps, maps text regions, and compiles the verified fact base.
  - Does NOT make speculative suggestions or write marketing copy.
- **Pass 2 — Strategic Interpretation**:
  - Consumes the synthesized facts.
  - Evaluates script narrative pacing, checks logo/text visibility, calculates cut frequency, and generates retention hypotheses and adaptation recommendations.

---

## ⚡ 2. Portability & Provider Port Adapter Pattern

Core domain logic must remain completely decoupled from external LLM providers (Vertex AI/Gemini, Anthropic/Claude).

### A. The Port Contract (`MultimodalAuditProviderPort`)
All analytics engines must implement the canonical port:
```typescript
export interface MultimodalAuditProviderPort {
  readonly providerId: string;
  readonly modelSetVersion: string;
  analyze(
    input: MultimodalAuditInput,
    context: MultimodalAuditContext
  ): Promise<MultimodalAuditProviderResult>;
}
```

### B. Generation Metadata Invariant
Every generated zurt-validated audit artifact MUST store detailed execution metadata:
*   `provider`: the AI adapter utilized (e.g., `'gemini'`, `'claude'`, `'deterministic-fake'`).
*   `model`: the specific model ID and version (e.g., `'gemini-2.5-pro'`).
*   `modelSetVersion`: version tag representing the prompt configuration.
*   `promptTemplateVersion`: the version of prompt templates fed to the LLM.
*   `tokenUsage`: input/output tokens consumed.
*   `durationMs`: execution processing duration.
*   `inputArtifacts`: map of the input artifact keys and their SHA-256 hashes to guarantee evidence integrity.

---

## 🧪 3. Partial-Input & Degraded Execution Policy

The pipeline must handle partial success gracefully (e.g., if OCR or audio analysis failed but transcription succeeded).

### A. Required vs. Optional Analysis Mapping
Standardize on the `AnalysisRequirements` configuration to map required and optional inputs.

### B. Graceful Warnings Compilation
If optional inputs are missing, the worker or provider must:
1. Inject specific, machine-readable codes in the `warnings` array:
   - `PARTIAL_INPUT_MISSING_OCR`: when OCR document is omitted.
   - `PARTIAL_INPUT_MISSING_AUDIO_FEATURES`: when audio features are omitted.
2. Compile as much of the report as possible using remaining inputs (e.g., run visual analysis using scenes even without OCR).

### C. Missing Required Inputs
If a required component (e.g., `transcript` when `transcript: 'required'`) is missing, the worker MUST throw a `MISSING_REQUIRED_EVIDENCE` error, shifting the job into `failed` or `manual_review` states rather than writing incomplete documents.

---

## 🛠️ 4. Test Verification Template
Always verify schema compliance and hash validation in unit/integration tests using the native Node test runner:
```typescript
import { test, describe } from 'node:test';
import assert from 'node:assert';
import { MultimodalAuditResultSchema } from '../schemas/multimodal-audit.js';

describe('Multimodal Audit Schema Validation', () => {
  test('should fail if observed claim lacks evidence references', () => {
    const invalidResult = {
      schemaVersion: 'multimodal-audit.v1',
      referenceAssetId: 'asset-1',
      observedFacts: [{
        id: 'claim-1',
        classification: 'observed', // Invalid: observed claim with empty refs
        text: 'Logo displayed on screen',
        timeRange: { startMs: 0, endMs: 2000 },
        evidenceRefs: {
          transcriptWordIndexes: [],
          sceneIndexes: [],
          ocrFrameIds: [],
          audioSegmentIndexes: [],
          evidenceItemIds: []
        },
        confidence: 0.95
      }],
      // ... structural and other fields omitted for brevity
    };

    const parsed = MultimodalAuditResultSchema.safeParse(invalidResult);
    assert.strictEqual(parsed.success, false);
  });
});
```

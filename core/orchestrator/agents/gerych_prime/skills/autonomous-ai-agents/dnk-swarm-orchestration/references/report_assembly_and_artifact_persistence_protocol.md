# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/report_assembly_and_artifact_persistence_protocol.md"
# purpose: "Canonical Reference for Deterministic VideoAuditReport Assembly, Integrity Verification & Persistence v1.0.0."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 📊 Report Assembly & Artifact Persistence Protocol (001E-D)

This document establishes the canonical protocol for deterministic aggregation of multimodal pipeline results, cryptographic validation of input manifests, evidence referential integrity checks, immutable storage persistence, and post-persistence transactional event emission.

## 🎯 1. Architectural Role & Flow
The `VideoAuditReportAssembler` lies at the application-orchestration layer, acting as a synchronisation gateway that transforms multi-worker outputs into a unified, compliant, and validated `VideoAuditReport`.

```text
+-----------------------+   +-----------------------+   +-----------------------+
|     transcript.v1     |   |       scenes.v1       |   |         ocr.v1        |
+-----------+-----------+   +-----------+-----------+   +-----------+-----------+
            |                           |                           |
            +---------------------------+---------------------------+
                                        |
                                        v
                    +-------------------+-------------------+
                    |      VideoAuditReportAssembler        |
                    |  - SHA-256 Integrity Verification     |
                    |  - referenceAssetId Alignment Check   |
                    |  - Evidence Link Citation Validation  |
                    |  - Degraded State Compiler            |
                    +-------------------+-------------------+
                                        |
                                        v
                            +-----------+-----------+
                            |     ArtifactStore     | (Immutable Persistence)
                            +-----------+-----------+
                                        |
                                        v
                            +-----------+-----------+
                            |     AuditEventBus     | (AuditReportCreated.v1)
                            +-----------------------+
```

---

## ⚡ 2. Core Protocol Invariants

### 2.1 Cryptographic Integrity Verification (SHA-256 Validation)
To prevent man-in-the-middle tampering and local file corruption, the assembler MUST compare the actual content hashes of all incoming documents against expected signatures listed in the ingestion manifest:
- For each artifact $A_i$ with content string $C_i$, verify:
  $$\text{SHA256}(C_i) == \text{Manifest.ExpectedHash}(A_i)$$
- Reject immediately if a hash mismatch is detected.

### 2.2 Entity Identity & Referential Alignment
- **Asset Scope Isolation**: All constituent documents MUST share the identical `referenceAssetId`. The assembler must throw a validation error if any artifact targets a different video or asset.
- **Schema Conformity**: Verify that all document `schemaVersion` strings match the expected versions (e.g. `transcript.v1`, `multimodal-audit.v1`).

### 2.3 Evidence Referential Integrity (Citations Verification)
Every evidence block inside `multimodal-audit.v1` (which backs up observations and hooks) must be validated against physical references:
- **Transcript Word Indices**: Verify `transcriptWordIndexes` lie within the actual boundaries of the `transcript.v1` words array.
- **Scenes & Cuts**: Verify `sceneIds` referenced exist in the `scenes.v1` collection.
- **OCR Frames**: Verify `ocrFrameIds` referenced exist in the `ocr.v1` collection.
If an evidence reference points to a non-existent index or ID, the assembler must treat this as an invalid/corrupt document state and halt assembly.

### 2.4 Degraded Mode Compilation & Partial-Input Resilience
If optional analytical outputs (such as `ocr.v1` or `audio-features.v1`) failed during upstream execution, the assembler must not crash. Instead:
- Substitute a safe default structure (e.g. empty array/object).
- Add a structured warning object to the report's `warnings` array:
  ```json
  {
    "code": "DEGRADED_PARTIAL_INPUT",
    "message": "OCR document (ocr.v1) was missing or corrupted. Assembled with empty OCR frames.",
    "severity": "warning"
  }
  ```
- Re-calculate overall status as `partially_successful` or `degraded` if mandatory thresholds are not met.

### 2.5 Idempotency & Immutable Persistence
- **Deterministic ID Generation**: The `reportId` must be derived deterministically from the SHA-256 hashes of all constituent input artifacts.
- **Write-Once policy**: Query the `ArtifactStore` with the computed `reportKey`. If the report already exists, return it immediately without initiating an overwrite.

### 2.6 Post-Persistence Event Emission Invariant
- The event `AuditReportCreated.v1` must **only** be dispatched after successful write-confirmation from the `ArtifactStore`.
- If the database or object-store write fails, the pipeline must fail-closed and withhold event publication to prevent downstream message consumers from operating on non-existent records.

---

## 📋 3. Canonical schemas

### 3.1 AuditReportCreated.v1 Payload Schema (JSON-Schema equivalent)
```typescript
export const AuditReportCreatedEventSchema = z.object({
  id: z.string().uuid(),
  type: z.literal('AuditReportCreated.v1'),
  timestamp: z.string().datetime(),
  payload: z.object({
    referenceAssetId: z.string(),
    reportId: z.string(),
    reportKey: z.string(),
    aggregateStatus: z.enum(['success', 'partially_successful', 'failed', 'degraded']),
    sha256: z.string(),
    createdAt: z.string().datetime(),
    metadata: z.record(z.any()).optional()
  })
});
```

---

## 🛡️ 4. Standard Assembly Checklist for Implementers

1. **Verify Asset Match**: Ensure `referenceAssetId` matches across all inputs.
2. **Execute Hash Checks**: Re-hash strings and check against the manifest.
3. **Verify Time Segments**: Validate that all scene `timeRange` intervals and evidence citations are temporally bounded by the overall media duration.
4. **Compile Aggregate Metrics**: Map hook types, average WPM, speech-to-music ratio, and visual intensity indicators to canonical output properties.
5. **Persist Immaturely**: Commit the generated report to object storage.
6. **Emit Transaction Event**: Publish `AuditReportCreated.v1` event securely.

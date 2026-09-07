# --- DNK-MRH-HEADER ---
# mrh_id: "references/deterministic_multimedia_pipeline_orchestration.md"
# purpose: "Architecture & Verification Protocol for Deterministic Video Audit Pipeline Orchestration."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎬 Deterministic Video Audit Pipeline Orchestration & Isolation Protocol

## 1. Isolation Principle (Foundation First)
When engineering multimedia pipelines (e.g. video audits, speech transcription, OCR, scene extraction), never couple heavy external engines (WhisperX, FFmpeg, multimodal LLMs) directly into the orchestration loop.
Build the **Orchestration Foundation** first:
1. Pure Domain Entities & Finite State Machine.
2. Canonical Idempotency & Retry Policies.
3. Clean Architecture Ports & Versioned DTOs/Events.
4. In-Memory Mock Implementations & Deterministic Fake Workers.
5. 100% Green Unit & Integration Test Suites before writing production adapters.

```
+-------------------------------------------------------------+
|                     APPLICATION LAYER                       |
|                 VideoAuditOrchestrator                      |
|         (submitJob, pollAndExecuteNext, reclaimLeases)      |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                        PORTS LAYER                          |
|  - AuditJobRepository (Atomic Lease, Idempotency Index)    |
|  - ArtifactStore (Content-Addressed SHA-256 Storage)        |
|  - AuditEventBus (Typed Versioned Event Envelopes)          |
|  - Clock & IdGenerator (Deterministic Time & ID Injection)  |
+-------------------------------------------------------------+
            /                          \
           v                            v
+---------------------------+  +-------------------------------+
|   TEST INFRASTRUCTURE     |  |   PRODUCTION INFRASTRUCTURE   |
| - InMemoryJobRepository   |  | - PostgresJobRepository       |
| - InMemoryArtifactStore   |  | - S3ArtifactStore             |
| - InMemoryAuditEventBus   |  | - RedisEventBus               |
| - DeterministicFakeWorker |  | - Real Multimedia Workers     |
+---------------------------+  +-------------------------------+
```

---

## 2. Finite State Machine (FSM) & Invariants

### State Lifecycle
```
                 +-------------------------------+
                 |                               |
                 v                               |
[queued] ---> [leased] ---> [running] ---> [succeeded]
                 |             |
                 | (timeout)   +---------> [retryable_error] ---> (backoff delay) ---> [queued]
                 v             |
              [queued]         +---------> [permanent_error]
                               |
                               +---------> [cancelled]
```

### Transition Invariants
- **Terminal States**: `succeeded`, `permanent_error`, and `cancelled` cannot transition to any other status.
- **Audit Trail**: Every state mutation records a `JobTransitionRecord`:
  `{ jobId, fromStatus, toStatus, actorId, timestamp, reason, attempt }`.
- **Atomic Leasing**: Workers lease next available job with `WHERE status = 'queued' AND availableAt <= now` and update `status = 'leased'`, `leasedBy = workerId`, `leasedUntil = now + leaseDurationMs`.
- **Lease Recovery**: The orchestrator periodically executes `reclaimExpiredLeases(now)`: jobs in `leased` status where `leasedUntil < now` are automatically rolled back to `queued`.

---

## 3. Idempotency Key Design

Jobs must be uniquely and deterministically identified to avoid duplicate executions:
```typescript
idempotencyKey = `${referenceAssetId}:${jobType}:${inputVersion}:${processorVersion}`
```
- Submitting a job with an existing `idempotencyKey` returns the existing job record without re-enqueuing or generating duplicate events.
- Artifacts use content-addressable and deterministic storage paths:
  `references/${referenceAssetId}/${artifactType}/${versionOrSha256}.${ext}`.

---

## 4. Exponential Backoff & Error Classification

### Error Classes
1. `retryable`: Network glitch, rate limit (HTTP 429), transient downstream timeout.
2. `permanent`: Corrupted input file, invalid container format, malformed schema.
3. `manual_review`: Repeated failures exceeding retry threshold or critical payload anomalies.

### Backoff Schedule (Deterministic Exponential)
```typescript
const BACKOFF_SCHEDULE_MS = [
  5_000,     // Attempt 1: 5s
  30_000,    // Attempt 2: 30s
  120_000,   // Attempt 3: 2m
  600_000,   // Attempt 4: 10m
];
// Attempt 5+ -> Permanent Error
```
When `attempt < maxAttempts`, status becomes `retryable_error`, `availableAt` is set to `now + delayMs`, and the job is automatically requeued for next polling.

---

## 5. Versioned Event Envelopes

All event contracts must be versioned with explicit schema version tags:
```typescript
interface AuditEventEnvelope<TType extends string, TPayload> {
  eventId: string;
  eventType: TType; // e.g. 'AuditJobCreated.v1'
  timestamp: string;
  correlationId: string;
  actorId: string;
  payload: TPayload;
}
```

---

## 6. Deterministic Test Harness Pattern

In unit/integration test suites:
- Use `DeterministicClock` to step time forwards without `setTimeout` sleeps.
- Use `DeterministicFakeWorker` configured to succeed or throw classified errors (`retryable` vs `permanent`).
- Validate that zero external dependencies (no child processes, no network calls) are required for full orchestration verification.

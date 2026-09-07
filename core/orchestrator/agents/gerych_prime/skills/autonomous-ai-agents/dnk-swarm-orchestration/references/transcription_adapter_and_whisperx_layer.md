# 🎙️ Transcription Adapter, WhisperX Layer & Ukrainian Speech Benchmark Protocol (VIDEO-AUDIT-PIPELINE-001C)

## Overview
This reference documents the canonical architecture, domain schemas, error mapping, and Ukrainian speech benchmark protocol for `VIDEO-AUDIT-PIPELINE-001C` inside `packages/video-audit-core`.

---

## 1. Canonical `transcript.v1` Schema & Invariants

All ASR engines must produce or be adapted into the canonical `TranscriptDocument` schema (`schemaVersion: "transcript.v1"`).

```typescript
// Key Invariants Enforced by Zod
1. startMs >= 0 && endMs > startMs for all segments and words.
2. Word time ranges must be strictly bounded by their enclosing segment:
   segment.startMs <= word.startMs && word.endMs <= segment.endMs
3. Segments and words must be strictly sorted by ascending timestamps.
4. durationMs must be >= max timestamp across all segments/words.
5. Empty transcript text is prohibited for status === "completed" 
   (must be degraded or partial with warnings).
6. Language must be BCP-47 normalized (e.g. "uk-UA", "en-US").
```

---

## 2. Domain Isolation & Provider Port

To prevent domain coupling to specific ASR frameworks (WhisperX, Faster-Whisper, AssemblyAI):

- `TranscriptionProviderPort` defines the contract (`transcribe(input, options)`).
- Specific ASR drivers (e.g., `WhisperXTranscriptionAdapter`) live in `infrastructure/transcription/`.
- Capabilities contract (`TranscriptionCapabilities`):
  - `supportsWordTimestamps`: boolean
  - `supportsDiarization`: boolean
  - `supportsLocalExecution`: boolean
  - `supportedLanguages`: BCP-47 tags array

---

## 3. Subprocess Execution & Error Mapping

When driving WhisperX or similar CLI engines:
1. **Subprocess Boundary**: Isolate process execution with configurable timeout, CUDA device selection (`computeType`, `device`), and VAD parameters.
2. **Error Classification**:
   - **CUDA OOM / Process Crash / Timeout** ➔ `retryable_error` (with exponential backoff attempt increment).
   - **Corrupt Audio / Missing Stream / Unsupported Format** ➔ `permanent_error` (fail-fast, no retry).
3. **Timestamp Alignment**: Convert floating-point seconds (e.g., `12.345s`) to integer milliseconds (`12345ms`) with strict round/floor bounds.

---

## 4. Deterministic Fake & Ukrainian Speech Benchmarks

For unit tests and CI offline verification:
- `DeterministicTranscriptionProvider` provides predictable synthesis of Ukrainian domain terms (ReBurn, Shopify, Teleprompter, ASR, OCR, "дофаміновий детокс").
- **Benchmark Metrics**:
  - `technicalTermRecall` >= 90%
  - `wordTimestampCoverage` >= 95%
  - Real-Time Factor (RTF) tracking.
  - Degraded audio simulation (background noise, missing tracks).

---

## 5. Artifact Persistence & Legacy Compatibility

1. **ArtifactStore Persistence**:
   - Store canonical `TranscriptDocument` JSON with SHA-256 digest and MIME `application/json`.
   - Publish `ArtifactCreated.v1` event downstream.
2. **Legacy Report Adapter**:
   - Use `toLegacyTranscriptDocument` to map `transcript.v1` into `VideoAuditReport` legacy structures without duplicating domain logic.

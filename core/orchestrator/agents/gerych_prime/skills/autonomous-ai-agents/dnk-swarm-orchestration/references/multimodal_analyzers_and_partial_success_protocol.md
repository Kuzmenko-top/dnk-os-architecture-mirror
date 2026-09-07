# Multimodal Analyzers, Scene/OCR/Audio Features & Partial Success Protocol (VIDEO-AUDIT-PIPELINE-001D)

## Overview
`VIDEO-AUDIT-PIPELINE-001D` introduces multi-analyzer parallel processing for video media assets in `@dnk/video-audit-core`. Instead of a single heavy pipeline step, three distinct analyzers execute in parallel:
1. **Scene Extraction** (`scenes.v1`): Detects scene cuts, keyframes, shot types (`talking_head`, `close_up`, `product`, `b_roll`), and boundary confidence.
2. **Keyframe OCR** (`ocr.v1`): Extracts text regions with normalized `[0..1]` bounding boxes, language hints, and confidence scores.
3. **Audio Features** (`audio-features.v1`): Calculates RMS levels, silence intervals, speech/music probabilities, clipping, and audio presence.

---

## Key Invariants & Architectural Rules

### 1. Independent Analyzer Architecture
- **Why Separate Workers?**: Scene detection, OCR, and audio analysis have different computational complexities, dependencies (FFmpeg vs CLI OCR vs Whisper/audio DSP), latencies, and failure modes.
- **Worker Contracts**:
  - `SceneExtractionWorker` ➔ Produces `scenes.v1.json`
  - `OCRWorker` ➔ Produces `ocr.v1.json`
  - `AudioFeatureWorker` ➔ Produces `audio-features.v1.json`

### 2. Time & Coordinate Invariants
- **Scenes**:
  - `startMs >= 0`, `endMs > startMs`.
  - Non-overlapping, sorted monotonically by `startMs`.
  - `durationMs = endMs - startMs`.
- **OCR Bounding Boxes**:
  - Normalized coordinates `x`, `y`, `width`, `height` MUST be within `[0.0, 1.0]`.
- **Audio Segments**:
  - `startMs >= 0`, `endMs > startMs`.
  - Continuous coverage across audio duration.

### 3. OCR vs. Speech Transcript Separation
- **`ocr.v1`**: Represents "what is visible on screen" (banners, titles, product labels).
- **`transcript.v1`**: Represents "what is spoken" (ASR audio stream).
- **Rule**: Never merge or conflate OCR text into `transcript.v1`. Keep them as distinct evidentiary layers.

### 4. Degraded Capabilities & Partial Success
- **Missing Audio**: Videos without audio streams (`hasAudioTrack: false`) return a degraded `AudioFeaturesDocument` with `silenceRatio: 1.0` and `degradationWarnings: ["NO_AUDIO_STREAM_FOUND"]`.
- **Partial Failure Handling**:
  - If OCR fails due to corrupt keyframes, `OCRWorker` transitions its job to `permanent_error`.
  - The aggregate job status (`computeAggregateStatus`) resolves to `partial_success` if at least one core analyzer (`scenes.v1` or `transcript.v1`) succeeded.

### 5. Multimodal Evidence Aggregation & Evidence References
- `buildMultimodalEvidence({ referenceAssetId, scenes, ocr, audioFeatures, transcript, statuses })`:
  - Correlates all multi-modal documents into time intervals (`EvidenceTimeInterval`) using `EvidenceReference` (`transcriptSegmentIds`, `transcriptWordIndexes`, `sceneIds`, `ocrFrameIds`, `audioSegmentIndexes`) for 100% deterministic traceability.
  - Merges spoken words, visual text, and acoustic metrics for each interval to supply complete context for downstream LLM reasoning (`VIDEO-AUDIT-PIPELINE-001E`).
  - Guarantees complete immutability of input documents.

### 6. Worker FSM Lifecycle & Storage Protocols
- **FSM Step-Sequence Invariant**: When workers lease jobs via `leaseNextJob`, the job state becomes `leased`. The worker MUST explicitly transition the job to `running` before starting analysis. Transitioning directly from `leased` to `succeeded` or `retryable_error` is forbidden.
- **Unified FSM Lifecycle Helper (`runLeasedAnalyzerJob`)**: To eliminate boilerplate duplication and guarantee state safety across workers, use the common application helper:
  ```typescript
  export async function runLeasedAnalyzerJob<TInput, TOutput>(params: {
    jobStore: JobRepositoryPort;
    workerId: string;
    leasedJob: Job;
    execute: (input: TInput) => Promise<{ document: TOutput; artifacts?: Record<string, Buffer> }>;
    persistArtifact: (key: string, data: Buffer) => Promise<void>;
    publishEvent?: (event: any) => Promise<void>;
  }): Promise<void>
  ```
  This helper automatically handles:
  1. `leased` ➔ `running` state transition before starting work.
  2. Executing the analyzer payload and writing returned artifact buffers to storage.
  3. Translating success to `succeeded` state and publishing events.
  4. Translating failures to `retryable_error` or `permanent_error` automatically based on the error classification.

- **Canonical Artifact Persistence**: Save serialized artifacts via `await artifactStore.put({ key, referenceAssetId, data: buffer, mimeType: 'application/json' })`.
- **Empty OCR Handling**: A video frame with zero detected text is a valid `completed` result, not a failure. Only engine crashes or unreadable files transition to error states.

### 7. Parameterized Analysis Requirements & Status Policies
To avoid hardcoding optional/required stream policies, standardize on the explicit **`AnalysisRequirements`** interface:
```typescript
export interface AnalysisRequirements {
  transcript: 'required' | 'optional';
  scenes: 'required' | 'optional';
  ocr: 'required' | 'optional';
  audio: 'required' | 'optional';
}
```
Aggregate status computation (`computeAnalysisAggregateStatus`) maps individual document presence and status to the final aggregate status using the following strict truth matrix:

| Component | Condition / Status | Requirement | Resolved Component Status | Final Aggregate Status |
| :--- | :--- | :--- | :--- | :--- |
| **Scenes** | Missing | `required` | `missing` | `failed` / `manual_review` |
| **Transcript** | Missing | `optional` | `missing` | `partial` |
| **Transcript** | Missing | `required` | `missing` | `manual_review` |
| **Audio** | No track (Degraded) | `optional` | `degraded` (with warning) | `partial` |
| **OCR** | Empty (0 text) | `optional` | `completed` | `completed` |
| **Any** | Provider Crash / Failed | `required` | `failed` | `failed` |


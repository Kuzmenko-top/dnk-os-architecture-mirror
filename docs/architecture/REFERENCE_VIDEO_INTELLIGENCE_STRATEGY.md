# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/REFERENCE_VIDEO_INTELLIGENCE_STRATEGY.md"
# purpose: "Canonical Multi-Layer Video Audit, Evidence-Backed Intelligence & Niche Adaptation Pipeline for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["VIDEO-AUDIT-CORE-001", "VIDEO-AUDIT-PIPELINE-001", "VIDEO-AUDIT-TELEGRAM-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧠 DNK Reference Video Intelligence & Audit Specification

## 📌 1. System Vision & Domain Boundaries

The **DNK Reference Video Intelligence** system serves as the **upstream Content Intelligence Engine** for DNK OS. It audits reference videos across speech, structure, visual cues, audio dynamics, and retention mechanics, generating an evidence-backed audit report and synthesizing niche-adapted scripts with prosody markup.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        DNK Content Intelligence Ecosystem                              │
├─────────────────────────────────────────────────┬──────────────────────────────────────┤
│ 1. Upstream: Video Intelligence & Audit         │ 2. Downstream: Execution & Capture   │
│   (packages/video-audit-core)                   │   (packages/teleprompter-core)       │
│                                                 │                                      │
│  Reference Asset Ingestion                      │  ScriptDocument + ProsodyDocument    │
│            ↓                                    │            ↓                         │
│  Multimodal Analysis Pipeline                   │  Word State Machine & Alignment      │
│  (Audio / Visual / Structural / Retention)      │            ↓                         │
│            ↓                                    │  HUD Tracking & Vocal Coaching       │
│  Evidence-Backed VideoAuditReport               │            ↓                         │
│            ↓                                    │  Web / PWA / TMA / Native Recording  │
│  Niche Adaptation & Script Synthesizer          │            ↓                         │
│            └────────────────────────────────────┼───────────► Remotion Video Export    │
└─────────────────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 🔍 2. Analysis Layers & Evidence Classification

### 2.1 Multi-Layer Multimodal Audit Scope

1. **Metadata Audit**: Aspect ratio, duration, resolution, FPS, language, platform source.
2. **Speech Audit**: Word-level timestamped transcript, speaker diarization, WPM pacing, pause duration, filler word density, rhetorical questions, emphasis anchors.
3. **Structure Audit**: Hook mechanism, setup, problem, tension buildup, social proof, reveal, payoff, CTA pattern, open-loop mechanics.
4. **Visual Audit**: Shot boundary detection, shot duration, framing (close-up/medium/wide), camera movement, subject gaze, hand gestures, B-roll timing, text overlays/captions, visual cuts/zooms.
5. **Audio Audit**: Loudness levels (LUFS), silence intervals, speech-to-music ratio, sound effects (SFX), vocal energy peaks, beat-synchronized visual cuts.
6. **Retention Hypotheses**: Time-to-first-context, first visual interrupt, cognitive load distribution, information delivery rhythm, CTA placement timing.

### 2.2 Evidence Classification Standard

To prevent AI hallucination, every analytical claim is strictly categorized:

| Type | Definition | Verification Source |
| :--- | :--- | :--- |
| `observed` | Hard, deterministic measurement extracted directly from media artifacts. | Timestamps from scene detector, audio waveform, exact transcript tokens. |
| `inferred` | High-confidence semantic classification derived from multimodal models. | Identified hook type, rhetorical structure, camera angle classification. |
| `hypothesized` | Plausible viral/retention mechanisms requiring performance validation. | Hypothesized reason for audience retention, pacing effectiveness claims. |

```json
{
  "id": "ev_01j7x8...",
  "type": "observed",
  "claim": "Visual cut to close-up occurs at 1.200s",
  "timeRange": { "startMs": 0, "endMs": 1200 },
  "source": "scene_detector",
  "confidence": 0.98
}
```

---

## 📦 3. Package Layout (`packages/video-audit-core`)

```text
packages/
  video-audit-core/
    package.json
    tsconfig.json
    src/
      domain/
        reference-asset.ts       # Raw reference asset entity & ingest lifecycle
        transcript.ts            # Word-level timestamped transcript models
        scene.ts                 # Shot boundaries, visual framing & gestures
        audit-report.ts          # Consolidated multi-layer audit report
        evidence.ts              # Evidence items (observed/inferred/hypothesized)
        adaptation.ts            # Niche adaptation request & constraints
      contracts/
        audit-schema.ts          # JSON Schema & TypeScript definitions for reports
        adaptation-schema.ts     # Data contract between Audit and Teleprompter Core
      scoring/
        retention-hypothesis.ts  # Heuristic scoring of engagement mechanics
        confidence.ts            # Probabilistic scoring engine
        similarity-guard.ts      # Plagiarism & creative independence gate
      ports/
        transcription.ts         # Timestamped ASR port (Whisper / WhisperX)
        frame-extractor.ts       # Shot detection & keyframe extraction port (FFmpeg)
        multimodal-analyzer.ts   # Vision & LLM structural analysis port
        storage.ts               # Video/artifact object storage port
```

---

## 📜 4. Canonical Domain Contracts

### 4.1 `ReferenceAsset`
```typescript
export interface ReferenceAsset {
  id: string;
  sourceType: 'telegram_file' | 'direct_upload' | 'youtube_url' | 'tiktok_url' | 'instagram_url' | 'screenshot_set';
  sourcePlatform?: 'tiktok' | 'instagram' | 'youtube' | 'telegram' | 'custom';
  sourceUrl?: string;
  storageKey?: string;
  durationMs?: number;
  language?: string;
  rightsStatus: 'user_owned' | 'licensed' | 'user_confirmed_fair_use' | 'unknown';
  ingestionStatus: 'received' | 'validating' | 'ingesting' | 'ready' | 'failed';
  createdAt: string;
}
```

### 4.2 `VideoAuditReport`
```typescript
export interface VideoAuditReport {
  id: string;
  referenceAssetId: string;
  schemaVersion: '1.0.0';
  modelVersions: Record<string, string>;
  metadata: VideoMetadata;
  transcript: TranscriptDocument;
  structure: StructureAnalysis;
  visual: VisualAnalysis;
  audio: AudioAnalysis;
  retentionHypotheses: RetentionHypothesis[];
  evidence: EvidenceItem[];
  adaptationRecommendations: AdaptationRecommendation[];
  similarityFingerprint: string;
  confidence: number;
  createdAt: string;
}
```

### 4.3 `AdaptationRequest` & Governance Guard
```typescript
export interface AdaptationRequest {
  auditId: string;
  brandId?: string;
  targetNiche: string;
  targetAudience?: string;
  targetLanguage: string;
  targetDurationMs?: number;
  tone?: string;
  preserveMechanisms: Array<'hook_mechanism' | 'story_beats' | 'shot_rhythm' | 'cta_pattern'>;
  avoidElements: Array<'original_wording' | 'same_visual_sequence' | 'same_music' | 'brand_trademarks'>;
}
```

---

## ⚙️ 5. Analysis Job State Machine

```
               ┌───────────────┐
               │   RECEIVED    │
               └───────┬───────┘
                       ▼
               ┌───────────────┐
               │  VALIDATING   │
               └───────┬───────┘
                       ▼
               ┌───────────────┐
               │   INGESTING   │
               └───────┬───────┘
                       ▼
         ┌─────────────┴─────────────┐
         ▼                           ▼
 ┌───────────────┐           ┌───────────────┐
 │ TRANSCRIBING  │           │EXTRACT_FRAMES │
 └───────┬───────┘           └───────┬───────┘
         │                           │
         ▼                           ▼
 ┌───────────────┐           ┌───────────────┐
 │ANALYZING_AUDIO│           │ANALYZING_VISUAL│
 └───────┬───────┘           └───────┬───────┘
         └─────────────┬─────────────┘
                       ▼
               ┌───────────────┐
               │STRUCT_ANALYSIS│
               └───────┬───────┘
                       ▼
               ┌───────────────┐
               │GENERATE_REPORT│
               └───────┬───────┘
                       ▼
               ┌───────────────┐
               │     READY     │
               └───────────────┘
```

---

## 🚀 6. Upstream Task Cards

### Task 1: `VIDEO-AUDIT-CORE-001`
- **Objective**: Build framework-agnostic `packages/video-audit-core`.
- **Deliverables**:
  - Full TypeScript domain models (`ReferenceAsset`, `TranscriptDocument`, `VideoAuditReport`, `EvidenceItem`).
  - Evidence schema validator (`observed` vs `inferred` vs `hypothesized`).
  - Similarity guard verifying zero verbatim copying of original scripts.
  - 100% unit test coverage for contracts and data normalization.

### Task 2: `VIDEO-AUDIT-PIPELINE-001`
- **Objective**: Asynchronous worker pipeline in `services/dnk_video_ai_creator/` or `apps/api/`.
- **Deliverables**:
  - Supervisor-Worker pipeline: Audio extraction $\to$ WhisperX timestamped transcription $\to$ FFmpeg shot boundary extraction $\to$ Gemini/Claude multimodal structural review $\to$ JSON report assembly.
  - Job tracking with Redis idempotency keys and retry policies.

### Task 3: `VIDEO-AUDIT-TELEGRAM-001`
- **Objective**: Telegram Bot Ingestion & Notification Shell.
- **Deliverables**:
  - Receive video forward / upload in Telegram.
  - Enqueue audit job and provide real-time status updates.
  - Display executive summary with direct link to launch adapted script in Web/PWA Teleprompter.

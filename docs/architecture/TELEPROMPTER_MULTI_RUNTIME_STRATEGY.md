# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/TELEPROMPTER_MULTI_RUNTIME_STRATEGY.md"
# purpose: "Canonical Multi-Runtime Architecture, Framework-Agnostic Core Specification & Task Pipeline for DNK Teleprompter."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TELEPROMPTER-CORE-001", "TELEPROMPTER-WEB-001", "TELEPROMPTER-TMA-001"]
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎬 DNK Teleprompter: Multi-Runtime Architecture & Core Specification

## 📌 1. Strategic Vision & Architectural Invariants

The DNK Teleprompter & Video AI Creator is built as a **unified Web-First Responsive/PWA application** backed by a **framework-agnostic TypeScript Core Engine** (`packages/teleprompter-core`), maintaining strict separation between domain state and platform-specific media runtime adapters.

```
                    ┌───────────────────────────┐
                    │       DNK Core API        │
                    │ FastAPI + PostgreSQL + S3 │
                    │ Redis (Session / Cache)   │
                    └─────────────┬─────────────┘
                                  │ (REST / WebSockets)
       ┌──────────────────────────┼──────────────────────────┐
       │                          │                          │
┌──────▼──────┐           ┌───────▼────────┐          ┌──────▼──────┐
│  Web / PWA  │           │ Telegram Mini  │          │ iOS/Android │
│   Next.js   │           │      App       │          │ React Native│
└──────┬──────┘           └───────┬────────┘          └──────┬──────┘
       │                          │                          │
       └──────────────────────────┼──────────────────────────┘
                                  │ (Adapter Ports)
      ┌───────────────────────────┴───────────────────────────┐
      │         packages/teleprompter-core (Framework-Free)    │
      │  - Script & Prosody Schema (JSON Contract-First)      │
      │  - Word State Machine (Upcoming/Speculative/Confirmed)│
      │  - Speech Alignment & Robust Normalizer / Recovery    │
      │  - WPM Pacer & Vocal Coaching Heuristics              │
      │  - Session Telemetry & Performance Analytics          │
      └───────────────────────────────────────────────────────┘
```

### 🛡️ Core Invariants

| Invariant | Requirement |
| :--- | :--- |
| **Single Source of Truth (SSOT)** | Token states, WPM, speech alignment, and session metrics live exclusively in `teleprompter-core` and are never duplicated in platform adapters. |
| **Framework-Agnostic Core** | `teleprompter-core` has ZERO dependencies on DOM, Next.js, React, React Native, or Telegram WebApp SDK. |
| **Offline-First Resilience** | Script editing, prosody HUD, speech tracking, and local session analytics function 100% offline via IndexedDB. |
| **Privacy-First Audio Pipeline** | Raw microphone streams are processed strictly on-device by default. No audio upload occurs without explicit user consent. |
| **Progressive ASR Enhancement** | Zero-latency Web Speech API $\to$ On-device WASM/WebGPU Whisper $\to$ Opt-in Cloud ASR fallback. |
| **Contract-First Versioning** | `ProsodyDocument` and session analytics events enforce versioned schemas (`schema_version`). |
| **No Premature Native Wrapping** | React Native/Expo development begins strictly after mobile media performance benchmarks on Web/PWA are validated. |

---

## 🧭 2. Domain Boundaries: Content Intelligence Upstream vs Teleprompter Execution

```
Reference Video / URL / Telegram File
              ↓
[packages/video-audit-core]
Reference Asset Ingestion & Validation
              ↓
Multimodal Analysis Pipeline (Speech, Visuals, Structure, Audio, Retention)
              ↓
Evidence-Backed VideoAuditReport (Observed / Inferred / Hypothesized)
              ↓
Niche Adaptation & Script Generation
              ↓
┌────────────────────────────────────────────────────────┐
│ Versioned Contract: ScriptDocument + ProsodyDocument   │
└───────────────────────────┬────────────────────────────┘
                            │ (Consumed by)
                            ▼
[packages/teleprompter-core]
Word State Machine, Vocal Prosody HUD & Real-Time Alignment Engine
                            │
                            ▼
[apps/web / apps/telegram-mini-app]
Camera Stream, Audio Capture, Recording & Remotion Export
```

> **Detailed upstream audit documentation**: See [`docs/architecture/REFERENCE_VIDEO_INTELLIGENCE_STRATEGY.md`](REFERENCE_VIDEO_INTELLIGENCE_STRATEGY.md).

---

## 📦 3. Recommended Package Layout

```text
packages/
  teleprompter-core/
    package.json
    tsconfig.json
    src/
      domain/
        script.ts          # Script scenes, paragraphs, and timing bounds
        token.ts           # Token representation & vocal properties
        prosody.ts         # Prosody notation (punch, tone hold, pauses, pitch, gestures)
        session.ts         # Teleprompter session state & configuration
      alignment/
        normalizer.ts      # Multi-lingual phonetics, punctuation & casing stripping
        matcher.ts         # Levenshtein / phonetic window matching
        recovery.ts        # Out-of-order jump recovery, skipping & backtrack handling
      pacing/
        wpm-controller.ts  # Target vs actual speaking rate calculator
      analytics/
        session-metrics.ts # Vocal stability, pause adherence, duration diffs
      state/
        word-state-machine.ts # Formal state machine for active spoken tokens
      ports/
        asr-provider.ts    # Abstract speech-to-text input port
        media-recorder.ts  # Abstract video/audio capture port & capabilities probe
        runtime.ts         # Platform runtime detection & lifecycle port

apps/
  web/
    src/components/teleprompter/ # Next.js 14/15 Responsive / PWA UI
  telegram-mini-app/            # Lightweight Telegram WebApp container
  mobile/                       # Future React Native / Expo shell
```

---

## 🔄 4. Word State Machine & Alignment Lifecycle

Tokens advance through an explicit, deterministic State Machine to prevent false jumping during continuous speech recognition:

```
               ┌───────────────┐
               │   UPCOMING    │
               └───────┬───────┘
                       │ (Interim ASR match)
                       ▼
               ┌───────────────┐
       ┌───────┤  SPECULATIVE  ├───────┐
       │       └───────┬───────┘       │
       │ (Low conf /   │ (Final ASR    │ (Forward jump /
       │  mismatch)    │  confirmation)│  skipped line)
       ▼               ▼               ▼
┌──────────────┐ ┌───────────┐  ┌─────────────┐
│   UPCOMING   │ │ CONFIRMED │  │   SKIPPED   │
└──────────────┘ └─────┬─────┘  └─────────────┘
                       │
                       ▼
                ┌─────────────┐
                │  COMPLETED  │
                └─────────────┘
```

---

## 🎙️ 5. ASR & Media Recorder Ports

### 5.1 ASR Fallback Chain
```
1. Web Speech API (webkitSpeechRecognition)
   └── (If unsupported or dropped stream)
2. On-Device WASM / WebGPU Whisper (Transformers.js / Whisper.cpp)
   └── (If insufficient local GPU or explicit user opt-in)
3. Cloud ASR Service (FastAPI / Whisper Backend - Explicit Consent Required)
```

### 5.2 Media Recorder Port & Capability Probing
```typescript
export interface MediaCapabilities {
  supportsCamera: boolean;
  supportsMicrophone: boolean;
  supportsMediaRecorder: boolean;
  supportsVideoExport: boolean;
  supportsBackgroundUpload: boolean;
}

export interface MediaRecorderPort {
  probeCapabilities(): Promise<MediaCapabilities>;
  requestPermissions(): Promise<PermissionState>;
  start(options?: RecordingOptions): Promise<void>;
  pause(): Promise<void>;
  resume(): Promise<void>;
  stop(): Promise<RecordingArtifact>;
  dispose(): Promise<void>;
}
```

---

## 🛡️ 6. Evidence & Similarity Governance

1. **Evidence Standard**: Every analytical insight must be classified as `observed` (deterministic measurement), `inferred` (high-confidence semantic model output), or `hypothesized` (unverified engagement theory).
2. **Similarity Guard**: Adaptation must preserve abstract storytelling mechanisms while strictly preventing verbatim script copying, visual frame sequences, copyrighted music, and trademarked branding elements.

---

## 🎯 7. Phased Task Cards & Definition of Done

```
┌────────────────────────────────────────────────────────┐
│ Upstream: VIDEO-AUDIT-CORE-001                         │
│ Multi-Layer Multimodal Audit Contracts & Schemas       │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 1: TELEPROMPTER-CORE-001                         │
│ Framework-Agnostic Domain & Alignment Engine           │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 2: TELEPROMPTER-WEB-001                          │
│ Next.js Responsive PWA Vertical Slice                  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 3: TELEPROMPTER-TMA-001                          │
│ Telegram Mini App Adapter & Bot Distribution Shell     │
└────────────────────────────────────────────────────────┘
```

### Task 1: `TELEPROMPTER-CORE-001`
- **Objective**: Author `packages/teleprompter-core` in pure TypeScript with zero framework dependencies.
- **Deliverables**:
  1. `domain/`: `ScriptDocument`, `ProsodyDocument`, `Token` models.
  2. `state/`: `WordStateMachine` with speculative vs confirmed speech transitions.
  3. `alignment/`: `Normalizer`, `Matcher`, and `RecoveryEngine` for jump/skip recovery.
  4. `pacing/`: `WPMController` real-time pacing engine.
  5. `ports/`: `ASRProviderPort`, `MediaRecorderPort`, `RuntimePort`.
  6. **Quality Gate**: 100% unit test coverage for state transitions, fuzzy normalization, and recovery jumps.

### Task 2: `TELEPROMPTER-WEB-001`
- **Objective**: Implement responsive Next.js 14/15 PWA vertical slice in `apps/web/`.
- **Deliverables**:
  1. `ProsodyHUD` & `WordHighlighter` components rendering dynamic emphasis and gesture cues.
  2. `WebSpeechProvider` implementing `ASRProviderPort`.
  3. `WebMediaRecorderAdapter` implementing `MediaRecorderPort` with camera preview toggle.
  4. IndexedDB persistence for offline scripts and session recovery.
  5. Cross-platform validation: iPhone Safari, Android Chrome, Desktop Chrome.

### Task 3: `TELEPROMPTER-TMA-001`
- **Objective**: Telegram Mini App container integration.
- **Deliverables**:
  1. `TelegramRuntimeAdapter` with `initData` HMAC backend authentication.
  2. Bot command integration (`/prompt <script_id>`, voice-to-script webhook).
  3. Seamless one-tap recording and return-to-chat video pipeline.

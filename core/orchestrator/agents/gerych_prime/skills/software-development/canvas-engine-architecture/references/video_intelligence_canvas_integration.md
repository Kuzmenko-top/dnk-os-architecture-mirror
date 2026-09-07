# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/canvas-engine-architecture/references/video_intelligence_canvas_integration.md"
# purpose: "Reference Specification for Video Intelligence & Multimodal Audit Canvas Integration (Phase 5)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Phase 5: Video Intelligence & Multimodal Audit Node Integration

This reference spec defines the architecture, data structures, and implementation practices for integrating social video intelligence capabilities (ASR, scene boundaries, OCR, audio features, hook score, and claim verification) directly into the Spatial Canvas.

---

## 🧭 1. Multimodal Audio-Video Core Architecture (`@dnk/video-audit-core`)

The backend processing is split into specialized workers orchestrated by a central pipeline in Python. The module is located at `packages/video_audit_core/`.

### A. Sub-Worker Pipeline Design
To ensure high-performance concurrent processing, the video audit core employs separate specialized modules:
1. **`transcription_adapter.py` (`WhisperXTranscriptionAdapter`):**
   - Transcribes audio using WhisperX.
   - Outputs word-level timestamps (`start`, `end`) and assigns speaker IDs (diarization).
2. **`scene_extraction_worker.py` (`SceneExtractionWorker`):**
   - Uses shot-boundary detection to slice video into narrative scene segments.
   - Extracts representative keyframe images and logs movement velocity.
3. **`ocr_worker.py` (`OCRWorker`):**
   - Captures text on-screen via optical character recognition.
   - Maps bounding boxes to normalized canvas-space coordinates (`[x1, y1, x2, y2]`).
4. **`audio_feature_worker.py` (`AudioFeatureWorker`):**
   - Extracts pitch, volume envelopes (prosody), BGM/Voice ratio, and musical tempo (BPM).
5. **`hook_retention_analysis.py` (`HookRetentionAnalyzer`):**
   - Performs a rigorous visual/narrative audit of the first 3 seconds ("the hook").
   - Generates second-by-second retention curve points and recommendations to prevent scrolling.
6. **`claim_verification.py` (`ClaimVerificationEngine`):**
   - Extracts statements and labels them:
     - `Observed` (🟢 verified explicit fact).
     - `Inferred` (🟡 implied or logically deduced statement).
     - `Hypothesized` (🔴 unverified or exaggerated marketing claim).

### B. Unified Orchestration Payload Shape
The Orchestrator gathers output from all sub-workers into a consolidated JSON payload:
```json
{
  "status": "success",
  "metadata": {
    "duration_seconds": 15.4,
    "fps": 30.0,
    "resolution": "1080x1920"
  },
  "hook_analysis": {
    "score": 88,
    "retention_curve": [
      {"second": 0, "retention": 100},
      {"second": 1, "retention": 94},
      {"second": 2, "retention": 89},
      {"second": 3, "retention": 85}
    ],
    "strengths": ["Strong verbal hook within 0.5s", "Immediate brand logo display"],
    "weaknesses": ["Volume dips at second 2.1"],
    "recommendations": ["Boost voice volume in the first 3s"]
  },
  "transcription": [
    {
      "start": 0.1,
      "end": 2.3,
      "text": "Привіт! Це новий крем від DNK OS.",
      "speaker": "SPEAKER_01"
    }
  ],
  "scenes": [
    {
      "start": 0.0,
      "end": 3.0,
      "keyframe_url": "data:image/png;base64,...",
      "description": "Close-up of product packaging"
    }
  ],
  "ocr": [
    {
      "timestamp": 1.2,
      "text": "100% ORGANIC",
      "bbox": [100, 200, 400, 250]
    }
  ],
  "audio_features": {
    "bpm": 120,
    "average_energy": 0.78,
    "voice_bgm_ratio": 1.5,
    "pauses": [
      {"start": 4.1, "end": 4.8}
    ]
  },
  "claims": [
    {
      "text": "Зменшує зморшки за 7 днів",
      "category": "Hypothesized",
      "timestamp": 6.5,
      "evidence": "Requires clinical proof"
    }
  ]
}
```

---

## 🎨 2. React Flow UI Node Integration (`VideoAuditReportNode.tsx`)

The spatial canvas node provides an immersive, analytical UI displaying video audit results across 6 interactive tabs.

### A. Progressive Ingest State Machine
To guide users during long-running multimedia AI processes, the node implements a progressive state machine showing clear steps:
- `idle` ➡️ Prompt to paste a video URL (TikTok, Reels, Shorts).
- `downloading` ➡️ Fetching video bytes.
- `transcribing` ➡️ WhisperX voice extraction.
- `analyzing` ➡️ Scene slicing, OCR bounding box mapping, audio profiling.
- `generating` ➡️ Hook retention modeling and claim classification.
- `completed` ➡️ Display full 6-tab analysis workbench.

### B. Hook Retention SVG Curve Rendering
Draw custom SVG vector coordinates to represent the 3-second attention curve smoothly:
```tsx
const points = data.hook_analysis.retention_curve; // e.g. [{second:0, retention:100}, ...]
const pathData = `M 0,${100 - points[0].retention} ` + 
  points.map((p, i) => `L ${p.second * 80},${100 - p.retention}`).join(' ');

return (
  <svg className="w-full h-24 stroke-teal-500 fill-none stroke-2">
    <path d={pathData} />
  </svg>
);
```

### C. Six-Tab Modular Layout Configuration
1. **Хук (Hook Analysis):** Circular score wheel (0-100) + SVG Retention Curve + detailed list of actionable suggestions.
2. **Транскрипція (ASR):** Chronological timeline of dialogue segments with Speaker tags. Clicking a segment seeks the video player.
3. **Кадри (Scene Timeline):** Visual layout of keyframes with scene duration and camera activity description.
4. **OCR Текст (On-Screen Text):** Captures text overlay timestamps, highlighted boxes, and translation layers.
5. **Аудіо (Audio Analytics):** Graph showing volume amplitude profiles, tempo (BPM), and speech-to-music energy balance.
6. **Верифікація (Claim Verification):** Interactive table categorized into:
   - `Observed` (🟢 green)
   - `Inferred` (🟡 yellow)
   - `Hypothesized` (🔴 red)

---

## 🛠️ 3. TypeScript Integration & IsolatedModules Compiling Pitfalls

### A. Resolving TypeScript `isolatedModules` Conflicts
Under strict Vite or Next.js tsconfig configurations (`"isolatedModules": true`), exporting types and concrete schemas in a single statement will throw build-time syntax errors.
- **Problematic Export:**
  ```typescript
  export { Scene, SceneSchema } from './schemas/audit.js'; // Fails!
  ```
- **Mandatory Clean Export Invariant:**
  ```typescript
  export type { Scene } from './schemas/audit.js';
  export { SceneSchema } from './schemas/audit.js';
  ```

### B. Dual Python Module & TypeScript Symlink Support
- To support native Python imports using clean snake_case directories (`import packages.video_audit_core`), rename the package directory to `packages/video_audit_core/`.
- To maintain seamless backwards-compatibility with TypeScript imports and npm configurations using kebab-case (`@dnk/video-audit-core`), create a symlink:
  ```bash
  ln -s video_audit_core packages/video-audit-core
  ```

---

## 🧪 4. Testing & Validation Invariants

- **Python Tests (`tests/media/test_video_audit_core.py`):** Assert that the `VideoAuditOrchestrator` runs all sub-workers and outputs the correct structured JSON schema with valid hook retention scores, transcript lists, and verified claims.
- **Master Quality Gate Validation:**
  Before finishing a phase, run:
  ```bash
  PYTHONPATH=. .venv/bin/pytest tests/media/test_video_audit_core.py
  ```
- **Automated Evidence Reporting:**
  To commit and seal the Phase 5 deliverables, generate official manifests via:
  ```bash
  python3 scripts/system/generate_evidence.py --task DNK-OS-PHASE5 --title "Phase 5: Video Intelligence" --components apps/web/components/canvas/nodes/VideoAuditReportNode.tsx packages/video_audit_core/...
  ```

# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/teleprompter_multi_runtime_architecture.md"
# purpose: "Canonical Multi-Runtime Protocol & Framework-Agnostic Core Architecture for Teleprompter & Video AI Studio."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TELEPROMPTER-CORE-001", "TELEPROMPTER-WEB-001", "TELEPROMPTER-TMA-001"]
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎬 Multi-Runtime Teleprompter & Video Studio Architecture

## 1. Core Operating Principles

1. **Framework-Agnostic TypeScript Core (`packages/teleprompter-core`)**:
   - Zero dependencies on React, Next.js, DOM, React Native, or Telegram WebApp SDK.
   - Houses the Word State Machine, speech normalization & fuzzy matching, WPM pacing controller, and session analytics.

2. **Multi-Runtime Deployment Strategy**:
   - **Canonical Web / Responsive PWA (`apps/web/`)**: Base application supporting desktop & mobile browsers (iPhone Safari, Android Chrome) and installed PWA mode.
   - **Telegram Mini App (`apps/telegram-mini-app/`)**: Acquisition and fast-capture channel sharing the same backend API and models (`User`, `Script`, `Project`, `TeleprompterSession`).
   - **React Native / Native Mobile (`apps/mobile/`)**: Deployed ONLY after media performance benchmarks validate native camera sensor lock, haptics, or hardware remote requirements. Avoid empty WebView wrappers per App Store Guideline §4.2.

3. **Deterministic Word State Machine**:
   - Tokens transition strictly through:
     `UPCOMING` ➔ `SPECULATIVE` (interim ASR) ➔ `CONFIRMED` (final ASR) ➔ `COMPLETED`
   - Transitions support `SKIPPED` (forward jump), `MANUAL_RESET` (user override), and direct `UPCOMING` ➔ `COMPLETED` for rapid final ASR hypothesis confirmation.

4. **Port & Adapter Abstractions**:
   - `ASRProviderPort`: Multi-tiered fallback (`WebSpeechProvider` ➔ On-Device WASM/WebGPU Whisper ➔ Opt-in Cloud ASR).
   - `MediaRecorderPort`: Explicit capability probing (`probeCapabilities()`) before starting recording.

5. **Task Rollout Pipeline**:
   - **`TELEPROMPTER-CORE-001`**: Framework-agnostic domain and alignment engine with 100% unit tests (Completed).
   - **`TELEPROMPTER-WEB-001`**: Next.js responsive PWA vertical slice (Prosody HUD, WebSpeech, IndexedDB, camera preview) (Completed).
   - **`TELEPROMPTER-TMA-001`**: Telegram Mini App runtime adapter and bot shell.

## 2. Technical Invariants & Implementation Lessons

1. **TypeScript NodeNext ESM Module Import Rules**:
   - When building pure TypeScript packages under `"moduleResolution": "nodenext"`, internal relative imports in `.ts` files MUST use `.js` extension (e.g. `import { X } from './tokens.js'`). Omitting extension or using `.ts` extension causes `tsc` compile errors.

2. **ASR Alignment State Machine Direct Transitions**:
   - `TokenStateMachine` must allow direct transition `upcoming` ➔ `completed` in `VALID_TRANSITIONS` for final ASR hypotheses that confirm words directly without intermediate `speculative` states.

3. **Ukrainian Stem Prefix Bonus in Levenshtein Fuzzy Matcher**:
   - Grammatical inflections in Ukrainian (e.g. `зливають` vs `зливає`) have word ending variations. `DefaultTextNormalizer` and `WordMatcher` apply a stem prefix bonus (common prefix $\ge 4$ characters) to keep fuzzy similarity above alignment threshold ($0.70$).

4. **Monotonic Hypothesis Sequence Validation**:
   - `ASRHypothesis` requires `sequence: number` to reject out-of-order or duplicate speech hypothesis frames via `OutofOrderHypothesisError`.

5. **Browser Adapter Isolation & Capability Probing (`TELEPROMPTER-WEB-001`)**:
   - WebSpeech API, MediaRecorder, IndexedDB, and Screen Wake Lock are strictly isolated in `apps/web/src/adapters/teleprompter/`.
   - **IndexedDB SSR / Headless Fallback**: `IndexedDbSessionStore` automatically provides an in-memory `Map`-backed store when `window.indexedDB` is unavailable (such as during SSR or Node.js test runners like Vitest/Jest).
   - **Deterministic Mock ASR Stream**: `MockASRStreamProvider` generates predictable word streaming hypotheses with configurable WPM, `startIndex`, and `enableInterim` options for headless test execution and devices without Web Speech API.
   - **PWA Viewport & Camera Mirroring**: `PrompterViewport` implements camera preview mirroring via CSS `transform: scaleX(-1)` and safe-area inset spacing (`env(safe-area-inset-top)`) for iPhone notch/dynamic island compatibility.

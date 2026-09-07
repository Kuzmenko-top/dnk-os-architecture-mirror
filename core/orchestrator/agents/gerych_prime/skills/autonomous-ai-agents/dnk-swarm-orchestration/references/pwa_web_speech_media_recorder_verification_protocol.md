# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/pwa_web_speech_media_recorder_verification_protocol.md"
# purpose: "Canonical Protocol for PWA Web Speech, MediaRecorder Adapters and Master Quality Gate Verification."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---

# 🎙️ PWA Web Speech, MediaRecorder & Quality Gate Acceptance Protocol

## 1. Quality Gate Acceptance Invariant (Beyond 0 LSP Diagnostics)

Static type checking (`tsc --noEmit` or `0 diagnostics`) is a necessary baseline but is NOT sufficient for full Quality Gate acceptance. Full verification requires:
1. **Adapter Test Execution**: Unit/integration tests testing public port contracts directly against mocking environments (e.g. `teleprompter-web-adapters.test.ts`).
2. **SSR Execution Safety**: Ensuring zero raw `window` or `navigator` accesses during server-side module import/evaluation.
3. **MIME Type Negotiation**: Runtime detection via `MediaRecorder.isTypeSupported` (`video/webm;codecs=vp9` -> `video/webm` -> `video/mp4`).
4. **ASR Stream Monotonicity**: Verifying sequence numbers (`sequence`), deduplication of repeat hypotheses, and rejection of out-of-order packets.
5. **Deterministic Storage Fallback**: Graceful degradation from IndexedDB to in-memory fallback during SSR or browser permission restrictions.

---

## 2. Deterministic Recording Lifecycle (STOP Flow)

To prevent media corruption or race conditions when stopping a live speech & video recording session, enforce the following sequence:

```text
STOP_REQUESTED
  ↓
ASR_STOPPED (WebSpeech / MockStream unbinds and stops emitting hypotheses)
  ↓
MEDIA_STOPPED (MediaRecorder triggers ondataavailable + onstop)
  ↓
BLOB_FINALIZED (Video/Audio blob packaged from recorded chunks)
  ↓
SESSION_SAVED (IndexedDB persistent session record + analytics stored)
  ↓
TRACKS_RELEASED (Camera & microphone tracks cleaned up via stream.getTracks().forEach(t => t.stop()))
  ↓
SUMMARY_READY (Performance metrics & SessionSummary display)
```

---

## 3. Evidence JSON Contract

Every accepted task vertical slice must produce an Evidence JSON at `docs/reports/evidence_<TASK_ID>.json`:
- `task_id`: Canonical Task DNA identifier.
- `package_versions`: SSOT package version mappings.
- `git_commit`: Active git commit SHA.
- `test_command` & `typecheck_command`: Commands executed for verification.
- `browser_adapter_tests`: Detailed test results and coverage checklist.
- `integration_tests`: Summary of monorepo regression suite passes (`verify_all.sh`).
- `master_gate_result`: `"PASSED"`.
- `timestamp`: ISO-8601 UTC timestamp.
- `known_limitations`: Documented edge cases (e.g. iOS Safari user interaction requirements).

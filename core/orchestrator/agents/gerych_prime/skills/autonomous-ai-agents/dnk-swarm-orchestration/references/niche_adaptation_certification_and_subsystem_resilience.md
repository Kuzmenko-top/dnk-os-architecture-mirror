# Niche Adaptation Certification & Subsystem Resilience Protocol (VIDEO-AUDIT-PIPELINE-001E-F-R1)

## 1. Niche Adaptation Engine Architecture
The Niche Adaptation Engine (`packages/video-audit-core`) provides deterministic video auditing, speech analysis, prosody verification, and e-commerce adaptation for specialized product niches (e.g., ReBurn smokehouse equipment).

### Core Invariants:
1. **Sidecar Caching (`social-knowledge-base`)**:
   - Cache video assets and transcribed text in structured sidecars:
     `references/{referenceAssetId}/source/{sha256}.mp4`
     `transcript/{provider}-{model}-{version}.{json,vtt,txt}`
   - Prevents duplicate heavy WhisperX ASR inference calls across re-audits.
2. **Multimodal Frame Deduplication (`mcp-video-analyzer`)**:
   - Filter static duplicate frames before LLM ingestion across 4 modes: `fast`, `balanced`, `deep`, `forensic`.
3. **Deterministic Similarity Isolation**:
   - Production logic uses real Jaccard + n-gram similarity analysis.
   - Test suites utilize `deterministicSimilarityMode: true` to avoid test flakiness while keeping production algorithms untouched.
4. **Fail-Closed Guardrails**:
   - Missing prosody or missing shotlist transitions status to `rejected`, NEVER `manual_review`.
5. **Speech Timing Normalization**:
   - Voiceover pacing calculated strictly at 130 WPM with a ±20–25% duration tolerance window.
6. **Dual Node/Python Monorepo Symlink**:
   - Directory: `packages/video-audit-core` (npm/pnpm standard).
   - Symlink: `packages/video_audit_core -> video-audit-core` (Python import resolution).

## 2. Subprocess Timing & Test Resilience
When testing asynchronous agent processes or subprocess lifecycle:
- **Flawed Pattern**: `time.sleep(0.2)` expecting child processes to spawn, load Python virtualenv modules, and create lock/checkpoint files.
- **Resilient Pattern**: Bounded polling loop with millisecond intervals:
  ```python
  start_wait = time.time()
  while time.time() - start_wait < 3.0:
      if os.path.exists(lock_file) and os.path.exists(checkpoint_file):
          break
      time.sleep(0.05)
  ```

## 3. Path Hygiene Allowlist Management
When adding staging directories, version snapshots, or audit artifacts:
- Update `core/playbooks/scripts/enforce_relative_paths.py` and `tests/verification/test_path_hygiene.py` with:
  `"core/hermes_versions"`, `"core/hermes_agent_staging"`, `"cache"`, `"sessions"`, `"checkpoints"`, `"docs/audit"`.

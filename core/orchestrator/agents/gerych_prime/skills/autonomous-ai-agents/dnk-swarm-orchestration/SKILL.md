---
name: dnk-swarm-orchestration
description: Run and coordinate Gerych and DNK OS multi-agent swarms.
category: autonomous-ai-agents
version: "1.0.0"
author: "DNK-e.com Maksym"
license: "MIT"
metadata:
  hermes:
    tags: ["swarm", "orchestration", "gerych", "dnk-os", "circuit-breaker"]
    related_skills: ["sota-repository-assimilation", "sdlc-review"]
    references:
      - "references/swarm_tool_kwargs_and_isolation.md"
      - "references/adversarial_audit_and_uncommitted_release_hygiene.md"
      - "references/structured_logging_and_distributed_tracing_protocol.md"
      - "references/stateless_agent_runtime_and_disk_hygiene.md"
      - "references/unified_swarm_control_plane_and_engine_consolidation.md"
      - "references/dynamic_context_budgeting_and_toolset_pruning.md"
      - "references/mcp_slim_guard_meta_tools_protocol.md"
      - "references/git_context_branching_and_isolation_protocol.md"
      - "references/critical_security_guards_and_evidence_verification_protocol.md"
      - "references/system_audit_git_hygiene_and_memory_buffer_protocol.md"
      - "references/ephemeral_cwd_drift_and_swarm_hygiene.md"
      - "references/session_sentinel_and_loop_hardening_protocol.md"
      - "references/chief_architect_mentor_and_human_task_intake_protocol.md"
      - "references/swarm_health_dashboard_and_multi_priority_architecture.md"
      - "references/agent_swarm_benchmarks_and_ledger_worktree_patterns.md"
      - "references/swarm_shared_ledger_topologies_and_hud_protocol.md"
      - "references/subagent_sandbox_and_zero_loss_handshake_protocol.md"
      - "references/dnk_os_2_0_system_skeleton_and_4tier_memory_protocol.md"
---

# 🐝 DNK Swarm Orchestration & Gerych Lifecycle Protocol

## When to Use
Use when launching, coordinating, or debugging Gerych Prime and specialized Swarm agents (`gerych_builder`, `gerych_researcher`, `gerych_auditor`, `dnk_shopify`, `dnk_dev_fullstack`) within the DNK OS ecosystem. See `references/agent_swarm_benchmarks_and_ledger_worktree_patterns.md` for architectural SOTA evaluations (ruflo, ccswarm, swarms) and adoption patterns (Ledger vs Executor, Git Worktree isolation).

## 🎯 Core Operating Invariants

### 1. Single Entry Point & Execution Root
- Always launch Gerych via the canonical root wrapper:
  ```bash
  ./scripts/system/gerych.sh "Task prompt or DNA goal"
  ```
- For parallel swarm multi-agent runs:
  ```bash
  ./scripts/system/gerych_swarm.sh --parallel
  ```
- Ensure execution root is always `$HUB_ROOT` with inherited `.venv` and `$PYTHONPATH`.

### 2. Anti-Duplication & Process Hygiene (Singleton Lock Pattern)
- Prevent zombie processes and SQLite database locks (`.hermes/sessions.db`, `canvas_production_fallback.db`):
  * Check and acquire single-instance lock via `python3 scripts/system/process_guard.py --check-lock <agent_name>`.
  * Auto-reap dead/stale instances using `process_guard.py --audit` upon launcher startup.
  * Release lock cleanly on exit via process trap.
  * Isolate `HERMES_HOME` per specialized swarm agent when running in parallel.

### 3. Proactive Auth Watchdog & Auto-Sanitizing Hooks
- **Proactive Token Refresh**: Validate OAuth token lifetime prior to execution. If under 10m TTL, automatically refresh via `gcloud auth print-access-token` to prevent 401 drops mid-task.
- **Smart Path Auto-Sanitizer**: `hermes_pre_tool_hook.py` transparently intercepts absolute repo paths (`/Users/.../DNK_HUB/...`) and translates them to valid relative paths (`services/...`, `apps/...`) with `{"action": "modify"}`.
- **No `sys.path` Manipulation**: Rely on environment `$PYTHONPATH`, never insert or append to `sys.path`.
- **Loop Breaker & Isolated Trackers**: Track patch frequency per session in `/tmp/hermes_loop_tracker_<session_id>.json`; halt repeated blind edits without tests.

### 4. Quality Gate Test Runner & Rate Limit Invariant
- **Symptom**: Bulk API test runs fail with HTTP 429 (Too Many Requests).
- **Fix**: In `./scripts/verify_all.sh`, always set `export SECURITY_RATE_LIMIT=100000` before invoking pytest. Use the project virtualenv binary (`.venv/bin/pytest`) with `-m "not live and not flume and not slow"`.

### 5. Runtime Artifact & Disk Space Hygiene
- **Disk Saturation Alert**: When disk capacity exceeds 90%, prune Docker build cache (`docker builder prune -a -f`), clean old visual_shell temp artifacts (`visual_shell/open_design/.tmp/`), and purge stale `.pytest_cache` / `__pycache__`.
- **Fast Non-Blocking Probing**: Avoid running deep recursive shell find loops across entire user home trees; use bounded `du -sh` or directory-specific target checks.
- **Stateless Agent Directory Invariant**: Agent profile directories (`core/orchestrator/agents/<agent>/`) must remain strictly stateless and declarative (`SOUL.md`, `agent_card.yaml`, `skills/`, `memories/`).
- **Runtime State & Cache Isolation**: All ephemeral runtime data (`state.db`, `verification_evidence.db`, `lsp/`, `checkpoints/`, `cache/`, `logs/`) must be isolated to `~/.hermes/runtime/<agent>/` (via launcher symlinks or dynamic environment redirect). (See `references/stateless_agent_runtime_and_disk_hygiene.md`).
- **SQLite WAL & VACUUM Maintenance**: Before migrating or archiving `state.db`, run `PRAGMA wal_checkpoint(TRUNCATE);` followed by `VACUUM;` to reclaim bloated disk pages and truncate `.db-wal` logs.

### 6. Hierarchical Memory Tiering (L1 / L2)
- **L1 (Fast System Context)**: Keep `MEMORY.md` strictly under 1,000-1,500 chars (identity, language, core invariants).
- **L2 (Deep Cognitive Knowledge)**: Query SCONES (`scones_get_memories(query=topic)`) for architectural patterns, donor digests, and historical solutions.

### 7. Spatial Canvas Node & Web App Synchronicity
- **Spatial Node Registration**: All Spatial Nodes (`SwarmAgentNode`, `ShopifyBuilderNode`, `VideoCreatorNode`, `SmartNoteNode`) must be registered in `NodeRegistry.ts` and `CanvasEngine.tsx` with explicit TypeScript schemas, 4-directional connection handles, and DNK Dark Luxury styling (`#060913` obsidian glass, neon accents).
- **Interactive Node Lifecycle & Dock**: Bottom dock (`StudioDock.tsx`) supports quick spawning (`+ Swarm`, `+ Shopify`, `+ Video`, `+ Smart Note`) with non-overlapping layout offsets and cascading edge pruning on deletion (`InspectorPanel.tsx`).
- **Local Persistence Engine**: Automatic debounced `localStorage` saving (`dnk_studio_canvas_nodes`, `dnk_studio_canvas_edges`), Layout Reset, and JSON Import/Export capabilities.
- **Real-Time Swarm Bridge**: `SwarmAgentNode` connects directly to `/api/v3/canvas/ws` to stream agent thoughts, execution logs, and dispatch commands in real time. (See `references/spatial_nodes_and_websocket_bridge.md`).
- **Dual-Tree Web Sync**: Always synchronize canvas and UI components between `apps/web/components/canvas/` and `apps/web/components/canvas/` (and `workspace/`) to guarantee identical React Flow runtimes.
- **Artifact & DB Hygiene**: Never commit transient SQLite/log files (`*.db`, `*.sqlite`, `*.sqlite3`, `*.log`). Ensure `.gitignore` ignores all local fallback databases.
- **Phase 3 Autonomous Co-Pilot Toolbar & Swarm Cascade**:
  * **Copilot Integration**: Embed `CopilotToolbar` with `[⚡ AI Co-Pilot]` buttons inside all key node templates (`StrategyMarkdownNode`, `DesignGalleryNode`, `ApiDocsCodeNode`, `SprintKanbanNode`) targeting dedicated agent roles (`dnk_marketing_cmo`, `dnk_video_ai_creator`, `dnk_shopify` / `dnk_dev_fullstack`, `gerych_builder`).
  * **Asynchronous Token Streaming & Buffering**: Utilize `AgentCopilotService.executeCoPilot` to stream token chunks sequentially into the UI, updating the localized state and maintaining clean loading feedback.
  * **Reactive Multi-Node Cascade**: Wire `SwarmPropagationEngine` to `canvasStore.ts` via `propagateSwarm(sourceNodeId, outputPayload, brand)`. Propagate upstream updates chronologically and topologically down connected edges (e.g. `Strategy` ➔ `Design` ➔ `Code` ➔ `Kanban`), mutating payloads while maintaining 100% path isolation for unconnected subgraphs.
  * **Undo/Redo & Transactions**: Every programmatic swarm mutation MUST push a state snapshot to `history.past` and clear `history.future` to guarantee seamless transactional rollbacks. Tests should assert store length and history boundaries under `tsx --test`.

### 8. Task-DNA Structured Hand-off
Before execution, define the structured task contract:
1. **Scope & Files**: Exact relative target paths.
2. **Interface Contracts**: Method signatures, argument types, return models.
3. **Quality Gate Target**: Specific test files and full verification (`bash scripts/verify_all.sh`).

### 9. Master Quality Gate & Evidence Verification
- Run `bash scripts/verify_all.sh` to certify 100% Green test status.
- Generate signed evidence:
  ```bash
  python3 scripts/system/generate_evidence.py --task <TASK_ID> --title "<TITLE>" --components <FILES...>
  ```
- **Dual-Channel Handoff Briefing Invariant**: In addition to terminal briefings, every completed epic or major architectural step must generate a structured Markdown report in `docs/reports/<TASK_ID>_handoff.md` with full architecture specifications, schema diffs, and verification metrics (adhering strictly to relative paths and DNK-STD-0075 MRH headers).
- **Fail-Closed Pre-PR Quality Gate & Fast-Path Protocol**: Pull requests created via `mcp__github__create_pull_request`, `gh pr create`, or GitHub REST API are physically intercepted and blocked fail-closed by `scripts/system/hermes_pre_tool_hook.py` unless fresh Master Quality Gate evidence (`docs/audit/*-evidence.json` <= 15 min old, 100% Green) is present and zero unverified file mutations exist. PR sync is idempotent (auto-updates existing open PR for the branch without duplication). See `references/github_mcp_fast_path_and_pre_pr_gate.md`.

### 10. Multi-Stack Docker Compose, Submodule & Repository Optimization Hygiene
- **Docker Live Verification Invariant**: Never report frontend or API services as "🟢 HTTP 200 OK" based on build exit codes alone. Always execute real probe commands (`curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000` and `curl -s http://localhost:8000/health`) and verify `docker ps` status.
- **Multi-Stage Dockerfile Target Directives**: When `docker-compose.yml` targets a builder stage (`target: node-builder`), ensure the stage specifies `ENV HOSTNAME="0.0.0.0"`, `ENV PORT=3000`, `EXPOSE 3000`, and `CMD ["npm", "start"]` to avoid instant `Exited (0)` termination.
- **Docker Image Pruning & Orphan Reaping**: See `references/docker_stack_verification_and_prune_protocol.md` for clean teardown, `docker image prune -a -f`, and orphan cleanup.
- **Docker Port Conflicts (`6379`, `5433`, `5432`, `3000`, `8000`)**: The project contains three compose setups: root `docker-compose.yml` (project `dnk_hub`), `DNK OS/docker-compose.yml` (project `dnk_os`), and `docker-compose.mvp.yml` (minimal MVP stack). If port collisions occur on `docker compose up --build`:
  * Check existing containers via `docker ps`.
  * Stop the conflicting stack via `docker compose -f DNK OS/docker-compose.yml stop` or `docker compose down` before launching the root or MVP stack.
  * Always implement pre-flight check in deployment scripts (e.g., `lsof -Pi :$port -sTCP:LISTEN -t`) to verify that standard ports `3000`, `8000`, `5432`, `6379` are clean before attempting automated MVP docker launches.
  * For long-running `docker compose up --build`, always run in background (`background=true` with `notify_on_complete=true`) or with `-d`.
- **Submodule Git Staging**: When staging commits inside `DNK_HUB/`, nested unpopulated directories/submodules (such as `services/dnk_shopify/DNK-e.com`) must be excluded from `git add` using `git -C DNK OS add -- ":(exclude)services/dnk_shopify/DNK-e.com"`, followed by updating the top-level repository's submodule pointer.
- **Repository Optimization (`git gc`)**: On multi-GB monolithic repositories, run `git gc --prune=now --aggressive` with `background=true` and `notify_on_complete=true` (monitoring via `process(action='wait')`) to avoid foreground 300s/600s timeouts and achieve a single clean pack-file with 0 loose objects.
- **MVP Stack Deployment Reference**: See `references/mvp_minimal_stack_deployment.md` for standard layouts, automated pre-flight checks, robust health probes, PostgreSQL schema auto-creation (`CREATE SCHEMA IF NOT EXISTS`), markdown path hygiene sanitization, beta launch onboarding cadences, and dual-channel terminal/markdown reporting protocols.
- **Docker Build Context Optimization**: See `references/docker_build_context_optimization_and_mvp_sync.md` to solve Docker compose build timeouts, optimize `.dockerignore` context size from GBs to MBs, and streamline local-first sync loops.

### 11. Monorepo Double-Nesting & Reconciliation Hygiene
- **Double-Hub Mirroring**: Prevent root repo (`DNK_HUB`) and nested checkout (`DNK_HUB`) from maintaining parallel duplicated trees.
- **Unified SSOT**: Consolidate all drift into root monorepo. Relocate loose domain assets (e.g. Shopify theme files) into dedicated service paths (`services/dnk_shopify/`). Purge tracked `.DS_Store` and fallback `.db` files.
- **Security & Gate Audits**: Scan agent configs for raw PAT tokens, enforce containment via `${GITHUB_PERSONAL_ACCESS_TOKEN}` placeholders without remote token revocation (unless directed), ensure verification scripts have no legacy paths (`DNK OS`), and unmask suppressed test suites (`-k`) by handling missing DB extensions (e.g. `pgvector`) gracefully in migration fixtures.
- **Reference**: See `references/monorepo_audit_and_reconciliation.md` for full audit procedures.

### 12. Open Design (Visual Shell) ⇄ Hermes ACP & Native MCP Server Integration
- **Hermes ACP Extra Dependency**: `hermes acp --check` requires the `agent-client-protocol` dependency (`uv pip install -p .venv -e '.[acp]'` in `core/hermes_agent`). If missing, Open Design daemon falls back to `antigravity` (`agy`).
- **Port Topology Invariant**: Daemon REST/WebSocket API runs on `7456` (`Cannot GET /` on browser root). The graphical Next.js/Vite Canvas UI runs on `5173` (or `3000`), connecting to daemon at `7456`.
- **Default Agent Priority**: Keep `'hermes'` at index 0 of `CANONICAL_AGENT_ORDER` in `apps/web/src/App.tsx` and labeled `Hermes (Герич · DNK OS)` in `agentLabels.ts`.
- **Native MCP Registration**: Register Open Design MCP helper via `hermes config set mcp_servers.open-design...`. Use `~` for path hygiene (`OD_DATA_DIR: "~/Library/Application Support/Open Design/namespaces/release-stable/data"`).
- **Reference**: See `references/open_design_visual_shell_integration.md` for full architecture, MCP setup, and launch instructions.

### 13. Modular Brick Registry & Standalone App Export Protocol (AI Product Foundry)
- **6 Core Bricks Registry**: Modular domains (`brick_01_agentic_brain` ... `brick_06_web_api_shell`) managed via `core/bricks/` manifests and Pydantic v2 contracts.
- **Topological DAG Resolution**: `DNKBrickRegistry.resolve_dependencies()` enforces dependencies-first ordering and cycle detection.
- **Standalone Export CLI**: `python3 scripts/export_standalone_app.py --app-id <name> --bricks <brick_list> --target-dir <path>` builds isolated Tier-2 repositories.
- **Verification Gate**: Ensure 100% green tests via `.venv/bin/pytest tests/bricks/test_brick_registry.py -v`.
- **Reference**: See `references/modular_brick_registry_foundry.md` for complete schema definitions, matrix, and export pipelines.

### 14. Multi-Runtime Teleprompter & Video AI Architecture Protocol
- **Contract-First Upstream Foundation**: `@dnk/video-audit-core` (`packages/video-audit-core`) provides canonical SSOT contracts (`ScriptDocument`, `ProsodyDocument`, `ShotList`, `AdaptationResult`, `VideoAuditReport`) with Zod schemas, evidence classification (`observed`, `inferred`, `hypothesized`), similarity risk policies, and zero framework dependencies.
- **Framework-Agnostic Core SSOT**: `packages/teleprompter-core` consumes `ScriptDocument` and `ProsodyDocument` to drive deterministic Word State Machine (`upcoming` → `speculative` → `confirmed` → `completed`), alignment/recovery, WPM pacing, and session metrics with 0 DOM/React dependencies.
- **Three-Tier Runtime Strategy**: Web/Responsive PWA (Canonical MVP) → Telegram Mini App (Acquisition/Fast Capture) → React Native/Expo (Performance/Native Sensors).
- **Anti-Wrapper App Store Invariant**: Never package plain WebViews for App Store; require native camera sensors, haptics, Photos export, and background processing.
- **Reference**: See `references/video_audit_core_contract_first_protocol.md`, `references/teleprompter_multi_runtime_architecture.md`, `references/voice_ai_remotion_exporter_and_standalone_rebuild.md` and `docs/architecture/TELEPROMPTER_MULTI_RUNTIME_STRATEGY.md`.

### 15. Production-Grade IndexedDB Storage Engine, Differential Snapshots & Crash Recovery Protocol
- **Storage Subsystem Path**: `apps/web/src/canvas/storage/` provides zero-dependency, local-first persistence for DNK OS Canvas state.
- **Ring Buffer Invariant**: Constrains history transactions to `MAX_RING_BUFFER_SIZE = 100` entries per draft to prevent storage inflation.
- **Differential Snapshots (RFC 6902)**: Generates and applies forward/inverse JSON patch deltas with FNV-1a checksum validation.
- **Auto-Save & Window Lifecycle**: 5-minute background timer with dirty-flag checking and automatic `beforeunload`/`pagehide` flush hooks.
- **Crash Recovery (`recoverFromCrash`)**: Replays uncommitted transaction logs on top of base draft snapshots after ungraceful session exits.
- **Node.js Test Runner Execution**: Tested via `npx tsx --test apps/web/src/canvas/storage/storage.test.ts` using in-memory storage fallback adapters.
- **Reference**: See `references/indexeddb_storage_engine_and_ring_buffer.md`.

### 16. PWA Web Speech, MediaRecorder & Quality Gate Verification Protocol
- **Beyond 0 LSP Diagnostics Invariant**: `tsc --noEmit` is a baseline requirement, but Quality Gate acceptance strictly requires executing browser adapter unit tests, SSR isomorphic import validation, dynamic MIME negotiation (`MediaRecorder.isTypeSupported`), and IndexedDB graceful fallbacks.
- **Deterministic Recording Stop Sequence**: Enforce ordered STOP flow (`STOP_REQUESTED` ➔ `ASR_STOPPED` ➔ `MEDIA_STOPPED` ➔ `BLOB_FINALIZED` ➔ `SESSION_SAVED` ➔ `TRACKS_RELEASED` ➔ `SUMMARY_READY`) to prevent data corruption or track leak.
- **Evidence JSON & Handoff Certification**: Standardized generation of `docs/reports/evidence_<TASK_ID>.json` with commit hash, package versions, and test results alongside markdown handoff reports.
- **Reference**: See `references/pwa_web_speech_media_recorder_verification_protocol.md`.

### 17. Deterministic Multimedia Pipeline Orchestration & Isolation Protocol (VIDEO-AUDIT-PIPELINE-001A)
- **Isolation Principle (Foundation First)**: When building multimedia pipelines (video audits, speech transcription, OCR, scene extraction), never couple heavy external engines (WhisperX, FFmpeg, multimodal LLMs) directly into orchestration. Build the domain FSM, idempotency keys, retry/backoff policies, versioned DTO/events, and clean architecture ports first.
- **Finite State Machine & Atomic Leasing**: Pure state machine transitions (`queued` ➔ `leased` ➔ `running` ➔ `succeeded` / `retryable_error` / `permanent_error` / `cancelled`) with terminal state guards and automatic expired lease recovery (`reclaimExpiredLeases`).
- **Deterministic Idempotency & Backoff**: Idempotency key format `{referenceAssetId}:{jobType}:{inputVersion}:{processorVersion}` and exponential retry backoff schedule (`[5s, 30s, 2m, 10m]`) based on classified error types.
- **Deterministic Fake Worker Harness**: Validate entire pipeline lifecycle in Vitest with `DeterministicClock`, `DeterministicFakeWorker`, and in-memory repository/store/event-bus adapters prior to real engine integration.
- **Reference**: See `references/deterministic_multimedia_pipeline_orchestration.md`.

### 18. Secure Media Ingestion, Probe Validation & SSRF Isolation Protocol (VIDEO-AUDIT-PIPELINE-001B)
- **Sanitisation & Traversal Protection**: Sanitise file names via `sanitizeFilename` (strip null bytes, control chars, OS path separators). Store binaries in `ArtifactStore` by SHA-256 hash digest, never by user-supplied filename.
- **Header Sniffing**: Inspect binary magic bytes (`sniffMediaHeader`) for MP4 (`ftyp`), MOV, WebM, MKV signatures. Do NOT trust `Content-Type` headers or file extensions.
- **SSRF Hardening**: Validate remote media URLs (`validateUrlForSsrf` / `SsrfUrlValidator`) against loopback (`127.0.0.0/8`), RFC1918 private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud IMDS (`169.254.169.254`). Require `https:` protocol.
- **Deduplication & Idempotency**: Index `ReferenceAsset` by SHA-256 hash and Telegram `file_unique_id` / `update_id` to prevent duplicate binary storage or job submission.
- **Degraded Audio-less Mode**: Videos without audio streams (`hasAudio: false`) record `degradationWarnings` and proceed with visual-only audit jobs rather than hard-failing.
- **Reference**: See `references/secure_media_ingestion_and_ssrf_isolation.md`.

### 19. Swarm Model Configuration & Reasoning Effort Protocol
- Update model configurations globally in Hermes CLI (`hermes config set model.default gemini-3.8-flash`, `hermes config set model.reasoning_effort high`, `hermes config set delegation.model gemini-3.8-flash`, `hermes config set delegation.reasoning_effort high`).
- Programmatically sync model and reasoning effort parameters across all 14 swarm agent configs under `core/orchestrator/agents/*/config.yaml`.
- Update corresponding `SOUL.md` agent identities and Visual Shell model selector components (`DnkModelGcpQuickBar.tsx`).
- **Reference**: See `references/model_configuration_and_reasoning_effort.md`.

### 20. Transcription Adapter, WhisperX Layer & Ukrainian Speech Benchmark Protocol (VIDEO-AUDIT-PIPELINE-001C)
- **Canonical `transcript.v1` Contract**: Enforce strict Zod invariants (`startMs >= 0`, `endMs > startMs`, word ranges bounded by segment range, monotonic sorting, `durationMs` >= max timestamp, non-empty text for `completed` status).
- **Domain-Agnostic ASR Port**: Isolate ASR engines (`TranscriptionProviderPort`) from domain logic. Adapt WhisperX or other CLI drivers in infrastructure layer (`WhisperXTranscriptionAdapter`).
- **Error Mapping & Retryability**: Classify CUDA OOM / process crashes as `retryable_error`; classify corrupt audio / missing streams as `permanent_error`.
- **Deterministic Ukrainian Benchmarks**: Benchmark ASR accuracy using `DeterministicTranscriptionProvider` against Ukrainian ReBurn terminology (>= 90% technical terms recall, >= 95% word timestamp coverage, RTF calculation).
- **Reference**: See `references/transcription_adapter_and_whisperx_layer.md`.

### 21. Multimodal Analyzers, Scene/OCR/Audio Features & Partial Success Protocol (VIDEO-AUDIT-PIPELINE-001D)
- **Three Independent Analyzers**: Decompose video analysis into three parallel workers: `SceneExtractionWorker` (`scenes.v1`), `OCRWorker` (`ocr.v1`), and `AudioFeatureWorker` (`audio-features.v1`). Avoid single monolithic "multimodal worker" due to distinct runtime dependencies, failure modes, and metrics.
- **Strict Domain Boundary (OCR vs Transcript)**: OCR represents visual text on screen (`0..1` normalized bounding boxes), whereas `transcript.v1` represents recognized speech ("what was said"). Never mix or overwrite speech text with OCR text.
- **Temporal Invariants & Bounding Boxes**: Enforce strict chronological bounds (`startMs >= 0`, `endMs > startMs`, monotonically sorted scenes without overlaps, `durationMs = endMs - startMs`). Bounding boxes MUST be normalized in `[0.0, 1.0]`.
- **Degraded Execution & Partial Success**: Missing audio track or single analyzer failure transitions job status to `partial_success` / `degraded` rather than terminating the entire pipeline.
- **Multimodal Evidence Aggregator**: `buildMultimodalEvidence` aggregates scenes, OCR, audio features, and transcript into synchronized time intervals for downstream LLM reasoning without modifying underlying documents.
- **Reference**: See `references/multimodal_analyzers_and_partial_success_protocol.md`.

### 22. Multimodal Audit & Claim Validation Protocol (VIDEO-AUDIT-PIPELINE-001E)
- **Strict Evidence Mapping**: Force any claim classified as `observed` to link explicitly to underlying sources (`transcriptWordIndexes`, `sceneIndexes`, `ocrFrameIds`, or `audioSegmentIndexes`).
- **Two-Pass Strategic Reasoning**: Decouple direct evidence synthesis (Pass 1) from high-level speculative marketing or retention hypotheses (Pass 2).
- **Graceful Warning Compilation**: Omit optional source components (`ocr.v1`, `audio-features.v1`) gracefully by capturing standard warnings, maintaining 100% partial-input runtime continuity.
- **Reference**: See `references/multimodal_audit_and_claim_validation_protocol.md`.

### 23. Deterministic Report Assembly, Consistency Checks & Persistence Protocol (VIDEO-AUDIT-PIPELINE-001E-D)
- **Deterministic Report Assembler**: Implemented in `VideoAuditReportAssembler` (`packages/video-audit-core/src/pipeline/application/report-assembler.ts`), unifying all upstream outputs (`transcript.v1`, `scenes.v1`, `ocr.v1`, `audio-features.v1`, `multimodal-evidence.v1`, `multimodal-audit.v1`).
- **Cryptographic & Reference Consistency**: Validate SHA-256 integrity hashes of each constituent artifact, match `referenceAssetId` cross-references, and verify that any evidence citation targets real visual/audio chunks.
- **Degraded Graceful Fallback**: Handle missing optional inputs (e.g. `ocr.v1`, `audio-features.v1`) gracefully by injecting defaults and logging structured warnings.
- **Idempotent Storage & Eventing**: Save immutable reports to `ArtifactStore` uniquely keyed by artifact content hashes, publishing `AuditReportCreated.v1` to the event bus strictly after persistence.
- **Reference**: See `references/report_assembly_and_artifact_persistence_protocol.md`.

### 24. Gerych Active Core & Multi-Tier System Kernels Topology
- **Three-Tier Kernel Architecture**: Explicitly differentiate between the active AI Intelligence Model (`gemini-3.8-flash` on Vertex AI), System Runtime Engines (`FastMCPKernel` in `core/kernel.py` binding `auth`, `canvas`, `hermes_runtime`, `swarm_orchestrator`, `accounting`), and Swarm Agent Profiles (`gerych_prime` active manager + 13 specialized workers).
- **Reference**: See `references/gerych_cores_and_system_kernels_architecture.md`.

### 25. ReBurn Fixtures, Semantic Calibration & Ukrainian Terminology Protocol (VIDEO-AUDIT-PIPELINE-001E-E)
- **11 Calibrated Scenarios**: Support 11 distinct promotional, educational, and border scenarios for smokehouse equipment e-commerce (ranging from product demos, talking-heads, to degraded audio-less or OCR-less videos).
- **Semantic Validation Invariants**: Rather than exact text assertions, enforce physical and business-driven rules (hook <= 3s, virality as hypothesized, traceability of observed claims to sources).
- **Ukrainian Terminology Benchmark**: Verify correct identification and mapping of niche terms (*конденсатовідвідник*, *нагнітач*, *AISI 304*) with >= 80% recall.
- **Reference**: See `references/reburn_fixtures_and_calibration_protocol.md`.

### 26. Niche Adaptation Engine & SpendGuard-Guarded LLM Protocol (VIDEO-AUDIT-PIPELINE-001E-F)
- **Explicit Translation Mapping**: Decouple upstream `VideoAuditReport` structure from downstream extractor logic using explicit data mappers like `mapAuditReportToExtractionInput`.
- **Dynamic Chronological Timeline**: Proportionally calculate and split scene durations based on `targetDurationMs` to prevent validation errors (e.g. Zod `.refine(startMs <= endMs)`).
- **SpendGuard Core & LLM Resiliency**: Wrap LLM script generators in budget tracking `SpendGuard` structures, enforcing automated graceful fallbacks to deterministic local engines under budget depletion or network faults.
- **Stem/Prefix Lexical Matching**: Utilize root stems (e.g. `сертифік`) to capture complex grammatical inflections in highly inflected languages like Ukrainian.
- **Reference**: See `references/niche_adaptation_engine_and_spendguard_protocol.md`.

### 27. Canary Review, Secret Boundaries & Promotion Recommendation Protocol (Phase F)
- **Systematic Multi-Boundary Verification**: Programmatically assert five boundaries (Evidence Integrity, Secret Boundary, Shopify Policy Gate, Cost Accounting, and Rollback State) before any production promotion recommendation.
- **The 5-Sink Leak Prevention Rule**: Validate that raw sensitive tokens (e.g., Anthropic, Shopify PAT, GitHub tokens) are 100% absent in model payloads, stdout/stderr logs, event bus feeds, checkpoints, and SQL databases.
- **Real Policy Mutational Blocking**: Ensure Shopify write mutations (e.g., `dnk-e.myshopify.com`) are intercepted by the Policy Engine generating explicit write forbidden exceptions with 0 outbound network requests.
- **Cost Accounting Retry Invariant**: Map iterative failures as distinct attempts with `status: failed` to prevent double-counting of success tokens while capturing full monetary costs.
- **SLA Rollback & Evidence Isolation**: Maintain Rollback SLA under 30.0 seconds while isolating canary evidence, logs, and checkpoints from deletion.
- **Reference**: See `references/canary_review_and_secret_redaction_protocol.md`.

### 28. Task Forest & gastownhall/beads (bd) Distributed Graph Coordination Protocol
- **Ontological Alignment**: Map 5-plant Task Forest taxonomy to Beads graph primitives (`Tree` ⟷ Epic `bd-xxx`, `Bush` ⟷ Task `bd-xxx.1`, `Flower` ⟷ Sub-task `bd-xxx.1.1`).
- **Atomic Worker Claims**: Swarm agents prevent race conditions and double-dispatch via atomic `bd update <flower_id> --claim --assignee <agent_name>`.
- **Topological Discovery**: Swarm dispatchers use `bd ready --json` to instantly surface unblocked atomic tasks ready for immediate execution.
- **Dolt Branching**: Leverage underlying Dolt database for zero-risk speculative execution branches (`dolt branch experiment/<feature>`) with instant rollbacks on test failure.
- **Reference**: See `references/task_forest_and_beads_coordination_protocol.md`.

### 29. Unified Canvas Canonical Architecture & Phase 3 Swarm Co-Pilot Protocol
- **MVP Convergence Milestone**: 4/4 MVP steps complete (Zustand SSOT, WhiteboardOverlay, StitchFloatingDock + MediaSidebar, PostgreSQL 16 hub_memory + Delta Sync + WebSocket + IndexedDB fallback queue).
- **Canonical Architecture Spec**: Detailed architecture and contracts defined in `docs/architecture/UNIFIED_CANVAS_CANONICAL_SPEC_V1.md`.
- **Phase 3 Swarm Co-Pilot Stack**: `CopilotToolbar.tsx` (Cmd+K contextual floating dock), `intentResolver.ts` (LLM-guided agent dispatch), `budgetGuard.ts` (token & cost safety controls), real-time token streaming, and reactive multi-node cascade (`propagateSwarm`).
- **Reference**: See `references/unified_canvas_canonical_architecture_and_phase3_spec.md`.

### 30. Uncommitted Git State Pre-Flight Invariant & Live LLM Test Gate
- **Zero Uncommitted Certification Rule**: Under no circumstances declare completion, announce phase certification (e.g. `001E-F-LIVE`), or generate final evidence if targeted package code or config has uncommitted git mutations.
- **Pre-Certification Git Status Verification**: Explicitly verify `git status --short <target_paths>` shows 0 untracked/modified files before running `generate_evidence.py`. Uncommitted code risks tests passing against stale builds while production files remain diverged.
- **Dedicated Live Script Configuration**: Packages with live LLM integrations must expose dedicated, explicit scripts in `package.json` (`"test:live": "vitest run tests/adaptation/adaptation-pipeline.test.ts"`) so live suites can be run deterministically with environment gates like `RUN_LIVE_LLM_TESTS=1`.
- **Reference**: See `references/live_llm_certification_and_git_hygiene_protocol.md`.

### 31. Zero-Waste Swarm Protocol v4.3.0 & Elimination of Multi-Agent Waste
- **Waste Elimination Invariants**: Eliminate Token/Context Waste (Context Diet 80-120 lines, no full repo dumps), Cycle/Guess Waste (Instant Self-Healing Distillation via `dnk_query_error_solutions` instead of blind iterative patching), Drift/Duplication Waste (SCONES RAG first, Two-Tier isolation between `DNK_HUB` and `DNKOS_APP`), Orphan/Zombie Waste (`process_guard.py` singletons), and Fabrication Waste (mandatory 100% Green `scripts/verify_all.sh` + signed `generate_evidence.py`).
- **TaskDNA First & SCONES First Invariants**: Before multi-step coding, run `dnk_decompose_task_dna(goal)`. Before researching or boilerplate generation, query `scones_get_memories(query=topic)`.
- **Role Invariant**: Swarm Manager decides & orchestrates, Builder implements, Researcher ast-scans, Auditor adversarially tests & breaks, Security protects boundaries, Finance accounts tokens & costs, Librarian catalogs.
- **Reference**: See `references/zero_waste_swarm_protocol_v4_3_0.md` and canonical specification `docs/architecture/DNK_ZERO_WASTE_SWARM_PROTOCOL_V4_3_0.md`.

### 32. E-Com Brand Launch Local Test Matrix & Acceptance Protocol
- **End-to-End Verification Pipeline**: Full ecosystem validation across 6 distinct stages: Launchpad Onboarding (4 starter nodes + SCONES Brand DNA), AI Co-Pilot (Cmd+K with Budget Guard ~$0.02 and streaming swarm propagation), Photo Studio (BiRefNet cutout + IC-Light relighting), Video Intelligence (Ukrainian ASR + Hook Score + claim verification), 9:16 Shorts Generation (Remotion template + phonk audio + Shopify Media API sync), and Persistence / Collaboration (PostgreSQL + IndexedDB hydration + WebSocket OCC delta sync 750ms).
- **Dependency Drift Guard Invariant**: Maintain Webpack resolve alias in `apps/web/next.config.mjs` (`'reactflow': '@xyflow/react'`) to prevent broken chunks or blank screen errors during canvas migration.
- **Reference**: See `references/ecom_brand_launch_local_test_matrix.md` and canonical test report `docs/reports/LOCAL_TEST_ECOM_BRAND_LAUNCH.md`.

### 33. Niche Adaptation Engine & Subsystem Resilience Protocol (VIDEO-AUDIT-PIPELINE-001E-F-R1)
- **Sidecar Caching**: Store references as `references/{referenceAssetId}/source/{sha256}.mp4` and `transcript/{provider}-{model}-{version}.{json,vtt,txt}` to avoid redundant ASR calls.
- **Multimodal Frame Deduplication**: Strip redundant frames across modes (`fast`, `balanced`, `deep`, `forensic`) before visual LLM analysis.
- **Deterministic Similarity Mode**: Isolate test fixtures via `deterministicSimilarityMode` while retaining genuine Jaccard and n-gram similarity in production.
- **Fail-Closed Guardrails**: Missing prosody or missing shotlist transitions status to `rejected`, never `manual_review`.
- **Speech Duration & Pacing**: Voiceover pacing normalized at 130 WPM with ±20–25% duration tolerance.
- **Dual Node/Python Monorepo Symlink**: Maintain `packages/video-audit-core` with `packages/video_audit_core -> video-audit-core` symlink for seamless Python/Node cross-resolution.
- **Reference**: See `references/niche_adaptation_certification_and_subsystem_resilience.md`.

### 34. Post-Task Knowledge Harvesting & Obsidian Archival Protocol
- **Proactive Harvesting Offer**: At the conclusion of every non-trivial task (complex bugfix, architectural decision, algorithmic design, or SOTA assimilation), Gerych Prime must proactively prompt the user to archive key decisions, rationale, and tradeoffs into the Obsidian Knowledge Base (`~/Documents/DNK_HUB My Notes/DNK_HUB My Notes` or canonical `./docs/notes/`).
- **5 Canonical Note Archetypes**: Structure records into `ARCH` (Architecture/Module), `ADR` (Architecture Decision Record), `SOTA` (External Tech Assimilation), `PLAYBOOK` (Testing & Runbooks), or `AGENT` (Agent Roles/Contracts).
- **Dual-Reader Principle & Graph Interlinking**:
  * Include YAML frontmatter (`title`, `tags`, `type`, `status`, `created`, `updated`, `repo_spec`).
  * Embed `DNK-MRH-HEADER` per `DNK-STD-0075` with relative paths (`./`, `../`) formatted as a muted HTML comment block (`<!-- --- DNK-MRH-HEADER --- ... --- END DNK-MRH-HEADER -->`), NEVER as `# --- DNK-MRH-HEADER ---`.
  * Connect to the Map of Content (`[[000 DNK HUB Index]]`) and link related notes (`[[...]]`) to prevent graph orphans.
- **Tier 4 Vault Retrieval & Task Forest Anti-Pollution**:
  * In `UnifiedMemoryBroker` or search tools, always use recursive globbing (`vault_path.rglob("*.md")`) to index subdirectories (`tasks_and_ideas/`, `02_Architecture/`).
  * Ensure test runners isolate generated test nodes into `tests/fixtures/` or temporary directories rather than polluting production `docs/notes/tasks_and_ideas/`.
- **References**: See `references/post_task_knowledge_harvesting_protocol.md` and `references/obsidian_vault_hygiene_and_memory_retrieval.md`.

### 35. DNK OS Infinite Node-Based Canvas & Multi-Domain System Blueprint (CapCut & Google Stitch Reference Architecture)
- **Aesthetic & Structural Benchmarks**: Combines Google Stitch (`stitch.withgoogle.com`) spatial canvas / live sandbox preview with CapCut AI Design (`capcut.com/ai-design`) multi-modal video/asset editing factory.
- **11 System Pillars Mapped**: User Soul (`core/user_soul.py`), Project Isolation (`core/workspace/`), 14-Agent Swarm (`core/swarm_engine.py`), Web & Media Generation (`LiveWebPreviewNode.tsx`, `RemotionPlayer.tsx`, `packages/video-audit-core/`), Scoped Task Injection (`core/dna_assimilation.py`), SCONES Memory Tiering (`core/scones_memory.py`), Social Media Video Audit (`packages/video-audit-core/`), Web/AST Research (`services/dnk_web_research/`), Shopify Theme AST (`services/dnk_shopify/`), Business Analytics & CRM (`apps/web/components/analytics/`), and Mind Mapping / Task Forest (`apps/web/components/canvas/`).
- **Canonical Architecture Note**: Synchronized with Obsidian Vault canonical note `002 DNK OS - Master System Architecture & Implementation Blueprint.md`.
- **Reference**: See `references/dnk_os_infinite_canvas_and_swarm_blueprint.md` and `references/dnk_os_subsystems_audit_and_verification_matrix.md`.

### 36. DNK OS Subsystems Audit & Verification Protocol
- **Zero-Guesswork Reality Auditing**: When auditing the 11 core subsystems of DNK OS, do not accept narrative claims or conceptual roadmaps. Always inspect concrete package manifests (`package.json`), AST parsing modules, test suites (`pytest`, `vitest`), and telemetry implementations.
- **Architectural Reality SSOT**:
  * Orchestrator: Custom Supervisor-Worker engine with sub-0.05s dispatch and Langfuse telemetry (rather than direct LangGraph StateGraph dependency).
  * Swarm Agents: Verified by >305 test suites across monorepo; external paid APIs segregated via mock fixtures in CI.
  * Spatial Canvas: Powered by `@xyflow/react` v12.11.2 with 25 custom node types, HTML5 drag-and-drop, and `.canvas` JSON compliance.
  * SCONES Memory: L1 Fast Inverted Index, L2 pgvector store, L3 RRF hybrid search with temporal recency decay ($\lambda=0.1$) and agentic sleep consolidation.
  * Video Audit: `@dnk/video-audit-core` with keyframe/hash deduplication (5-10x frame reduction) and Ukrainian speech benchmarks.
  * Shopify: Section AST and Liquid validation via `shopify_canvas_client.ts` and `dnk_shopify_validate_liquid`.
- **Reference**: See `references/dnk_os_subsystems_audit_and_verification_matrix.md`.

### 37. Phase 1 Canvas Swarm WebSocket Bridge & Real-Time Node Execution Protocol
- **Multiplex WebSocket Endpoints**: FastAPI endpoints (`/ws`, `/api/ws`, `/ws/swarm` in `apps/api/routers/swarm_ws.py` and `/ws/canvas/v3/{canvas_id}` in `apps/api/routers/canvas_v3_ws.py`) connect React Flow canvas nodes to the Swarm Engine.
- **Strict FSM Node Status Lifecycle**: Node executions map through `idle` ➔ `thinking` ➔ `running` ➔ `completed` (or `error`) via structured `TASK_STATUS` events.
- **Real-Time Log Streaming**: Emit `AGENT_LOG` events with level, message, and timestamp to populate `StitchAgentLog.tsx` in real time.
- **UserSoul Injection & Langfuse Tracing**: Automatically inject `UserSOUL` context into task payloads, generate unique trace IDs, and record metrics via `AccountingEngine.log_workflow_telemetry` (`duration_ms=int(duration_ms)`).
- **Import Resiliency**: Guard optional experimental flows (e.g. `core.flows.research_write_validate`) with `try...except (ImportError, ModuleNotFoundError)` to keep FastAPI router packages importing cleanly.
- **Reference**: See `references/canvas_swarm_websocket_bridge_protocol.md`.

### 38. Mind Map Canvas Nodes, Custom Edges & Spatial Toolbar Contract Protocol
- **5 Mind Map Primitives**: `MindMapIdeaNode` (💡), `MindMapGoalNode` (🎯), `MindMapTaskNode` (✅), `MindMapAgentNode` (🤖), and `MindMapEvidenceNode` (📎) built on top of `BaseMindMapNode` with 4-directional connection handles.
- **Custom Edges**: Directional execution (`DependencyEdge`), conceptual association (`RelationEdge`), and timeline progression (`MilestoneEdge`).
- **Dual-Casing Registration Invariant**: Register both PascalCase and camelCase keys in `CanvasEngine.tsx` (`nodeTypes` & `edgeTypes`) and `NodeRegistry.ts` (`NODE_REGISTRY_MAP`) for seamless React Flow resolution.
- **Dual-Mode Spatial Toolbar**: `StitchSpatialToolbar.tsx` provides quick-spawn buttons supporting both click-to-spawn (with non-stacking random spatial offsets) and HTML5 drag-and-drop (`application/reactflow`).
- **Automated Contract Test Gate**: Regression contract test `tests/canvas/test_mindmap_nodes_edges_contract.py` validating node/edge file presence, MRH headers, exports, and registration across canvas engines.
- **Reference**: See `references/mindmap_canvas_contract_and_spatial_toolbar.md`.

### 39. Auto-Task-Spec Generation & Natural Language Interceptor Protocol
- **Natural Query Interception**: When unstructured requests (e.g. "Герич, зроби аудит...") arrive, never execute blindly. `core/orchestrator/task_spec_generator.py` detects action verbs via `should_auto_spec(query)` while safely ignoring conversational chat and questions.
- **Micro-Slice Auto-Increment**: Automatically parses recent git commits via `get_next_slice_number()` to determine the active micro-slice ID (e.g. 13.1 -> 13.2).
- **Evidence Planner & Epistemic Taxonomy**: Embeds `core/orchestrator/evidence_planner.py` to classify claims (`OBSERVED`, `INFERRED`, `HYPOTHESIS`), generate probe commands (`du -sh`, `find`, `stat`, `pytest`), and enforce empirical verification before mutation.
- **Risk Gate & Safety Shields**: Leverages `core/orchestrator/risk_gate.py` to assess risk scores (HIGH/MEDIUM/LOW), require human approval for destructive operations (`rm -rf`, `drop`, `delete`), and automate pre-flight snapshot backups in `.hermes/backups/`.
- **GitHub SOTA Research**: Integrates `core/orchestrator/github_research.py` to detect GitHub repositories, audit licenses under the Two-Track protocol (TRACK_1_DIRECT vs TRACK_2_CLEAN_ROOM), and extract architecture patterns.
- **Mandatory Atomic Slice Specification**: Builds a full v2.5 Task Spec adhering to `docs/templates/GERYCH_TASK_TEMPLATE.md` with explicit budget constraints (≤ 25 tool calls), target files, DoD, and verification commands.
- **Hook & CLI Integration**: Integrates directly with `scripts/system/hermes_pre_tool_hook.py` (caching in session tracker) and CLI `./scripts/system/auto_task_spec.py`.
- **Zero-Touch Inception & Multi-Tier Persistence Gateway**: `save_task_spec` automatically mirrors the spec to 4 destinations: `.hermes/active_task_spec.md`, `docs/plans/TASK_ACTIVE.md`, `docs/plans/my_task/task_YYYYMMDD_<slug>.md`, and Obsidian `docs/notes/tasks_and_ideas/<slug>.md`. For Obsidian, strictly adheres to `[OBSIDIAN_MRH_HYGIENE]` (frontmatter on line 1, muted HTML comment for MRH header, and rich `[[wikilinks]]`).
- **Mentor & Human Intake Protocol**: See `references/chief_architect_mentor_and_human_task_intake_protocol.md` for Chief System Architect role definition, human-to-swarm idea intake, and pedagogical swarm explainer bridges.
- **Reference**: See `references/auto_task_spec_generation_and_mase_protocol.md`.

### 40. Unified Swarm Control Plane, DAG State Machine & Checkpointer Protocol (CONTROL-PLANE-001)
- **Consolidated Authority**: All swarm and task coordination is unified in `core/orchestrator/control_plane.py` (`SwarmControlPlane`), eliminating fragmented coordination across legacy scripts.
- **State Machine States**: Strict enum `NodeStatus` (`PENDING`, `SCHEDULED`, `RUNNING`, `COMPLETED`, `FAILED`, `PAUSED_APPROVAL`, `RETRYING`).
- **DAG Topological Schedulability & Cycle Guard**: Executes dependencies via DFS cycle detection (`has_cycle()`) and topological sorting.
- **Human-in-the-Loop Gates**: Tasks marked `requires_approval=True` transition into `PAUSED_APPROVAL` until unlocked via `grant_approval()`.
- **Fault-Tolerant Checkpointing**: Persistent `StateCheckpointer` records execution state and step outputs to JSON snapshots for instant recovery via `restore_checkpoint(run_id)`.
- **Sub-50ms RAG Skill Ingestion**: Set-intersection keyword retrieval (`inject_skills_rag`) matches agent queries against skill tags and frontmatter with sub-50ms latency.
- **Reference**: See `references/unified_swarm_control_plane_and_engine_consolidation.md`.

### 41. Dynamic Context Budgeting, Toolset Pruning & Context Window Tax Elimination Protocol (TAX-PRUNE-001)
- **Zero Context Window Tax (84–89% Token Reduction)**: Slashes upfront dead system overhead from 25,000 to 2,800–4,000 tokens per turn via 3 coordinated mechanisms:
  1. **Lazy Tool Schema Loading (`LazyToolLoader`)**: Defers injection of 60+ full JSON schemas; stores metadata in memory and hydrates full schemas on demand (`load_schema`).
  2. **Tool Aliases & Summaries (`ToolAliases`)**: Injects ultra-compact signatures (`alias(args): summary`) into the system context (~350–500 tokens instead of 17,500). Resolves short aliases (`sh`, `shopify.validate_liquid`, `video.generate`) and domain toolsets back to canonical schemas.
  3. **Adaptive System Prompt Pruning (`AdaptivePromptEngine`)**: Dynamically selects prompt tiers based on task complexity score: `SIMPLE` (≤3), `MEDIUM` (4–8), or `COMPLEX` (>8) with MASE tool budget enforcement.
  4. **MCP Slim Guard 3 Meta-Tools Pattern (`MCPSlimGuard`)**: Replaces upfront registration of 60+ schemas with 3 lightweight meta-tools (`find_tool`, `call_tool`, `read_result`), consuming only ~290 tokens (98.3% savings vs 17,500). Employs two-tier search (MiniLM vector search + zero-dependency lexical overlap fallback), on-the-fly `jsonschema` parameter validation, and sidecar storage (`/tmp/dnk_sidecar/sidecar-{uuid}.txt`) for paginated reads (`read_result`) of outputs exceeding token thresholds, ensuring 0% context overflow on 8k/16k models.
- **Domain-Aware Triage Gating**: Step 0 triage (`core/orchestrator/task_triage.py`) computes `enabled_toolsets`, `disabled_toolsets`, `prompt_tier`, and `token_savings_pct`.
- **Orchestrator vs Worker Tool Isolation**: Prime operates with lightweight `CORE_TOOLSETS` + delegation tools; domain-specific schemas belong exclusively to isolated workers.
- **Verification Benchmark**: Measured via `python3 scripts/system/measure_context_tokens.py` verifying 88%+ token savings and <4,000 total tokens.
- **Reference**: See `references/dynamic_context_budgeting_and_toolset_pruning.md`, `references/mcp_slim_guard_meta_tools_protocol.md`, and `sota-repository-assimilation` reference `references/sota_context_management_and_compression_patterns.md` (Hermes LCM, Continuous Claude, MCP Slim Guard, GCC, CodeGraph-Rust).

### 42. Critical Security Guards, Epistemic Validation & Path-Traversal-Proof Snapshots (SEC-GATE-001)
- **Zero Shell-Injection Invariant**: All subprocess execution MUST pass argument lists (`shell=False`). Commands parsed from strings MUST use `shlex.split()`.
- **Epistemic Validation (`verify_evidence`)**: Any non-zero exit code (`exit_code != 0`) strictly fails verification (`verified = False`). Evaluates criteria (`exit_code_0`, `NON_EMPTY`, `> N`, `contains:...`).
- **Path Traversal & Symlink Exploit Defense**: All snapshot backups/restores must reject symlinks (`src.is_symlink() -> skip`) and verify `path.resolve().relative_to(root_dir)`.
- **Collision-Proof Backup Hashing**: Backups must store paths hashed with `hashlib.sha256(rel_path.encode()).hexdigest()[:8]_{filename}` mapped in `snapshot_manifest.json`.
- **Honest Fallback Invariant**: Research engines fallback to honest zero-states (`stars: 0`, `last_commit: "UNKNOWN"`, `fallback_used: True`) rather than hallucinated/mock metrics.
- **Reference**: See `references/critical_security_guards_and_evidence_verification_protocol.md`.

### 43. System Workspace Audit, L1 Memory Buffer Management & Git Hygiene Protocol (SYS-AUDIT-001)
- **Git Hygiene Guard (GIT-HYGIENE-001)**: Prevent orphaned test suites and unindexed router drift. Run `./.venv/bin/python3 scripts/system/git_hygiene_guard.py` before staging commits to ensure no `??` files exist in `tests/**`, `core/tests/**`, or `apps/api/routers/**`.
- **L1 Fast Memory Cap Management**: `MEMORY.md` is strictly limited to 2,200 chars. Prune duplicate swarm instructions already in `SOUL.md`/`AGENTS.md` via single atomic `memory(operations=[...])` calls to maintain ~30-40% capacity (<1000 chars).
- **Segmented Domain Commits**: Never lump 50+ mixed files into a single monolithic commit. Group by domain (`infra`, `core`, `canvas`, `assimilation`, `system/telemetry`), run targeted pytest suites, and commit each slice cleanly.
- **Background Daemon Terminate-Before-Commit**: Headless metric loggers (e.g. `collect_metrics.py`) continuously modify staging files. Always check `ps aux | grep collect_metrics`, terminate active PIDs, and finalize logs before concluding git hygiene.
- **Toolchain Invariant**: Always execute via `./.venv/bin/python3` and `./.venv/bin/pytest` with `PYTHONPATH="$HUB_ROOT:$HUB_ROOT/services"`.
- **Reference**: See `references/system_audit_git_hygiene_and_memory_buffer_protocol.md`.

### 44. Conversational Task Intake & CapCut/Stitch Visual Cabinet Protocol (INTAKE-STITCH-001)
- **Conversational Task & Idea Ingestion**: Transform natural language prompts in Ukrainian/English directly into DAG nodes (`idea`, `task`, `epic`, `gate`) via `ConversationalTaskExtractor` (`services/dnk_node_tasks/conversational_intake.py`) and `POST /api/v3/node_tasks/chat_intake`.
- **Swarm Agent Auto-Routing & Decomposition**: Automated routing to specialized swarm workers (`dnk_video_ai_creator`, `dnk_shopify`, `dnk_dev_fullstack`, `gerych_auditor`) with dynamic dependency link (`depends_on`) generation.
- **CapCut & Google Stitch UI Integration**: Floating Command Dock (`GerychTaskPromptDock.tsx`) with quick chips and Slide-out Chat Drawer (`GerychTaskChatDrawer.tsx`) rendered on the task canvas.
- **Reference**: See `references/conversational_task_intake_and_capcut_stitch_protocol.md`.

### 45. MCP Slim Guard Meta-Tools & Sidecar Offloading Protocol (SLIM-MCP-001)
- **Context Window Tax Elimination (98.3% Reduction)**: Replace static upfront registration of 60+ tool schemas (~17,500 tokens) with 3 dynamic meta-tools: `find_tool(query, tags)`, `call_tool(tool_name, arguments)`, and `read_result(ref, chunk_size, offset)` (~290 tokens).
- **Two-Tier Semantic Discovery**: `ToolSemanticIndex` pairs dense vector cosine search (`all-MiniLM-L6-v2`) with automatic tokenized/lexical Jaccard fallback when ML libraries are unavailable.
- **Sidecar Disk Buffer for Large Payloads**: Execution outputs exceeding 3,000 characters are automatically diverted to `/tmp/dnk_sidecar/sidecar-<ref>.txt`. Returns a summary preview + `result_ref`, consumed iteratively via `read_result` to prevent context explosion.
- **Reference**: See `references/mcp_slim_guard_meta_tools_protocol.md`.

### 46. Git-like Context Branching & Speculative Context Isolation (BRANCH-CTX-001)
- **Problem & Zero-Waste Law**: Speculative architectural exploration, test debugging, or hypothesis prompting can generate 30k–50k tokens of dead-end context. Leaving these in the primary conversation triggers premature context compaction (64k compression) and degrades agent steering.
- **GitContextController Lifecycle**:
  - `create_branch(name, from_branch="main", copy_parent_messages=False, checkout=True)`: Isolates speculative sub-routines on a detached branch with 0 baseline tokens.
  - `commit_branch(branch_id, message)`: Creates structured checkpoints of the branch state.
  - `merge_branch(branch_id, success=True)`: Condenses successful exploration findings into a concise summary (≤500 tokens) merged into `main`, dropping raw scratchpad traces.
  - `discard_branch(branch_id)`: Completely purges failed speculative iterations, ensuring **0 tokens** leak into `main`.
- **Triage & Slim Guard Integration**: `task_triage.py` flags speculative prompts (`is_isolated=True`), while `mcp_slim_guard.py` logs tool outputs directly to the active isolated branch.
- **Reference**: See `references/git_context_branching_and_isolation_protocol.md`.

### 47. Session Sentinel Watchdog & Hardened Self-Healing Loop Protocol (SENTINEL-SOUP-001)
- **Problem & Objective**: Unmonitored multi-agent sessions can silently fall into degenerative execution traps: tool argument loops (`read_file` thrashing), unverified task completion claims (false compliance), semantic error repetition without distillation, budget breaches (>25 actions/turn), or orphaned sessions when terminal crashes or disconnects.
- **Soup-Assimilated Resilience Engine (v2.0)**:
  - `SessionSentinel`: Background watcher (`scripts/system/session_sentinel.py --watch <PID>`) and CLI auditor (`--audit-latest`, `--reconcile-orphaned`) parsing session messages directly from `~/.hermes/state.db`.
  - **In-Flight Live Trajectory Polling**: Daemon periodically polls message increments (`poll_in_flight_trajectory`) and writes live anomaly alerts directly to `data/sentinel_alerts.json`.
  - **False-Compliance Guard (`FALSE_COMPLIANCE`)**: Intercepts narrative claims of success ("all tests pass", "100% green", "fixed") when no empirical verification tool (`pytest`, `verify_all.sh`, `terminal`) was executed in the session trajectory.
  - **Semantic Error Distillation Loop (`SEMANTIC_ERROR_LOOP`)**: Catches repeated exceptions/tracebacks without calling self-healing memory (`dnk_query_error_solutions`), preventing tool budget burnout.
  - **AST Fast-Path & Anti-Search-Loop Interceptor (`EXPLORATORY_NAV_WASTE`)**: Pre-tool hook redirects regex code definition lookups to `dnk_resolve_symbol` (<20ms AST index) and blocks repeated `search_files` (>=4) without action.
  - **Unverified Rewrite Churn & MASE Hard-Budget Stop**: Blocks repeated edits of the same file (>=2 patches) without testing; stops all exploratory actions at >=30 calls to force test execution and commit.
  - **Orphaned Sessions Reconciler (`--reconcile-orphaned`)**: Identifies dead-PID sessions via `os.kill(pid, 0)`, atomically marks completion, and synthesizes post-mortem incident specs.
  - **Crash-Resilient Persistence (MitigationLogWriter)**: Atomic writes (`atomic_write`) via `.{name}.tmp.{pid}_{ts}` and `os.replace` preventing corrupt state during unexpected terminations.
  - **Automated Self-Healing Hand-off**: Automatically generates canonical `TASK-DNK-SELFHEAL-*.md` specifications and registers DAG execution nodes on the Spatial Canvas for worker `dnk_dev_fullstack`.
  - **Intelligent Anomaly Role Routing**: Routes test, verification, false compliance, and auth/gate errors to `gerych_auditor`; routes code, syntax, and runtime exceptions to `dnk_dev_fullstack`.
  - **SCONES Distilled Remedy Injection**: Queries `docs/scones/error_distillations.json` via `lookup_scones_remedy`. When a verified pattern matches, the exact solution is directly injected into the self-healing task spec and worker parameters (`scones_remedy`), allowing 1-click execution.
  - **Auto-Dispatch Closed Loop**: Automatically dispatches remediation subagents via `dnk_swarm_dispatch` when anomaly severity is `CRITICAL` or `DNK_SENTINEL_AUTO_DISPATCH=1` is set, eliminating human stall time.
- **Reference**: See `references/session_sentinel_and_loop_hardening_protocol.md`.

### 48. Swarm Health Dashboard & Multi-Priority Unified Observability Protocol (HEALTH-DASH-001)
- **Problem & Objective**: Disparate swarm telemetry (worker readiness, Sentinel watchdog anomalies, SpendGuard token budgets, and Canvas WebSocket bridge traffic) previously required inspecting multiple isolated modules and CLI logs.
- **Unified Architectural Priorities**:
  1. **Priority 1 (Reactive FileWatcher)**: Push-based WebSocket notifications (`CANVAS_FILE_MUTATED`) via `watchdog` instead of client polling.
  2. **Priority 2 (OCC 3-Way Merge Engine)**: 3-way structural graph merging protecting against concurrent canvas overwrite collisions.
  3. **Priority 3 (Live Swarm HUD & Popover)**: Real-time agent status streaming (`SWARM_STATUS_UPDATE`) with color badges for all 14 specialized workers (`SWARM_WORKER_COLORS`) and interactive Canvas HUD Pill (`SwarmHealthWidget.tsx`).
  4. **Priority 4 (Swarm Health Dashboard)**: Canonical `SwarmHealthEngine` (`core/orchestrator/swarm_health.py`) providing unified REST (`/api/v1/health/swarm`) and WebSocket stream (`/api/v1/health/swarm/ws`).
  5. **Priority 5 (Concurrency-Safe Atomic Store)**: Multi-worker JSON telemetry and canvas storage protected by POSIX `fcntl.flock` locks, temporary file swap, and atomic `os.replace` (`core/atomic_store.py`).
  6. **Priority 6 (Active Swarm Auto-Healing)**: Transition from passive alerting to active remediation via `POST /api/v1/health/swarm/heal` and WebSocket `heal` action, archiving resolved anomalies.
  7. **Priority 7 (Resilient Client Streaming)**: Resilient WebSocket bridge client with exponential backoff (1.5s -> 10s) and in-memory outgoing event queuing during network interruptions (`apps/web/lib/api/canvas_bridge_client.ts`).
- **Core Diagnostics**:
  - `workers`: 14 workers with hex/canvas colors, status, and capabilities.
  - `sentinel`: Active alerts, severity distribution, and pending self-healing task specs.
  - `accounting`: Token burn, cost in USD, and SpendGuard saturation percentage.
  - `canvas_bridge`: Active client connections and broadcast event counts.
  - `system_resources`: Memory RSS (MB), CPU %, and uptime.
  - `overall_status`: Auto-calculated `healthy` / `degraded` / `unhealthy` state.
- **Reference**: See `references/swarm_health_dashboard_and_multi_priority_architecture.md`.

### 49. Git Worktree Isolation, NDJSON Audit Trail & Sangha Consensus Protocol (WORKTREE-AUDIT-001)
- **Problem**: Parallel coding subagents running directly in `$HUB_ROOT` risk concurrent file overwrite races and unverified destructive edits.
- **Core Pillars (`SwarmWorktreeManager` in `core/orchestrator/swarm_worktree.py`)**:
  1. **Git Worktree Isolation**: Spawns subagents in `.worktrees/<task_id>` on temporary branches `swarm/<agent>/<task_id>`. Subprocess cwd is scoped strictly to worktree root.
  2. **Append-Only NDJSON Audit Stream**: Structured events in `data/swarm_artifacts/audit_trail.ndjson` (`SWARM_WORKTREE_CREATED`, `SWARM_SANGHA_CONSENSUS_AUDIT`, `SWARM_WORKTREE_MERGED`, etc.).
  3. **Sangha Consensus Review Gate**: Multi-stage pre-merge gate (`evaluate_sangha_consensus`) enforcing Python syntax checks (`py_compile`), strict path hygiene (rejecting `/Users/...`, `/home/...`), and adversarial approval. Blocks dirty merges on failure.
- **Reference**: See `references/agent_swarm_benchmarks_and_ledger_worktree_patterns.md`.

## ⚠️ Pitfalls & Launcher Troubleshooting

### 1. Hermes CLI Argument Stripping
- **Symptom**: `hermes: error: argument command: invalid choice: 'gerych_prime'`
- **Cause**: Wrapper scripts (`gerych.sh`, `gerych_swarm.sh`) passing launcher flags like `--agent gerych_prime` directly down to `hermes`.
- **Fix**: Parse and strip `--agent <name>` inside `gerych.sh` (exporting `HERMES_AGENT_NAME` / `TARGET_AGENT`) before executing `python3 ./hermes "$@"`.

### 2. Pre-Flight Script String Splitting (`NameError` under `set -e`)
- **Symptom**: Launcher terminates abruptly right after printing the briefing card with zero Hermes execution.
- **Cause**: `NameError: name 'parts' is not defined` inside `preflight_sync.py` when parsing `.env` lines without calling `line.split("=", 1)` first.
- **Fix**: Ensure string splitting (`parts = line.split("=", 1)`) is executed before checking `len(parts)`.

### 3. Interrupted Session Continuity & Session Search Invariant
- **Symptom**: Calling `session_search(session_id=..., around_message_id=1)` fails with `around_message_id 1 not in session_id ...`.
- **Cause**: `session_search` uses absolute database message IDs rather than 1-based relative turn indexes.
- **Fix**: When resuming an interrupted session, always run `session_search(query="<task keywords>", detail="full")` to fetch `match_message_id`, `bookend_start`, and `bookend_end`, or dump the session via `session_search(session_id=id)` without `around_message_id`.

### 4. Evidence & Audit Manifest Absolute Path Sanitization Invariant
- **Symptom**: `scripts/verify_all.sh` fails at Step 2 (`core/playbooks/scripts/enforce_relative_paths.py`) reporting absolute path violations in `docs/audit/*-evidence.json` or `docs/reports/*_handoff.md`.
- **Cause**: Automated evidence generators, canary runners, or execution manifests serializing raw `/Users/<username>/...` absolute paths.
- **Fix**: All generated audit manifests and handoff documents MUST replace absolute paths with relative repo paths (`./`, `../`) or home shortcuts (`~/.hermes`). Run `python3 -c "from core.playbooks.scripts.enforce_relative_paths import audit_relative_paths; assert audit_relative_paths() == 0"` before executing `verify_all.sh`.

### 5. Subprocess Python Temporary Files Path Resolution Invariant
- **Symptom**: Subprocesses or canary integration tests crash with `python: can't open file 'tmp...py': [Errno 2] No such file or directory` even when `delete=False` is set.
- **Cause**: `tempfile.NamedTemporaryFile("w", delete=False, dir=".")` generates relative file paths (`./tmp...py`). When `subprocess.Popen` executes under custom environment arrays (`self.env` altering `PYTHONPATH` or `PWD`), relative path lookups from the spawning interpreter can mismatch the subprocess resolution.
- **Fix**: Always enforce absolute paths on temporary files before handing them to subprocess launchers by wrapping the output in `os.path.abspath(sf.name)`.

### 6. Next.js Blank Screen (FOUC `display: none` / Corrupted Webpack Chunks)
- **Symptom**: Browser opens `http://localhost:3000` and displays a solid, completely blank white page with no error overlay.
- **Cause**: Next.js hides unstyled content during SSR errors by injecting `<style data-next-hide-fouc="true">body{display:none}</style>`. If a background reload or webpack compilation gets interrupted, missing chunk files (e.g., `Cannot find module './682.js'`) or missing NPM dependencies (like legacy `reactflow` being replaced by modern `@xyflow/react` but still imported in some components) cause compilation failures, showing a blank screen with a webpack runtime error.
- **Fix**: 
  1. Direct probe with `curl -sI http://localhost:3000` to inspect status.
  2. Kill stale processes on the port (`lsof -ti :3000 | xargs kill -9`), clear the corrupted build cache (`rm -rf apps/web/.next`), and restart cleanly (`npm run dev`).
  3. **High-Velocity Zero-Install Fix for Dependency Drift (e.g. `reactflow` ➔ `@xyflow/react`)**: If `reactflow` is missing and cannot be installed due to CLI environments blocking `npm install`, add a Webpack alias in `next.config.mjs` resolving `'reactflow'` to `'@xyflow/react'`:
     ```javascript
     config.resolve.alias = {
       ...config.resolve.alias,
       'reactflow': '@xyflow/react',
     };
     ```
     This maps legacy imports to the modern runtime instantly with zero dependency overhead.

### 7. Cross-Virtualenv Subprocess Environment Scrubbing (`__PYVENV_LAUNCHER__`)
- **Symptom**: Tests running under one Python version/venv (e.g. root Python 3.14 `.venv`) spawn subprocesses targeting a different Python binary/venv (e.g. Python 3.12 staging `.venv`), which immediately crash or fail to import standard libraries.
- **Cause**: macOS/Unix Python launchers inject `__PYVENV_LAUNCHER__` and `PYTHONHOME` into environment variables, which leak into child subprocesses when using `os.environ.copy()`.
- **Fix**: Scrub launcher variables before spawning:
  ```python
  env = os.environ.copy()
  env.pop("__PYVENV_LAUNCHER__", None)
  env.pop("PYTHONHOME", None)
  ```

### 8. Nested CWD Tool Path Resolution Mismatch (File Mutation Verification Failure)
- **Symptom**: `⚠️ File-mutation verifier: 1 file(s) were NOT modified this turn` and `[patch] Failed to read file: <workspace_root>/core/hermes_agent/<path>`.
- **Cause**: The active Hermes session CWD is nested (e.g. `core/hermes_agent`), but tool arguments assume the monorepo root (`$HUB_ROOT`).
- **Fix**: Follow the 5-step diagnostic checklist in `references/live_llm_certification_and_git_hygiene_protocol.md` (check `ls -la`, symlinks, `git status`, `cat`, and `git show HEAD --stat`). Differentiate between **Scenario A (False Positive)** where the working tree is clean and committed vs **Scenario B (Real Issue)** where changes are uncommitted. Prefix relative paths with `../../` if operating from nested directories.

### 9. Uncommitted Changes & Premature Certification Gate Failure
- **Symptom**: Evidence JSON generated and phase gate declared passed, but system verifier or auditor detects uncommitted changes or missing files in the git tree.
- **Cause**: Editing files in memory or failing to commit them before running `generate_evidence.py` and announcing certification.
- **Fix**: Invariant: never certify without `git status` clean check. Always run `git status --short <target_paths>` and verify working tree is clean. Any uncommitted code renders certification invalid.

### 10. TUI Banner Version Drift & Emoji VS16 Border Desync
- **Symptom 1 (Version Drift)**: Startup banner displays an outdated version or release date (e.g. `Hermes v0.20.5 (2026.8.19)` instead of `v0.21.0 (2026.8.31)`).
- **Cause 1**: The banner header string (`Gerych (DNK OS) · Hermes v...`) resolves from `hermes_cli.__version__` and `hermes_cli.__release_date__` defined in `core/hermes_agent/hermes_cli/__init__.py` and `pyproject.toml`.
- **Fix 1**: Ensure runtime version upgrades update both `core/hermes_agent/hermes_cli/__init__.py` and `core/hermes_agent/pyproject.toml`.
- **Symptom 2 (Border Desync / Broken Right Edge)**: The right border column (`│`) on specific lines in the Rich panel is offset or missing (black void), especially on lines with emojis like `🛠️ Доступні інструменти`.
- **Cause 2**: Emoji containing Variation Selector 16 (`\ufe0f`, e.g. `\u1f6e0\ufe0f`) or ambiguous East Asian Width causes a cell-count mismatch between Rich (`cell_len`) and terminal emulators, leading to extra terminal cursor advances and broken borders.
- **Fix 2**: Replace composite VS16 emojis with canonical, naturally Wide (`W`) single-codepoint emojis (e.g. use `🔧` U+1F527 instead of `🛠️` U+1F6E0+FE0F). Verify with `python3 scripts/system/ensure_dnk_tui_integrity.py`.

### 11. Pre-Tool Hook Circuit Breaker & Anti-Bypass Guardrail
- **Symptom**: Calling `read_file` fails with `⚠️ DNK OS Circuit Breaker: You have read '<path>' 3 times in a row. The content is already in context.` or `patch`/`write_file` fails with `❌ BLOCKED by DNK OS Circuit Breaker: You have modified '<path>' 2 times consecutively without testing.`
- **Cause**: `scripts/system/hermes_pre_tool_hook.py` tracks history in `/tmp/hermes_loop_tracker_<session_id>.json` to stop repetitive read/patch churn without verification. Furthermore, section 5 of the hook blocks attempts to bypass the read lock via `terminal`/`execute_code` with `cat`, `head`, `tail`, or `open()`.
- **Fix**: Never try to circumvent the circuit breaker by executing shell reading commands. When blocked:
  1. The content is already in the conversation context — proceed directly to authoring your patch or code.
  2. Run verification/tests (`pytest`, `verify_all.sh`) via `terminal` — executing a real test resets consecutive patch tracking.
  3. If tests or linters fail, immediately query `dnk_query_error_solutions` instead of making blind repeated patches to the same file.

### 12. Flaky Subprocess Spawn Latency in Canary / Integration Tests
- **Symptom**: Integration tests asserting lock/checkpoint creation in spawned Python subprocesses fail with `AssertionError: Lock file was not created!`.
- **Cause**: Hardcoded static `time.sleep(0.2)` is insufficient during interpreter startup and disk writes under system load.
- **Fix**: Replace static sleeps with a bounded polling loop (up to 3.0s with 50ms intervals) checking `os.path.exists()`.

### 13. Path Hygiene False Positives on Version Archives & Staging Trees
- **Symptom**: Step 2 of `scripts/verify_all.sh` (`enforce_relative_paths.py`) reports absolute path violations in archived version snapshots or staging directories.
- **Cause**: Path hygiene scanners recursively analyzing non-production archive/staging directories not present in the ignore list.
- **Fix**: Synchronize `ignored_dirs` in `core/playbooks/scripts/enforce_relative_paths.py` and `tests/verification/test_path_hygiene.py` to include `"core/hermes_versions"`, `"core/hermes_agent_staging"`, `"cache"`, `"sessions"`, `"checkpoints"`, and `"docs/audit"`.

### 14. Asyncio Event Loop Re-entrancy & Thread-Safe Queue Put Trap
- **Symptom**: Test runner or server hangs indefinitely / times out during cross-thread or cross-loop event bus dispatch.
- **Cause**: In event dispatchers (e.g. `RuntimeEventBus.publish`), defining a recursive helper `_enqueue` that evaluates `if curr_loop is not q_loop: q_loop.call_soon_threadsafe(_enqueue)` inside `_enqueue`. If `curr_loop` is closed over from the outer scope, `_enqueue` continuously reschedules itself on `q_loop` in an infinite recursion.
- **Fix**: Decouple the put action into a pure callable `_put()` that strictly executes `queue.put_nowait(event)` (with backpressure/overflow drops). In the outer scope, schedule `q_loop.call_soon_threadsafe(_put)` if running across different event loops, or execute `_put()` directly if loops match.

### 15. Swarm Tool Kwargs Hardening (`TypeError: unexpected keyword argument`)
- **Symptom**: Agent tool invocations fail with `TypeError: dnk_swarm_status() got an unexpected keyword argument 'task_id'` or `'swarm_id'`.
- **Cause**: Different subagents or LLM callers produce slightly different keyword names (`swarm_id` vs `task_id` vs `project_id`) when querying status or telemetry.
- **Fix**: Always accept `**kwargs: Any` in tool function signatures (`def dnk_swarm_status(swarm_id: Optional[str] = None, task_id: Optional[str] = None, **kwargs: Any)`) and declare both parameters in the tool schema to prevent rigid schema rejection.

### 16. Path Hygiene on Agent Identity & SOUL Files
- **Symptom**: `tests/verification/test_path_hygiene.py` fails during pre-commit checks due to absolute paths found in `core/orchestrator/agents/*/SOUL.md`.
- **Cause**: Specifying user home directory paths like `/Users/username/Documents/...` in agent memory or system prompts.
- **Fix**: Use tilde expansion (`~/Documents/...`) or relative paths (`./`, `../`) to maintain 100% path hygiene compliance across different developer workstations.

### 17. In-Memory Python Module Caching Trap (`sys.modules`) during Live Patching
- **Symptom**: Calling custom tools (e.g. `dnk_run_adversarial_review`) in a persistent daemon/harness continues failing with the exact same error even after patching the tool file on disk.
- **Cause**: Persistent Python processes cache imported modules in `sys.modules`. Modifying code on disk does not invalidate cached in-memory module bytecode.
- **Fix**: Either execute verification via fresh subprocesses (`python3 -c "from ... import ..."`) or explicitly call `importlib.reload(sys.modules[mod_name])` before retrying in the same process.

### 18. Unscoped AST Scans & Monorepo Vendor Code Pollution
- **Symptom**: Static code analysis or adversarial security scans (`review_target()`) generate thousands of false positive violations and time out.
- **Cause**: Passing broad top-level directories (`core/`) that include third-party frameworks, vendor agents (`core/hermes_agent`), or virtual environments.
- **Fix**: Scope scans to explicit modified component files (`apps/api/routers/...`, `core/runtime_events.py`) and enforce exclusions for `hermes_agent`, `node_modules`, and `.venv`.

### 19. Uncommitted Working Tree PR Deadlock
- **Symptom**: `generate_evidence.py` reports `Warning: N uncommitted changes` and `gh pr create` fails with `GraphQL: No commits between main and feature/<branch>`.
- **Cause**: Changes reside solely in the working directory as unstaged/untracked modifications without git commits on the feature branch.
- **Fix**: Before generating evidence or opening PRs, sanitize `.gitignore`, commit changes atomically via Conventional Commits, push to remote (`git push origin <branch>`), and verify `git status` is 100% clean. (See `references/adversarial_audit_and_uncommitted_release_hygiene.md`).

### 20. System Python vs .venv Virtual Environment Execution Trap
- **Symptom**: Running `python3 -c "..."` or bare `pytest` in terminal commands raises `ModuleNotFoundError: No module named 'starlette'` or similar workspace dependency errors.
- **Cause**: Host system Python (`/usr/bin/python3`) lacks project virtualenv dependencies installed under `$HUB_ROOT/.venv`.
- **Fix**: Always execute verification scripts and test commands using the project virtualenv prefix: `./.venv/bin/python` or `./.venv/bin/pytest`. (See `references/structured_logging_and_distributed_tracing_protocol.md`).

### 21. High-Concurrency TestClient Thread Safety & Server Daemon Hangs
- **Symptom**: Load and stress test runners deadlock indefinitely or report flaky socket connection errors / 429 Too Many Requests.
- **Cause**: Starlette `TestClient` is not thread-safe across concurrent threads in `ThreadPoolExecutor`; background daemon server threads (`uvicorn.Server.run()`) don't terminate cleanly; `SecurityMiddleware` blocks load tests.
- **Fix**: Use `threading.local()` for per-thread `TestClient` isolation, enforce watchdog timeouts / `os._exit(0)`, and set `TESTING=1` to bypass rate limits. When dispatching parallel worker tasks via `dnk_swarm_parallel`, always pass explicit `target_files: [...]`. (See `references/swarm_target_files_and_concurrency_watchdog.md`).

### 22. Full-Suite Multi-Threaded Regression Overhead & Benchmark RPS Jitter
- **Symptom**: Isolated throughput tests (e.g. `assert rps >= 500.0`) pass individually, but intermittently fail under `bash scripts/verify_all.sh` (e.g. `484.5 >= 500.0`).
- **Cause**: Test runner tracing overhead (`coverage`, `pytest-cov`), concurrent threads, and full 1600+ test suite resource pressure.
- **Fix**: Calibrate benchmark thresholds to check `sys.modules["coverage"]`, `COVERAGE_RUN`, or `VERIFY_ALL` environment indicators, allowing a reasonable overhead buffer (e.g. 350-450 RPS). Ensure pre-commit diff checks (`git diff --check`) are run after stripping trailing JSX whitespace. (See `references/user_onboarding_and_benchmark_jitter_hygiene.md`).

### 23. Agent Runtime Bloat, Git Symlink Invariants & Stateless Configuration Leak
- **Symptom**: Agent profile directories (`core/orchestrator/agents/*`) balloon with `state.db` (500+ MB), LSP language server caches, and checkpoint dumps. Adding `dir/` to `.gitignore` fails to ignore created symlinks (`dir` shows up in `git status` as untracked symlink `?? core/orchestrator/agents/.../cache`).
- **Cause**: Git ignores only real directories if a trailing slash `/` is specified (e.g. `path/dir/`); a symlink pointing to a directory is considered a link/file by git, not a directory!
- **Fix**: Specify both or omit the trailing slash in `.gitignore` (`core/orchestrator/agents/**/cache` and `core/orchestrator/agents/**/cache/`). Isolate ephemeral state to `~/.hermes/runtime/<agent>/` via startup wrapper (`scripts/system/gerych.sh`), ensuring agent directories in git remain 100% stateless declarative configuration (`SOUL.md`, `agent_card.yaml`, `skills/`). (See `references/stateless_agent_runtime_and_disk_hygiene.md`).

### 24. Checkpoint State Reconstitution & Fresh Control Plane Node Re-instantiation
- **Symptom**: When attempting to resume or inspect an interrupted DAG run using a fresh instance of `SwarmControlPlane` via `restore_checkpoint(run_id)`, execution fails with `KeyError` or crashes when looking up `self.nodes[node_id]`.
- **Cause**: Checkpointer writes JSON metadata and step results, but does not serialize arbitrary Python callable action objects across processes. If the fresh control plane hasn't registered the nodes yet, `self.nodes` is empty.
- **Fix**: In `restore_checkpoint()`, iterate over the checkpoint's saved node state and dynamically re-instantiate synthetic `TaskNode` objects with their original dependencies and statuses into `self.nodes` if not already present. Ensure action handlers gracefully accept both `(context)` and `(node, context)` signatures. (See `references/unified_swarm_control_plane_and_engine_consolidation.md`).

### 25. Shell Injection Vulnerability & Epistemic False Positives in Evidence Planning
- **Symptom**: Running evidence probes with `shell=True` allows unescaped shell metacharacters to inject arbitrary commands, while probes return `verified: True` even when subprocesses exit with non-zero error codes.
- **Cause**: Passing string commands directly to `subprocess.run(..., shell=True)` and assuming presence of output equals verification success without evaluating process return status.
- **Fix**: Strictly enforce `shell=False` across all execution modules, parse CLI strings using `shlex.split()`, validate command binaries via fallbacks (`.venv/bin/pytest` -> `which` -> `uv run`), and implement `verify_evidence(probe, output, exit_code)` requiring `exit_code == 0` for passing probes. (See `references/critical_security_guards_and_evidence_verification_protocol.md`).

### 26. Subtree Test Runner Directory Mirroring Invariant (`core/orchestrator/test_*.py` vs `tests/core/test_*.py`)
- **Symptom**: External test runners or automated directives execute commands targeting module subtrees directly (e.g. `pytest core/orchestrator/test_lazy_tool_loader.py -v`) while tests reside canonically under `tests/core/test_*.py`, causing `fatal: pathspec did not match any files` or missing test suites.
- **Cause**: Structural differences between root `tests/` hierarchy and inline module test expectations specified in legacy directives or CI harnesses.
- **Fix**: Author lightweight mirror proxy runners in `core/orchestrator/test_<module>.py` containing `from tests.core.test_<module> import *` with valid MRH headers. This provides zero-cost dual-path test execution without duplicating test logic.

### 27. Pytest Basename Collision & Importlib Mode Invariant (`tests/core/test_*.py` vs `tests/verification/test_*.py`)
- **Symptom**: `bash scripts/verify_all.sh` or multi-directory test runs fail with `import file mismatch: imported module 'test_...' has this __file__ attribute ... which is not the same as the test file we want to collect` (exit code 2).
- **Cause**: Pytest default import mode (`prepend`) keys modules solely by their filename basename without prepending package paths. If identical test basenames exist across subdirectories (e.g. `tests/core/test_knowledge_base_rag.py` and `tests/verification/test_knowledge_base_rag.py`), module collision occurs during collection.
- **Fix**: Ensure `pyproject.toml` configures `addopts = ["--import-mode=importlib"]` under `[tool.pytest.ini_options]`. This isolates test module imports per path using Python's `importlib`, resolving name collisions across disparate test suites without requiring file renames.

### 28. Background Daemon Metric Logger Git Tree Pollution
- **Symptom**: `git status` repeatedly shows unstaged modifications in `docs/performance/metrics_staging_*.csv` or runtime logs immediately after running `git commit`.
- **Cause**: Background daemon processes (`collect_metrics.py` or polling threads) are still running in the background and continuously flushing to disk.
- **Fix**: Inspect active background Python processes with `ps aux | grep -E "collect_metrics|monitor"`, kill the offending PIDs (`kill <pid>`), and commit the final quiescent file state.

### 29. L1 Fast Memory Buffer Overflow (2,200 Character Cap)
- **Symptom**: Calling `memory(action='add', content='...')` raises a runtime buffer overflow error (`104% full`, >2,200 chars).
- **Cause**: Storing verbose procedural descriptions or duplicating agent roles in L1 memory.
- **Fix**: Perform an atomic batch operation via `memory(target='memory', operations=[...])` that consolidates memory entries into compact high-signal bullet points (<1,000 chars), freeing room for new operational invariants.

### 30. Containerized Broken Symlink to Obsidian Vault & FileExistsError Fallback
- **Symptom**: Calling `sync_to_obsidian()` inside a Docker container raises `FileExistsError: [Errno 17] File exists: 'docs/notes'`.
- **Cause**: `./docs/notes` is a symlink pointing to a host macOS path (e.g. `~/Documents/DNK_HUB My Notes/...`) that does not exist inside the isolated container filesystem. Calling `Path(dir).mkdir(parents=True, exist_ok=True)` treats the broken symlink as an existing non-directory.
- **Fix**: Trap `(FileExistsError, OSError)` on directory creation and gracefully fall back to an in-container safe directory (e.g. `./docs/local_notes/tasks_and_ideas` or `/tmp/obsidian_tasks_vault`), ensuring non-blocking execution while preserving file creation.

### 31. Pre-Tool Hook Loop Tracker Static Session ID Collision in Test Runners
- **Symptom**: Tests exercising pre-tool hooks or security interceptors fail with loop circuit breaker errors (`loop_circuit_breaker_triggered`) or consecutive read blocks.
- **Cause**: Hardcoded static session IDs (e.g. `session_id="test_vault_hygiene_1"`) persist file access counts in `/tmp/hermes_loop_tracker_<session_id>.json` across test runs, causing subsequent test executions or assertions to exceed the 3-read / repetition limit.
- **Fix**: Always generate a dynamic UUID session ID per test function or hook execution (e.g. `session_id = f"test_{uuid.uuid4().hex[:8]}"`) to ensure pristine state isolation across test suites.

### 32. Large Tool Execution Payload Context Overflow & Sidecar Threshold Desync
- **Symptom**: Agent context window balloons to 30k+ tokens during multi-file scans, code extraction, or deep git audits, causing 64k compression or tool turn budget exhaustion.
- **Cause**: Directly returning uncompressed raw text payloads (>3,000 chars) instead of routing execution through `call_tool` with sidecar storage interception.
- **Fix**: Always enforce `call_tool` payload interception for outputs >3k characters, emitting preview slices and disk-backed references (`/tmp/dnk_sidecar/`), and paginating via `read_result(ref, chunk_size, offset)`.

### 33. Speculative Prompt Bloat & Uncommitted Context Leakage
- **Symptom**: Exploring multiple architectural hypotheses or debugging complex test failures dumps tens of thousands of speculative prompt tokens into the primary conversation window, triggering premature 64k context compaction.
- **Cause**: Executing investigative experiments, alternative designs, or test retry loops on the default `main` context thread without branch isolation.
- **Fix**: Automatically fork speculative or exploratory tasks into a detached branch via `GitContextController.create_branch(name, copy_parent_messages=False)`. If the hypothesis fails, call `discard_branch()` to purge the scratchpad with **zero token leakage** into `main`. If successful, merge via `merge_branch()` which distills findings into a compact summary commit (≤500 tokens).

### 34. Markdown Planning Doc Absolute Path Audit Rejection
- **Symptom**: `bash scripts/verify_all.sh` (or `core/playbooks/scripts/enforce_relative_paths.py`) fails on Step 2/4 with `[Absolute Path Violation]` pointing to documentation, task plans, or error reproduction notes in `docs/plans/` or `docs/notes/`.
- **Cause**: Path hygiene linters scan all tracked files for `/Users/[a-zA-Z0-9_\\.]+/`. Writing literal user home paths in markdown text or problem descriptions triggers hard rejection.
- **Fix**: Never write literal `/Users/<user>/` paths in markdown plans or logs. Use relative `./` paths, `<HUB_ROOT>/`, or sanitize as `~/[REDACTED]/...`.

### 35. Untracked Test Suite & Staged Commit Amnesia (Git Hygiene Guard)
- **Symptom**: Feature code is committed to Git, but newly authored test files (`tests/core/test_*.py` or `tests/verification/test_*.py`) remain untracked in the working tree. Subsequent branch switches or CI runs fail with missing tests or dirty working tree errors.
- **Cause**: Selectively running `git add <file>` on modified source files while forgetting to index newly authored test files.
- **Fix**: Always verify `git status --porcelain` before completing a slice. If new tests were created to verify the code, they MUST be committed atomically alongside the code they test.

### 36. Frontend TypeScript Blind Spot & Missing `type-check` Script Invariant
- **Symptom**: Backend pytest suites pass 100% Green in `verify_all.sh` and pre-commit checks, but deployment or Next.js production builds fail with TypeScript syntax and type mismatch errors.
- **Cause**: Monorepo verification gates only executed pytest/AST/hygiene scans on Python services while omitting Next.js/TypeScript checks, especially when `apps/web/package.json` lacked an explicit `"type-check": "tsc --noEmit"` script.
- **Fix**: Always define `"type-check": "tsc --noEmit"` in `apps/web/package.json` and wire it directly into master gates (`scripts/verify_all.sh` Step 3.5 and `auto_precommit_guard.py` Check 5) so type errors fail fast before commits.

### 37. Untracked Nested Test Suites & Git Status Shallow Blindspot (-u flag)
- **Symptom**: Developers create new test suites in nested directories (e.g., `tests/stealth/test_adapter.py`), but `git_hygiene_guard.py` fails to flag them, or PRs/commits proceed without adding test files.
- **Cause**: Standard `git status --porcelain` without the `-u` flag groups untracked directories as single directory entries (`?? tests/stealth/`) rather than listing nested files individually, bypassing simple prefix matches like `line.endswith(".py")`.
- **Fix**: Always invoke `git status --porcelain -u` in pre-commit and hygiene checks to recurse into all untracked directories and detect untracked `.py` tests or routers.

- `38. MASE Turn Budget Circuit Breaker & Pre-Exhaustion Guard`
- `39. Ephemeral CWD Drift in Terminal Tool (Persistent Shell State Trap)`
- `40. Swarm Worker Scaffold Orphanage & Git Hygiene Blockers`
- **Symptom**: An agent enters a deep research or exploratory read loop, consuming 30–60 turns on a single sub-task and exhausting the 90/90 tool budget before writing code or running verification.
- **Cause**: Absence of an autonomous circuit breaker in the pre-tool hook allowing unconstrained iterations without intermediate commits or reports.
- **Fix**: Wire a turn counter into `hermes_pre_tool_hook.py`: issue a strong warning at turn 25, and physically block exploratory read/search calls at turn ≥28 until verification (`verify_all.sh`) is run and changes are committed. Store slice limits in agent configs (`max_turns_per_slice: 25`).

### 39. Ephemeral CWD Drift in Terminal Tool (Persistent Shell State Trap)
- **Symptom**: Subsequent `read_file`, `search_files`, or relative path commands fail with `File not found` or path resolution errors after executing an in-tree `cd` command (e.g. `cd apps/web && npm run type-check`).
- **Cause**: The `terminal` tool persists current working directory mutations across calls. Running `cd` shifts the session root away from `$HUB_ROOT`.
- **Fix**: Encapsulate directory changes in subshells `(cd apps/web && ...)` or use native CLI directory flags (`npm --prefix apps/web ...`). If CWD changes, return to root immediately in the same command. See `references/ephemeral_cwd_drift_and_swarm_hygiene.md`.

### 40. Swarm Worker Scaffold Orphanage & Git Hygiene Blockers
- **Symptom**: `scripts/system/git_hygiene_guard.py` or `scripts/verify_all.sh` fails with `❌ GIT HYGIENE ERROR: Found untracked test/router files!`.
- **Cause**: Swarm domain workers (e.g., `dnk_dev_fullstack`) generate endpoint routers (such as `apps/api/routers/rag.py`), schemas, or test stubs that remain untracked and unregistered in `apps/api/main.py`.
- **Fix**: Immediately after worker completion, either wire the router into `apps/api/main.py` with tests and stage via `git add`, or prune stale stubs before triggering quality gates. See `references/ephemeral_cwd_drift_and_swarm_hygiene.md`.

### 41. Git-Tracked Swarm Tool Placement & FastAPI Dependency Injection Invariants
- **Symptom**: Swarm tools placed in `core/hermes_agent/` disappear from git status or remain untracked due to `.gitignore`; or FastAPI test fixtures fail to mock backend services because routes invoke factory methods directly instead of `Depends()`.
- **Cause**:
  1. `core/hermes_agent/` is excluded from git in root `.gitignore`. Any persistent tools meant for the 14 Swarm workers must reside in `core/orchestrator/tools/` and register in `core/orchestrator/tool_aliases.py`.
  2. Directly instantiating adapters inside route functions (`adapter = get_rag_adapter()`) bypasses FastAPI's `app.dependency_overrides`, causing integration tests to hit real dependencies or fail.
- **Fix**:
  1. Place all native Swarm tools in `core/orchestrator/tools/<tool_name>.py` and bind their aliases in `core/orchestrator/tool_aliases.py`.
  2. In FastAPI routers, always inject adapters via `adapter: AdapterType = Depends(get_adapter)` to ensure 100% test isolation via `dependency_overrides`.

### 42. False-Compliance Verification & Sentinel Zombie Watchers
- **Symptom**: An agent generates narrative completion summaries claiming all unit tests pass, yet `scripts/verify_all.sh` was never executed; background sentinel watchers linger as orphaned zombies after terminal disconnection; or repeated identical exceptions trigger iterative guessing loops instead of error distillation.
- **Cause**:
  1. The agent falls into "declarative confirmation" without executing real validation tools, leading to broken downstream pipelines.
  2. Running `--watch <PID>` without checking for orphaned PPIDs or handling SIGTERM leaves stale sentinel processes polling non-existent sessions.
  3. Repetitive code-patching without consulting self-healing memory (`dnk_query_error_solutions`) exhausts tool call limits and causes context rot.
- **Fix**:
  1. Enforce Soup-inspired False-Compliance detection: fail the session gate if keywords like "Success/Completed/100% Green" appear without corresponding `terminal(pytest/verify_all.sh)` tool invocations.
  2. In `session_sentinel.py`, implement atomic PID polling (`os.kill(pid, 0)`) with `--reconcile-orphaned` to clean up dead sessions, and auto-terminate watch daemons on parent process exit.
  3. Detect semantic error loops (`SEMANTIC_ERROR_LOOP`) and mandate SCONES/Distiller querying on repeated tracebacks.
  4. Ensure crash-resilient persistence via `atomic_write` (MitigationLogWriter pattern) to prevent partial/corrupted markdown or JSON specs on SIGKILL.

### 43. Bash Launcher Exec-Trap Annihilation & Active Circuit-Breaker Deadlocks
- **Symptom**: Background session reconciliation (`--reconcile-orphaned`) fails to run when terminal or shell terminates; or an active Sentinel circuit breaker traps the agent in an unrecoverable deadlock by blocking all tool execution.
- **Cause**:
  1. Launcher scripts using `exec <cmd>` replace the shell process at the kernel level, destroying all registered bash signal handlers (`trap ... EXIT INT TERM`).
  2. A pre-tool hook checking Sentinel error loops blocks tools indiscriminately, blocking even the self-healing tools needed to resolve the loop.
  3. Spatial Canvas nodes injected by Sentinel CLI are invisible in the UI because long-running API servers cache graph state in memory without checking disk `mtime`.
- **Fix**:
  1. In launcher scripts (`gerych.sh`), replace `exec <cmd>` with direct calls capturing `EXIT_CODE=$?`, exit via `exit $EXIT_CODE`, and protect `cleanup_on_exit()` with a re-entrancy flag (`_CLEANUP_CALLED=1`).
  2. In pre-tool hooks (`hermes_pre_tool_hook.py` Rule 9), enforce a strict Escape Hatch: whitelist `dnk_query_error_solutions`, `dnk_record_error_solution`, `dnk_distiller_tool`, verification commands (`verify_all.sh`, `pytest`), and provide an emergency bypass (`DNK_BYPASS_SENTINEL=1`).
  3. Add `mtime` staleness checks in `NodeTaskPersistenceManager.load_graph()` to auto-refresh in-memory graph caches upon external file writes.

### 44. Pre-Tool Hook Event Payload Contract (`hook_event_name`) & Synthetic Testing
- **Symptom**: Subprocess integration tests simulating `scripts/system/hermes_pre_tool_hook.py` return `{}` (noop) or fail to trigger guardrails (such as PR blocking, loop detection, or commit guards), even when testing dangerous operations.
- **Cause**: The hook checks `payload.get("hook_event_name") == "pre_tool_call"` as its primary guard condition. If this key is absent from the input JSON (as is common when callers pass a bare `{"tool_name": ...}` dict), the hook assumes it was invoked for an unrelated lifecycle event and exits cleanly with `{}`.
- **Fix**: All unit tests, fixtures, and synthetic harness callers must supply `"hook_event_name": "pre_tool_call"` alongside `"tool_name"` and `"tool_args"` in the stdin JSON payload.

### 45. Session Sentinel Auto-Dispatch Recursion Spiral & Circuit Breaker
- **Symptom**: Autonomous self-healing triggers another agent run, which fails and triggers another self-healing run, creating an unbounded cascading execution spiral that exhausts tokens and API limits.
- **Cause**: Lack of lineage depth tracking between parent and child healing sessions.
- **Fix**: Persist lineage in `data/self_heal_lineage.json` mapping child session IDs to parent sessions with incrementing `recursion_depth`. In `SessionSentinel`, inspect session history for depth markers (`Recursion Depth: X` or `[Self-Heal Autopilot Depth X/Y]`). Enforce a strict Circuit Breaker: when `depth >= max_recursion_depth` (default 2), trip the breaker, log a `CRITICAL` `ERROR_LOOP` anomaly in `data/sentinel_alerts.json`, and halt automatic dispatch (`recursion_depth_exceeded`).

### 46. Path Hygiene False Positives on Synthesized Self-Heal Task Specs
- **Symptom**: `core/playbooks/scripts/enforce_relative_paths.py` fails during pre-commit or verification gates because newly synthesized self-heal task files (`docs/plans/self_heal/TASK-DNK-SELFHEAL-*.md`) contain raw stack traces or tool inputs embedding `/Users/...` absolute paths.
- **Cause**: Error logs and tracebacks captured from failed sessions frequently contain absolute filesystem paths in `raw_evidence`. When serialized verbatim into markdown task specs, they trigger the zero-tolerance absolute path auditor.
- **Fix**: When synthesizing task specifications, sanitize raw evidence strings using regex substitution `re.sub(r'/Users/[^/\s]+', '$HOME', evidence)` before writing to disk, and ensure `enforce_relative_paths.py` ignores historical verification plan directories.

### 47. Multi-Worker Read-Modify-Write Race Condition on Telemetry & Canvas JSON Files
- **Symptom**: Intermittent `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` or truncated JSON files (`visual_shell_db.json`, `accounting_log.json`, `sentinel_alerts.json`) when executing parallel swarm pipelines.
- **Cause**: Standard Python `open(path, 'w')` truncates the file immediately upon opening. If another worker thread or process reads the file between truncation and `json.dump()` completion, it reads an empty string or partial JSON.
- **Fix**: Mandatory use of `core/atomic_store.py` (`atomic_json_read`, `atomic_json_write`, `atomic_json_update`). Employs POSIX `fcntl.flock(LOCK_EX / LOCK_SH)` around operations and writes to a same-directory temporary file followed by atomic `os.replace` to guarantee all reads and writes are clean and non-colliding.

### 48. Skills Guard Heuristic Quarantine (`path_traversal` / `agent_config_mod`)
- **Symptom**: `skill_view` returns `[Quarantined Skill] ... refusing to load` or `scan_skill` returns `dangerous`.
- **Cause**: `tools.skills_guard.scan_skill` executes static regex analysis. Relative path traversals (`../../`) in markdown links trigger `path_traversal`, and literal citations of agent governance filenames (`AGENTS.md`) trigger `agent_config_mod`.
- **Fix**: Always refer to project templates using canonical root-relative paths without `../` (e.g. `docs/templates/...`), and refer to governance files conceptually (e.g. "DNK OS architecture invariants"). See `references/workspace_capacity_audit_and_skills_guard_quarantine_hygiene.md`.

### 49. Test Suite `sys.path` Module Poisoning Between Hermes Agent and Workspace
- **Symptom**: `ModuleNotFoundError: No module named 'plugins.slack_plugin'` when running full test suite across multiple files.
- **Cause**: Tests importing tools from `core/hermes_agent` insert that directory to `sys.path[0]`. Because `core/hermes_agent` contains an internal `plugins/` directory, subsequent imports resolve to the wrong package.
- **Fix**: Always remove the injected path from `sys.path` immediately after importing Hermes tools, or explicitly re-prioritize repository root at the top of `sys.path` in plugin test suites.

### 50. In-Process Function Dispatch Illusion (Solo Agent Bottleneck)
- **Symptom**: Gerych Prime exhausts its 25-tool action budget and blows up its context window while specialized agents remain idle in memory.
- **Cause**: In-process dispatcher executes worker logic synchronously within the orchestrator's session instead of isolated background worker processes. Subprocess wrappers (`gerych_swarm.sh`) also risked dropping `--agent` arguments, resetting subagent identities back to `gerych_prime`.
- **Fix**: See `references/solo_agent_syndrome_cure_and_subagent_spawning_protocol.md`. Enforce Step 0 Triage gating ($C > 3$), physical subagent spawning via `delegate_task` or CLI subprocess (`./scripts/system/gerych_swarm.sh --agent <agent_role> -q "<task>"`), strict input spec ➔ output JSON artifact boundaries (`data/swarm_artifacts/`), and role-based tool gating. Ensure launcher shell wrappers explicitly forward `--agent "$TARGET_AGENT"` and export `HERMES_AGENT_NAME`.

### 51. Concurrent File Mutation Collisions in Parallel Swarm Workers
- **Symptom**: Parallel coding workers overwrite each other's changes or trigger merge conflicts.
- **Cause**: Workers running directly in root `$HUB_ROOT` without filesystem isolation.
- **Fix**: Use `SwarmWorktreeManager` (`core/orchestrator/swarm_worktree.py`) with `isolated_worktree(task_id, agent)` context manager. Run workers inside `.worktrees/<task_id>` on temporary branches `swarm/<agent>/<task_id>`, enforce deterministic NDJSON audit logging in `data/swarm_artifacts/audit_trail.ndjson`, and gate merging through Sangha Consensus Review (`evaluate_sangha_consensus`). See `references/agent_swarm_benchmarks_and_ledger_worktree_patterns.md`.






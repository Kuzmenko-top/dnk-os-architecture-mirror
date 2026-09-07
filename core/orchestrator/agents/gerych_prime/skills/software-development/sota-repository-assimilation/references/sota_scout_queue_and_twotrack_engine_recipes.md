# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/sota_scout_queue_and_twotrack_engine_recipes.md"
# purpose: "SOTA Scout background queue, Two-Track compliance, and AST sanitization engine patterns for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# SOTA Scout Queue & Two-Track Engine Recipes

## 1. Core Architecture Overview
The SOTA Scout Engine (`core/orchestrator/sota_scout.py`) and its CLI runner (`scripts/system/sota_scout_runner.py`) automate the 5-level repository ingestion lifecycle with legal safety, AST hygiene, and swarm capability distribution.

### 5-Stage Pipeline
1. **Metadata & README Retrieval**: GitHub REST API / MCP ingestion with 24h caching in `data/sota_scout_cache.json`.
2. **Two-Track License Compliance Classifier**:
   - **Track 1 (Permissive)**: `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `Unlicense`, `CC0`.
     - Direct template, component, and architectural pattern assimilation into `core/` or `apps/`.
   - **Track 2 (Copyleft / Proprietary)**: `GPL-2.0`, `GPL-3.0`, `AGPL-3.0`, `LGPL`, `SSPL`, `BSL`, `CC-BY-NC`.
     - **Clean-Room Reverse Engineering**: Code copy is strictly forbidden. Extract high-level specifications, schemas, interfaces, and generate an independent clean-room implementation with explicit `CLEAN-ROOM REVERSE-ENGINEERING INVARIANT` tags.
3. **AST Pattern Extraction & Code Sanitizer**:
   - Converts absolute paths (`/Users/...`, `/home/...`) into canonical relative paths (`./`, `../`).
   - Redacts sensitive credentials (tokens, API keys, passwords) with `[REDACTED]`.
   - Automatically injects compliant DNK-MRH headers (`DNK-STD-0075`).
4. **Multichannel Knowledge Generation**:
   - **SCONES Memory**: Appends structured JSON to `.scones/sota_memories.json` under topic `SOTA_ASSIMILATION_<SLUG>`.
   - **Hermes Skill**: Authors `skills/<repo>_assimilated/SKILL.md` with recipes, pitfalls, and invariant tags.
   - **SOTA Knowledge Card**: Outputs structured markdown in `docs/tech/sota_assimilation/SOTA_<SLUG>_ASSIMILATION.md`.
   - **Obsidian Note**: Generates `docs/notes/xxx_<slug>_sota_assimilation_audit.md` adhering to YAML frontmatter and HTML comment MRH header.
5. **Swarm Routing & TaskDNA Generation**:
   - Routes work to the appropriate specialist worker (`dnk_video_ai_creator`, `gerych_builder`, `dnk_shopify`, `dnk_dev_fullstack`, `gerych_auditor`).
   - Produces evolutionary DAG with tool call budgets (MASE <= 25 tools/slice).

---

## 2. CLI Runner (`scripts/system/sota_scout_runner.py`)

### Direct Assimilation
```bash
./.venv/bin/python3 scripts/system/sota_scout_runner.py --repo "GVCLab/PersonaLive" --focus video,streaming
```

### Background Queue Management
```bash
# Enqueue a repository with high priority (1 is highest)
./.venv/bin/python3 scripts/system/sota_scout_runner.py --repo "org/lib" --enqueue --priority 1

# Check queue status and pending items
./.venv/bin/python3 scripts/system/sota_scout_runner.py --status
./.venv/bin/python3 scripts/system/sota_scout_runner.py --list

# Process up to N jobs from the queue
./.venv/bin/python3 scripts/system/sota_scout_runner.py --process-queue --max-jobs 2
```

---

## 3. Python API Integration
```python
from core.orchestrator.sota_scout import SOTAScoutEngine, ScoutJobQueue

engine = SOTAScoutEngine()

# 1. Audit License
track, license_name, notes = engine.audit_license_two_track("org/repo")

# 2. Sanitize Code
clean_code = engine.sanitize_code(
    raw_code=untrusted_code,
    file_path="core/modules/adapter.py",
    purpose="Clean-room adapter implementation"
)

# 3. Full Assimilation Pipeline
result = engine.assimilate(
    repo_url="org/repo",
    focus_areas=["realtime_canvas", "streaming"]
)
```

---

## 4. Pitfalls & Invariants
- **Fail-Closed Licensing**: If license detection cannot confirm a permissive license with 100% confidence, the engine defaults to Track 2 Clean-Room Isolation.
- **No Absolute Paths**: All generated skills, digests, and sanitized code must strictly pass the relative path invariant check.
- **Swarm Mapping Integrity**: Repositories must not default to generic media workers unless visual/video frameworks (Remotion, WebGL, Canvas) are explicitly detected.

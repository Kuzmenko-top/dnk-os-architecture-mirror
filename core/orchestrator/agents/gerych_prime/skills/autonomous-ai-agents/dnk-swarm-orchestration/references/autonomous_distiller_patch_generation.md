# 🛠️ Autonomous Distiller Patch Generation & Self-Healing Pipeline (DISTILL-PATCH-001)

## 1. Executive Summary & Purpose
When an automated test, build, or runtime pipeline fails, manual or trial-and-error shell guessing burns tokens, introduces context bloat, and risks exhausting tool execution budgets. 
The **Autonomous Distiller Patch Generator** (`core/error_distillation/patch_generator.py`) establishes a deterministic, closed-loop mechanism that:
1. Matches runtime error tracebacks against verified, historical error distillations (`docs/scones/error_distillations.json`).
2. Synthesizes clean, unified `diff` patches and performs safe fuzzy replacements on target source files.
3. Validates changes in dry-run mode before modifying files on disk.
4. Preserves resolved fixes directly back into cognitive long-term memory (`dnk_record_error_solution`).

---

## 2. Architectural Components (`core/error_distillation/`)

### 2.1 Traceback Fingerprinting & Similarity Matcher
- **Regex Extraction**: Distills incoming stack traces down to core exception types, error messages, and file locations.
- **Token Overlap (Jaccard Similarity)**:
  - Tokenizes stack traces using `\b\w{2,}\b` (preserving short technical tokens like `db`, `os`, `ws`).
  - Computes intersection over union: $|T_{query} \cap T_{db}| / |T_{query} \cup T_{db}|$.
- **Sequence Matching**:
  - Employs `difflib.SequenceMatcher` to compare raw exception messages for high-confidence character-level matching.
- **Confidence Scoring**:
  - $S = 0.6 \times \text{Jaccard} + 0.4 \times \text{SequenceRatio}$.
  - Candidates with $S \ge 0.35$ qualify for automated patch synthesis.

### 2.2 Deterministic Patch Synthesis & Fuzzy Replacement
- **Unified Diff Generation**: Uses `difflib.unified_diff` to produce standard patch strings formatted with standard `--- / +++ / @@` headers.
- **Fuzzy Replacement Strategy**:
  - Locates target code blocks even when minor whitespace or comment drift exists.
  - Generates atomic file replacements with immediate syntax and verification checks.
- **Dry-Run Validation**:
  - Evaluates `generator.apply_patch(dry_run=True)` to confirm file readability, exact string match, and path safety before committing disk mutations.

### 2.3 Strict Path Traversal Safety Invariant (`is_safe_path`)
- **Vulnerability**: Unchecked file paths generated from arbitrary error traces or LLM hallucinated paths can escape repository boundaries (`../../etc/passwd`).
- **Safety Gate**:
  - Every target path is resolved against `repository_root`.
  - Any path containing `..`, leading slashes escaping workspace root, or resolving outside the project root raises a strict `ValueError("Path traversal detected")`.

---

## 3. Operational Workflow & Tool Invocation

```
[Test/Command Failure]
         │
         ▼
[dnk_query_error_solutions(error_text)]
         │
         ├─► [Match Found (Confidence >= 0.35)]
         │         │
         │         ▼
         │   [DistillerPatchGenerator.synthesize_patch()]
         │         │
         │         ▼
         │   [Dry-run Verification & File Patch]
         │         │
         │         ▼
         │   [Targeted Test Run (pytest / tsc)] ──► [Green] ──► [Commit]
         │
         └─► [No Match Found]
                   │
                   ▼
             [Root-Cause Fix & Verify]
                   │
                   ▼
             [dnk_record_error_solution(error, cause, solution)]
```

---

## 4. Key Lessons & Integration Guidelines
1. **Never Iteratively Guess in Shell**: On encountering an exception, invoke `dnk_query_error_solutions` first. If an existing distillation exists, apply the distilled patch directly.
2. **Atomic Verification**: Always execute targeted verification (`./.venv/bin/pytest tests/...` or `npm run --prefix apps/web type-check`) immediately after applying a patch.
3. **Continuous Knowledge Distillation**: Once a novel bug is diagnosed and resolved, call `dnk_record_error_solution` to ensure the entire swarm benefits from the solution on subsequent runs.

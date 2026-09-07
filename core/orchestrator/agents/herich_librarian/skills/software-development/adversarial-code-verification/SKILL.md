---
name: adversarial-code-verification
description: "Dual-agent Red Team vs Blue Team security AST code review."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [adversarial-review, red-team, blue-team, security, ast-analysis, quality-gate]
    related_skills: [requesting-code-review, systematic-debugging, test-driven-development]
---

# Adversarial Code Verification (Red Team vs Blue Team)

Dual-agent code review pattern that pits an aggressive Red Team attacker against a defensive Blue Team refuter to eliminate both false negatives (uncaught security flaws) and false positives (blocking test mocks/fixtures).

## When to Use

- Before committing or opening a PR when performing automated AST code security scans
- When running automated pre-commit gates (`scripts/verify_all.sh`)
- When validating python code for hardcoded secrets, absolute path violations, missing MRH headers, or async deadlocks
- When insulating test suites (`tests/`, `conftest.py`) from false-positive security blocks

## Core Architecture (3-Stage Active Gate)

1. **Red Team (Auditor / Attacker ⚔️)**:
   - Performs deep AST analysis and probe injection over target files.
   - Searches for hardcoded secret patterns, tokens, absolute filesystem paths, missing Machine-Readable Headers (MRH), SQLi in raw queries, SSRF, CORS/CSRF vulnerabilities, and async deadlock risks.
   - Uses specialized probe suites (e.g. `PyRIT`, `garak`, `promptfoo` prompt libraries) in isolated sandbox environments with strict rate limiting (e.g. 100 probes/min) to prevent API quota exhaustion.
   - Computes Attack Success Rate (ASR) metrics.

2. **Blue Team (Builder / Defender 🛡️)**:
   - Evaluates each Red Team finding against context rules and sanitization schemas.
   - Automatically refutes valid false positives (e.g. test fixtures, mock data, `conftest.py` setups, redacted placeholders `[REDACTED]`).
   - Filters benign prompts (e.g. if ASR < 5% on benign probes).
   - Confirms genuine security vulnerabilities or quality violations.

3. **Multi-Stage Quality Gates**:
   - **Gate 1 (PR Fast-Path, <5 min)**: Pre-commit / PR blocking scan for AST secrets, absolute paths, MRH compliance, and basic prompt injection.
   - **Gate 2 (Pre-Deploy Comprehensive, 15 min)**: Full scan including SSRF, raw SQL injection, concurrency heuristics, and deep probe sets.
   - **Gate 3 (Production Drift Canary, every 30 min)**: Scheduled canary probes monitoring live behavior drift in staging/production.

4. **Adversarial Gate Verdict & Evidence Store**:
   - If confirmed findings == 0: **PASS** (100% Verified). Generates signed `adversarial_report.json` with ASR metrics.
   - If confirmed findings > 0: **FAIL** (blocks pre-commit / PR pipeline).

## Workflow Steps

### Step 1: Triggering Adversarial Scan
Run the adversarial review tool or unified verification gate:
```bash
# Executing via unified pre-commit script
bash scripts/verify_all.sh

# Or direct invocation via Python/Hermes tool
dnk_run_adversarial_review(target_path="core/security")
```

### Step 1b: LLM-Driven Dual-Agent Debate Loop (Gemini / Multi-Model Adaptation)
When using LLM agents (e.g. Gemini 1.1 Pro) as Auditor and Builder:
- **Auditor (Red Team)**: Prompted specifically to challenge security, architecture, AST standards, and edge cases in the submission.
- **Builder (Blue Team)**: Prompted to refute invalid findings, defend design choices, or propose architectural mitigations.
- **Approval Logic**:
  $$\text{approval\_threshold} = 0.50$$
  $$\text{approved} = (\text{auditor\_score} \ge \text{approval\_threshold}) \land (\text{builder\_score} \ge \text{approval\_threshold})$$
- **Testing & Mocking**: Unit tests should mock the underlying LLM client (e.g., `google.genai.Client`) returning structured responses (`Auditor Score`, `Builder Score`, `Verdict`) using standard `unittest.mock.MagicMock` or `pytest` `monkeypatch` to avoid external API calls during CI/CD.

### Step 2: AST & Pattern Inspection
The Red Team scans for:
- Secret Leaks: `api_key`, `jwt_secret`, `private_key`, `token` (unless redacted as `[REDACTED]`).
- Absolute Paths: Hardcoded system paths such as `/Users/...` or `/home/...` (enforces relative path SSOT).
- Structural Quality: Missing Machine-Readable Headers (e.g. `DNK-MRH-HEADER`).
- Concurrency: Unawaited coroutines or blocking I/O calls inside `async def` functions.

### Step 3: False-Positive Defense & Refutation
The Blue Team automatically checks context before blocking:
- Is the finding inside `tests/`, `conftest.py`, or a test fixture? -> **Refuted as False Positive**.
- Is a token string explicitly masked with `[REDACTED]` or placeholder syntax? -> **Refuted as False Positive**.
- Is the path relative (`./`, `../`) or dynamically constructed via `Path`? -> **Refuted as False Positive**.

### Step 4: Remediation
If genuine issues are confirmed:
1. Mask all secrets using environment variables or `[REDACTED]` for documentation.
2. Convert all absolute paths to relative path resolution.
3. Add required MRH headers to module tops.
4. Re-run `bash scripts/verify_all.sh` to confirm 100% Green status.

## Pitfalls & Lessons Learned

- **Test Fixture False Positives**: Without a Blue Team defense layer, Red Team scanners will flag mock secrets in unit tests, creating developer friction. Always insulate test directories.
- **Decoupled Tool Invocation**: Tool wrappers invoking `AdversarialReviewEngine` should avoid hard runtime dependencies on orchestrator event buses (`RuntimeEventBus`), using graceful fallbacks so security review can execute in standalone CLI scripts, pre-commit hooks, and isolated tests.
- **Import Shadowing**: In split repositories (e.g. `root/` vs `sub_app/`), ensure test suites set explicit `PYTHONPATH` so the security engine imports cleanly in both environments.
- **Fail-Closed Execution**: If AST parsing encounters a syntax error, treat it as a finding to ensure malformed code cannot bypass security scans.

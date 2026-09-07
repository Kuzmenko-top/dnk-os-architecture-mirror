#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/hermes_pre_tool_hook.py"
# purpose: "SOTA Pre-Tool-Call Auto-Sanitizer & Circuit Breaker for Hermes/Gerych with Auto-Relative Path Resolution."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import os
import re
import sys
import time
from pathlib import Path


def get_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for p in [current, *current.parents]:
        if (p / "AGENTS.md").exists() or (p / ".git").exists():
            return p
    return current.parent.parent


def get_tracker_file(session_id: str) -> Path:
    clean_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_")) or "default"
    return Path(f"/tmp/hermes_loop_tracker_{clean_id}.json")


def load_tracker(session_id: str) -> dict:
    tfile = get_tracker_file(session_id)
    if tfile.exists():
        try:
            with open(tfile, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"history": [], "last_clean": time.time()}


def save_tracker(session_id: str, data: dict):
    try:
        tfile = get_tracker_file(session_id)
        data["history"] = data.get("history", [])[-120:]
        with open(tfile, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def has_completed_evidence(repo_root: Path, max_age_seconds: int = 900) -> bool:
    evidence_dir = repo_root / "docs" / "audit"
    if not evidence_dir.exists():
        return False
    ev_files = sorted(evidence_dir.glob("*-evidence.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not ev_files:
        return False
    latest_file = ev_files[0]
    file_age = time.time() - latest_file.stat().st_mtime
    if file_age > max_age_seconds:
        return False
    try:
        ev_data = json.loads(latest_file.read_text(encoding="utf-8"))
        return ev_data.get("status") == "Completed"
    except Exception:
        return False


def is_pr_creation_request(tool_name: str, tool_input: dict) -> bool:
    if tool_name == "mcp__github__create_pull_request":
        return True
    if tool_name == "tool_call" and tool_input.get("name") == "mcp__github__create_pull_request":
        return True
    if tool_name in ("terminal", "execute_code"):
        cmd = tool_input.get("command") or tool_input.get("code") or ""
        if any(x in cmd for x in ("gh pr create", "gh pr edit")):
            return True
        if ("gh api" in cmd or "curl" in cmd) and "pulls" in cmd and any(m in cmd for m in ("-X POST", "--method POST", "-d ", "--data")):
            return True
    return False


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({}))
            sys.exit(0)

        event = json.loads(raw_input)
        hook_name = event.get("hook_event_name")
        tool_name = event.get("tool_name", "")
        tool_input = event.get("tool_input", {}) or {}
        session_id = event.get("session_id", "default")
        cwd = Path(event.get("cwd") or os.getcwd()).resolve()

        if hook_name != "pre_tool_call":
            print(json.dumps({}))
            sys.exit(0)

        repo_root = get_repo_root()
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        for sp in (repo_root / ".venv" / "lib").glob("python*/site-packages"):
            if str(sp) not in sys.path:
                sys.path.insert(0, str(sp))
        tracker = load_tracker(session_id)
        modified_args = {}
        modified_tool_name = None

        # 0.5. Canonical Tool Alias Translation (Context Window Tax mitigation)
        try:
            from core.orchestrator.tool_aliases import resolve_tool_name
            canonical_tool = resolve_tool_name(tool_name)
            if canonical_tool and canonical_tool != tool_name:
                modified_tool_name = canonical_tool
                tool_name = canonical_tool
        except Exception:
            pass

        # Ensure docs/notes symlink to external Obsidian Vault exists
        notes_symlink = repo_root / "docs" / "notes"
        if not notes_symlink.exists() and not notes_symlink.is_symlink():
            vault_target = Path(os.path.expanduser("~/Documents/DNK_HUB My Notes/DNK_HUB My Notes")).resolve()
            if vault_target.exists():
                try:
                    notes_symlink.symlink_to(vault_target)
                except Exception:
                    pass

        # 1. Inspect & Auto-Sanitize Path Hygiene & Intelligent CWD Resolution
        path_keys = ["path", "file", "target_path", "filepath", "workdir"]
        for key in path_keys:
            if key in tool_input and isinstance(tool_input[key], str):
                raw_path = tool_input[key].strip()
                if not raw_path:
                    continue

                # 1.0. Virtual Obsidian Vault prefix 'vault:<note_or_canvas>'
                if raw_path.startswith("vault:"):
                    sub_p = raw_path[6:].lstrip("/\\")
                    target_note = repo_root / "docs" / "notes" / sub_p
                    rel_p = os.path.relpath(target_note, cwd)
                    modified_args[key] = rel_p
                    continue

                # 1.1. External Obsidian Vault path leak auto-sanitization to relative docs/notes
                if "DNK_HUB My Notes" in raw_path:
                    note_sub = raw_path.split("DNK_HUB My Notes")[-1].lstrip("/\\")
                    if note_sub.startswith("DNK_HUB My Notes/"):
                        note_sub = note_sub[len("DNK_HUB My Notes/"):]
                    target_note = repo_root / "docs" / "notes" / note_sub
                    rel_p = os.path.relpath(target_note, cwd)
                    modified_args[key] = rel_p
                    continue

                if raw_path.startswith("/Users/"):
                    try:
                        abs_p = Path(raw_path).resolve()
                        if str(abs_p).startswith(str(repo_root)):
                            rel_p = os.path.relpath(abs_p, cwd)
                            modified_args[key] = rel_p
                    except Exception:
                        pass
                else:
                    # Check relative path resolution
                    target_candidate_cwd = (cwd / raw_path).resolve()
                    target_candidate_root = (repo_root / raw_path).resolve()

                    # If not found from CWD but found from repo root, bridge the relative path
                    if not target_candidate_cwd.exists() and target_candidate_root.exists():
                        rel_from_cwd = os.path.relpath(target_candidate_root, cwd)
                        modified_args[key] = rel_from_cwd
                    elif cwd != repo_root:
                        # For newly created files: if path starts with a canonical hub root folder, anchor to repo_root
                        root_prefixes = ("docs/", "apps/", "services/", "core/", "tests/", "scripts/", "config/")
                        if any(raw_path.startswith(pref) for pref in root_prefixes):
                            rel_from_cwd = os.path.relpath(target_candidate_root, cwd)
                            modified_args[key] = rel_from_cwd

        # 1.5. Python Virtualenv & PYTHONPATH Auto-Bridge + Obsidian Vault & Fast-Fail Command Sanitizer
        if tool_name in ("terminal", "execute_code"):
            cmd = tool_input.get("command") or tool_input.get("code") or ""
            if cmd:
                new_cmd = cmd
                # Auto-sanitize absolute Obsidian paths in shell commands
                if "DNK_HUB My Notes" in new_cmd:
                    new_cmd = re.sub(r'([^\s"\'=]*)/Documents/DNK_HUB My Notes/DNK_HUB My Notes/?', r'./docs/notes/', new_cmd)
                    new_cmd = re.sub(r'([^\s"\'=]*)/Documents/DNK_HUB My Notes/?', r'./docs/notes/', new_cmd)

                # Fast-Fail Terminal Sanitizer (Pillar 4: Eliminate 180s command hangs)
                # 1. gitleaks detect: limit log depth and redact to prevent deep-history hanging
                if re.search(r'\bgitleaks\s+detect\b', new_cmd) and not any(opt in new_cmd for opt in ("--log-opts", "--staged")):
                    new_cmd = re.sub(r'\bgitleaks\s+detect\b', 'gitleaks detect --log-opts="-n 5" --redact', new_cmd)

                # 2. act / act --dry-run: replace with fast actionlint or list mode to prevent docker daemon freeze
                if re.search(r'\bact(\s+--dry-run|\s+-n)?(\s|$)', new_cmd) and not any(opt in new_cmd for opt in ("-l", "actionlint")):
                    new_cmd = re.sub(
                        r'\bact(\s+--dry-run|\s+-n)?(\s|$)',
                        r'actionlint .github/workflows/*.yml 2>/dev/null || act -l -W .github/workflows\2',
                        new_cmd
                    )

                # 3. Server / Daemon Hang Watchdog: prevent inline uvicorn / http.server commands from hanging Hermes runner
                is_server_cmd = bool(
                    re.search(r'(?:python3?|\.venv/bin/python)\s+-c\s+[\'"].*(?:uvicorn|http\.server|serve_forever)', new_cmd, re.DOTALL)
                    or re.search(r'(?:^|&&|\|\||;)\s*(?:[\w\./]*/)?(?:uvicorn\b|python3?\s+-m\s+http\.server)', new_cmd)
                )
                if is_server_cmd and not any(t_kw in new_cmd for t_kw in ("timeout", "gtimeout")):
                    timeout_bin = "/opt/homebrew/bin/timeout" if Path("/opt/homebrew/bin/timeout").exists() else "timeout"
                    new_cmd = f"{timeout_bin} 45s {new_cmd}"

                venv_python = repo_root / ".venv" / "bin" / "python"
                venv_pytest = repo_root / ".venv" / "bin" / "pytest"
                if venv_python.exists():
                    rel_py = os.path.relpath(venv_python, cwd)
                    rel_pytest = os.path.relpath(venv_pytest, cwd)
                    if not rel_py.startswith((".", "/")):
                        rel_py = f"./{rel_py}"
                    if not rel_pytest.startswith((".", "/")):
                        rel_pytest = f"./{rel_pytest}"

                    new_cmd = re.sub(r'(?<![/\w])python3?(?=\s|$)', rel_py, new_cmd)
                    new_cmd = re.sub(r'(?<![/\w])pytest(?=\s|$)', rel_pytest, new_cmd)
                if new_cmd != cmd:
                    modified_args["command" if "command" in tool_input else "code"] = new_cmd

        # 1.6 Adversarial Review Target Sanitizer (Trap Breaker)
        if tool_name == "dnk_run_adversarial_review":
            t_path = tool_input.get("target_path", "")
            if t_path in ("core", "core/", "./core", ""):
                modified_args["target_path"] = "active"

        # 2. Inspect Code Content for Forbidden Hacks (sys.path.insert/append)
        code_snippets = []
        for key in ["content", "diff", "patch", "new_string"]:
            if key in tool_input and isinstance(tool_input[key], str):
                code_snippets.append(tool_input[key])

        for snippet in code_snippets:
            if "sys.path.insert" in snippet or "sys.path.append" in snippet:
                block_msg = {
                    "action": "block",
                    "message": "❌ BLOCKED by DNK OS Circuit Breaker: 'sys.path' manipulation is forbidden. The environment already injects $PYTHONPATH with all root modules. Fix your imports (e.g. 'from services... import ...') directly without mutating sys.path."
                }
                print(json.dumps(block_msg))
                sys.exit(0)

        # 3. Anti-Tampering Test Guardrail (Block tampering with existing tests to fake green builds)
        target_path = tool_input.get("path") or tool_input.get("file") or ""
        allow_test_tamper = os.environ.get("DNK_ALLOW_TEST_TAMPER", "").strip().lower() in ("1", "true", "yes")

        if tool_name in ("patch", "write_file") and target_path and not allow_test_tamper:
            # Check if target is an existing test file
            norm_target = str(Path(target_path)).replace("\\", "/")
            is_test_file = (
                "/tests/" in norm_target
                or norm_target.startswith("tests/")
                or norm_target.endswith("_test.py")
                or Path(norm_target).name.startswith("test_")
            )
            
            if is_test_file:
                # Check if file already exists (editing existing tests is blocked; creating new tests is allowed)
                target_cand = (cwd / target_path).resolve()
                target_root_cand = (repo_root / target_path).resolve()
                if target_cand.exists() or target_root_cand.exists():
                    block_msg = {
                        "action": "block",
                        "message": (
                            f"❌ BLOCKED by DNK OS Anti-Tamper Guard: Modification of existing test '{target_path}' "
                            "is prohibited to prevent false-green test manipulation! "
                            "Fix the production code or models instead of altering test assertions. "
                            "If you are legitimately modifying API contracts or test fixtures, re-run with DNK_ALLOW_TEST_TAMPER=1."
                        )
                    }
                    print(json.dumps(block_msg))
                    sys.exit(0)

        # 4. Loop Breaker & Mutation/Verification Tracker
        recent = tracker.get("history", [])

        # Auto-reset Circuit Breaker when verification command is executed & register verification pass
        if tool_name in ("terminal", "execute_code"):
            cmd = tool_input.get("command") or tool_input.get("code") or ""
            if any(v in cmd for v in ("verify_all.sh", "pytest", "npm test", "vitest", "actionlint", "python -m unittest", "python3 -m unittest", "test_")):
                tracker["blocked_paths"] = {}
                tracker["history"] = []
                tracker["verification_passed"] = True
                save_tracker(session_id, tracker)
                recent = []

        if tool_name in ("patch", "write_file", "create_file", "replace_file_content", "multi_replace_file_content"):
            tracker["has_mutations"] = True
            tracker["verification_passed"] = False
            # Auto-unblock path from read circuit breaker when modified (subsequent verification reads are valid)
            if target_path:
                norm_str = str(Path(target_path).resolve())
                if "blocked_paths" in tracker:
                    tracker["blocked_paths"].pop(str(target_path), None)
                    tracker["blocked_paths"].pop(norm_str, None)
                # Reset unmutated read count on file mutation
                if "file_reads" in tracker:
                    tracker["file_reads"].pop(str(target_path), None)
                    tracker["file_reads"].pop(norm_str, None)
            save_tracker(session_id, tracker)

            consecutive_patches = 0
            for h in reversed(recent):
                if h.get("tool_name") in ("patch", "write_file", "create_file", "replace_file_content") and h.get("target_path") == target_path:
                    consecutive_patches += 1
                elif h.get("tool_name") in ("terminal", "execute_code"):
                    break
                else:
                    break

            if consecutive_patches >= 2:
                block_msg = {
                    "action": "block",
                    "message": f"❌ BLOCKED by DNK OS Circuit Breaker: You have modified '{target_path}' {consecutive_patches} times consecutively without testing. Do NOT rewrite the same file blindly. Plan the complete interface (types, imports, components) and run verification/tests."
                }
                print(json.dumps(block_msg))
                sys.exit(0)

        elif tool_name == "read_file" and target_path:
            # 4.1. Consecutive Reads Guard
            consecutive_reads = 0
            for h in reversed(recent):
                if h.get("tool_name") == "read_file" and h.get("target_path") == target_path:
                    consecutive_reads += 1
                elif h.get("tool_name") in ("terminal", "execute_code", "patch", "write_file", "replace_file_content"):
                    break
                # Note: search_files, dnk_resolve_symbol, etc. do NOT reset consecutive reads of the same file

            if consecutive_reads >= 3:
                tracker.setdefault("blocked_paths", {})[str(target_path)] = time.time()
                save_tracker(session_id, tracker)
                block_msg = {
                    "action": "block",
                    "message": f"⚠️ DNK OS Circuit Breaker: You have read '{target_path}' {consecutive_reads} times in a row. The content is already in context. Proceed with patching or executing tests."
                }
                print(json.dumps(block_msg))
                sys.exit(0)

            # 4.2. Session-Wide Anti-Read-Loop Tax Guard (Unmutated Re-Read Protection)
            file_cand = (cwd / target_path).resolve() if not Path(target_path).is_absolute() else Path(target_path).resolve()
            file_mtime = file_cand.stat().st_mtime if file_cand.exists() else 0
            norm_path = str(file_cand)

            file_reads = tracker.setdefault("file_reads", {})
            read_info = file_reads.get(norm_path) or file_reads.get(str(target_path)) or {"count": 0, "last_mtime": file_mtime}

            if file_mtime and read_info.get("last_mtime") == file_mtime:
                read_info["count"] += 1
            else:
                read_info = {"count": 1, "last_mtime": file_mtime}

            file_reads[norm_path] = read_info
            save_tracker(session_id, tracker)

            # If file has not been modified since last read and has already been read >= 3 times in this session
            if read_info["count"] >= 3:
                tracker.setdefault("blocked_paths", {})[str(target_path)] = time.time()
                save_tracker(session_id, tracker)
                block_msg = {
                    "action": "block",
                    "message": (
                        f"⚠️ BLOCKED by DNK Anti-Read-Loop Tax Guard: You have read '{target_path}' {read_info['count']} times "
                        "without any modification since your last read! The file content is already in context. "
                        "Do NOT waste tokens re-reading identical files. Proceed directly with `patch`, `write_file`, or running tests."
                    )
                }
                print(json.dumps(block_msg))
                sys.exit(0)

        # 4.3 AST Fast-Path & Anti-Search-Loop Guard
        if tool_name == "search_files":
            pattern = tool_input.get("pattern", "")
            target = tool_input.get("target", "content")
            
            # Check for symbol definition search pattern
            if pattern and target == "content":
                def_match = re.search(r"^\s*(?:export\s+)?(?:default\s+)?(?:class|interface|type|enum|function|const|def)\s+([A-Za-z0-9_]+)", pattern)
                if def_match:
                    symbol_name = def_match.group(1)
                    block_msg = {
                        "action": "block",
                        "message": (
                            f"⚡ BLOCKED by DNK AST Fast-Path Guard: You are searching for definition '{symbol_name}' using heavy regex search_files!\n"
                            f"Under Section 2 Invariant 16, invoke `dnk_resolve_symbol(symbol='{symbol_name}')` for instant <20ms AST index lookup across the repository."
                        )
                    }
                    print(json.dumps(block_msg))
                    sys.exit(0)

            # Anti-Search-Loop Guard
            consecutive_searches = tracker.get("consecutive_searches", 0) + 1
            tracker["consecutive_searches"] = consecutive_searches
            save_tracker(session_id, tracker)
            if consecutive_searches >= 4:
                block_msg = {
                    "action": "block",
                    "message": (
                        f"⚠️ BLOCKED by Anti-Search-Loop Guard: You have performed {consecutive_searches} consecutive `search_files` operations without action or verification.\n"
                        "Under Section 2 Invariant 16, invoke `dnk_resolve_symbol` for instant AST symbol resolution or proceed with targeted file inspection/modification."
                    )
                }
                print(json.dumps(block_msg))
                sys.exit(0)
        else:
            if tracker.get("consecutive_searches", 0) > 0:
                tracker["consecutive_searches"] = 0
                save_tracker(session_id, tracker)

        # 4.4 Unverified Rewrite Churn Guard (Invariant 10)
        if tool_name in ("patch", "write_file"):
            target_p = tool_input.get("path", "")
            if target_p:
                unverified = tracker.setdefault("unverified_mutations", {})
                unverified[target_p] = unverified.get(target_p, 0) + 1
                save_tracker(session_id, tracker)
                if unverified[target_p] >= 4:
                    block_msg = {
                        "action": "block",
                        "message": (
                            f"⚠️ BLOCKED by DNK Unverified Rewrite Churn Guard: You have modified '{target_p}' {unverified[target_p]} times consecutively without running verification!\n"
                            "Under Section 2 Invariant 10, run your test command (`pytest`, `npm test`, or `bash scripts/verify_all.sh`) to verify incremental changes before further modifications."
                        )
                    }
                    print(json.dumps(block_msg))
                    sys.exit(0)
        elif tool_name in ("terminal", "execute_code"):
            cmd = tool_input.get("command") or tool_input.get("code") or ""
            if any(v in cmd for v in ("pytest", "verify_all.sh", "test_", "npm test", "cargo test", "vitest", "tsc")):
                if tracker.get("unverified_mutations"):
                    tracker["unverified_mutations"] = {}
                    save_tracker(session_id, tracker)

        # 5. Anti-Bypass Guard: Block attempts to circumvent read_file circuit breaker via terminal open()/cat
        if tool_name in ("terminal", "execute_code"):
            cmd = tool_input.get("command") or tool_input.get("code") or ""
            blocked_map = tracker.get("blocked_paths", {})
            now = time.time()
            # Check active blocks (within 10 minutes)
            for b_path, b_time in list(blocked_map.items()):
                if now - b_time < 600:
                    base_name = Path(b_path).name
                    if base_name in cmd and any(kw in cmd for kw in ("open(", "cat ", "head ", "tail ", "read(")):
                        block_msg = {
                            "action": "block",
                            "message": (
                                f"❌ BLOCKED by DNK OS Anti-Bypass Guard: Attempting to circumvent the read circuit breaker "
                                f"for '{b_path}' via terminal/execute_code is prohibited! The file content is already in context. "
                                "Proceed with `patch` or run `dnk_query_error_solutions`."
                            )
                        }
                        print(json.dumps(block_msg))
                        sys.exit(0)

        # 6. Destructive Action Guard (HermesRuntime Dry-Run Simulation & Interception)
        if tool_name in ("terminal", "execute_code"):
            cmd = tool_input.get("command") or tool_input.get("code") or ""
            allow_destructive = os.environ.get("DNK_BYPASS_DESTRUCTIVE", "").strip().lower() in ("1", "true", "yes")
            if cmd and not allow_destructive:
                destructive_patterns = [
                    (r"\brm\s+-(?:rf|fr|r|f)\s+(?:apps|services|core|tests|scripts|\.|\*|~|/)", "file_system_deletion"),
                    (r"\bgit\s+reset\s+--hard\b", "git_hard_reset"),
                    (r"\bgit\s+clean\s+-(?:fdx|dfx|fx|fd)\b", "git_clean_force"),
                    (r"\bDROP\s+(?:TABLE|DATABASE)\b", "database_drop"),
                    (r"\bTRUNCATE\s+(?:TABLE)?\b", "database_truncate"),
                    (r"\bshutil\.rmtree\s*\(\s*['\"](?:apps|services|core|tests|scripts)", "python_recursive_deletion"),
                ]
                for pat, action_type in destructive_patterns:
                    if re.search(pat, cmd, re.IGNORECASE):
                        try:
                            from core.hermes_runtime import HermesRuntime
                            runtime = HermesRuntime()
                            plan = runtime.generate_dry_run_plan(
                                action_type=action_type,
                                targets=[cmd[:80]],
                                details={"session_id": session_id, "command": cmd}
                            )
                            approval_id = runtime.request_destructive_action(
                                action_type=action_type,
                                target=cmd[:80],
                                details=plan
                            )
                        except Exception:
                            plan = {"action_type": action_type, "dry_run": True, "status": "Ready for Review"}
                            approval_id = "req-dryrun"

                        block_msg = {
                            "action": "block",
                            "message": (
                                f"🛡️ BLOCKED by HermesRuntime Destructive Guard: High-risk destructive operation '{action_type}' detected!\n"
                                f"Dry-Run Plan: {json.dumps(plan)}\n"
                                f"To proceed safely, review the Dry-Run or re-run with DNK_BYPASS_DESTRUCTIVE=1 (Approval ID: {approval_id})."
                            )
                        }
                        print(json.dumps(block_msg))
                        sys.exit(0)

        # 6.5. Tier 2 CompletionGate Commit Guard (Block unverified commits/pushes after mutations)
        if tool_name in ("terminal", "execute_code"):
            cmd = tool_input.get("command") or tool_input.get("code") or ""
            if cmd and re.search(r'\bgit\s+(commit|push)\b', cmd):
                allow_unverified = (
                    os.environ.get("DNK_BYPASS_COMPLETION_GATE", "").strip().lower() in ("1", "true", "yes")
                    or os.environ.get("DNK_ALLOW_UNVERIFIED_COMMIT", "").strip().lower() in ("1", "true", "yes")
                )
                if not allow_unverified and tracker.get("has_mutations", False) and not tracker.get("verification_passed", False):
                    block_msg = {
                        "action": "block",
                        "message": (
                            "🛡️ BLOCKED by CompletionGate (Tier 2 Anti-Phantom-Done): "
                            "You have modified source files without running tests! "
                            "Execute `pytest` or `bash scripts/verify_all.sh` before committing code. "
                            "(Bypass: DNK_BYPASS_COMPLETION_GATE=1)"
                        )
                    }
                    print(json.dumps(block_msg))
                    sys.exit(0)
                elif allow_unverified or tracker.get("verification_passed", False):
                    # Commit/push permitted: reset mutation flag for subsequent changes
                    tracker["has_mutations"] = False
                    save_tracker(session_id, tracker)

        # 6.6. GitHub MCP & CI/CD Pre-PR Evidence Guard (Fail-Closed)
        if is_pr_creation_request(tool_name, tool_input):
            allow_unverified_pr = (
                os.environ.get("DNK_BYPASS_PR_GATE", "").strip().lower() in ("1", "true", "yes")
                or os.environ.get("DNK_BYPASS_COMPLETION_GATE", "").strip().lower() in ("1", "true", "yes")
            )
            has_unverified = tracker.get("has_mutations", False) and not tracker.get("verification_passed", False)
            if not allow_unverified_pr and (has_unverified or (not has_completed_evidence(get_repo_root()) and not tracker.get("verification_passed", False))):
                block_msg = {
                    "action": "block",
                    "message": (
                        "🛡️ BLOCKED by DNK OS CI/CD Pre-PR Gate: Pull request creation requires verified Master Quality Gate and Evidence artifact. "
                        "Run 'python3 scripts/system/generate_evidence.py --task <TASK_ID> --title \"<TITLE>\"' to run verification and generate evidence before creating a PR. "
                        "(Bypass: DNK_BYPASS_PR_GATE=1)"
                    )
                }
                print(json.dumps(block_msg))
                sys.exit(0)

        # 7. Adaptive Zero-Waste Iteration Pacer & Pre-Exhaustion Guard (MASE Circuit Breaker)
        call_history = tracker.setdefault("history", [])
        now_ts = time.time()
        last_call_ts = call_history[-1].get("timestamp", 0) if call_history else 0
        if last_call_ts and (now_ts - last_call_ts > 1800):
            call_history.clear()

        turn_call_count = event.get("turn_call_count") or (len(call_history) + 1)
        is_atomic_slice = os.environ.get("DNK_ATOMIC_SLICE", "").strip().lower() in ("1", "true", "yes")

        # MASE Circuit Breaker Notification at limit 25
        if turn_call_count == 25:
            sys.stderr.write(
                "\n⚠️ [MASE CIRCUIT BREAKER] Досягнуто ліміт 25 викликів інструментів! "
                "Завершіть поточний слайс, запустіть scripts/verify_all.sh, зробіть git commit та надайте звіт користувачу.\n"
            )

        if is_atomic_slice:
            if turn_call_count == 15:
                sys.stderr.write(
                    f"\n💡 [DNK Zero-Waste Pacing] {turn_call_count}/25 tool calls executed for this atomic slice. "
                    "Maintain focus on current slice scope. Prepare verification.\n"
                )
            elif turn_call_count == 22:
                sys.stderr.write(
                    f"\n⚠️  [DNK Zero-Waste Warning] {turn_call_count}/25 tool calls executed. "
                    "Slice budget almost reached! Finalize mutations and run verification immediately.\n"
                )
            elif turn_call_count >= 28 and tool_name in ("read_file", "search_files"):
                block_msg = {
                    "action": "block",
                    "message": (
                        f"🚨 BLOCKED by MASE Circuit Breaker ({turn_call_count} calls executed in atomic slice)! "
                        "Перевищено ліміт MASE (≤25 викликів на слайс). Пошукові та читальні операції зупинено. "
                        "Execute your slice verification command (`pytest` or `bash scripts/verify_all.sh`) and report completion."
                    )
                }
                print(json.dumps(block_msg))
                sys.exit(0)
        else:
            if turn_call_count >= 28 and tool_name in ("read_file", "search_files"):
                block_msg = {
                    "action": "block",
                    "message": (
                        f"🚨 BLOCKED by MASE Circuit Breaker: {turn_call_count} tool calls executed! "
                        "Перевищено ліміт MASE (≤25 викликів на слайс). Пошукові та читальні операції зупинено. "
                        "Завершіть поточний слайс, запустіть `bash scripts/verify_all.sh`, зробіть git commit та надайте звіт користувачу."
                    )
                }
                print(json.dumps(block_msg))
                sys.exit(0)
            elif turn_call_count >= 30:
                is_verification = False
                if tool_name in ("terminal", "execute_code"):
                    cmd = tool_input.get("command") or tool_input.get("code") or ""
                    if any(v in cmd for v in ("pytest", "verify_all.sh", "test_", "npm test", "cargo test", "vitest", "tsc", "git commit", "git add", "git status", "generate_evidence")):
                        is_verification = True
                
                if not is_verification and tool_name not in ("clarify", "todo", "memory", "session_search"):
                    block_msg = {
                        "action": "block",
                        "message": (
                            f"🚨 BLOCKED by MASE Hard Budget Guard: {turn_call_count}/25 calls exceeded for this turn!\n"
                            "Under Section 2 Invariant 2 (Mandatory Atomic Slice Execution), exploratory and mutation operations are halted.\n"
                            "Execute your slice verification (`pytest` or `bash scripts/verify_all.sh`), commit, and report milestone completion."
                        )
                    }
                    print(json.dumps(block_msg))
                    sys.exit(0)
            elif turn_call_count == 45:
                sys.stderr.write(
                    f"\n⚠️  [DNK Zero-Waste Warning] {turn_call_count} tool calls executed. "
                    "Approaching turn midpoint. Complete mutations and run verification.\n"
                )
            elif turn_call_count >= 65 and tool_name in ("read_file", "search_files"):
                # Proactively protect the agent from 90/90 cut-off by blocking exploratory reads early
                block_msg = {
                    "action": "block",
                    "message": (
                        f"🚨 BLOCKED by DNK Zero-Waste Budget Guard: {turn_call_count}/90 iterations consumed! "
                        "Stop reading or searching. Execute your verification command (`bash scripts/verify_all.sh` or `pytest`) "
                        "and report your completion NOW to prevent system budget cut-off."
                    )
                }
                print(json.dumps(block_msg))
                sys.exit(0)

        # 8. Swarm Delegation Guard & Anti-Solo Enforcement (Strict Dispatch Law)
        bypass_swarm = (
            os.environ.get("DNK_BYPASS_SWARM", "").strip().lower() in ("1", "true", "yes")
            or os.environ.get("DNK_SWARM_WORKER", "").strip().lower() in ("1", "true", "yes")
            or event.get("agent_id") not in (None, "", "gerych_prime", "hermes", "operator")
            or bool(tool_input.get("bypass_swarm"))
            or bool(tool_input.get("allow_solo"))
        )

        if tool_name == "dnk_triage_task":
            prompt_cand = tool_input.get("goal_or_prompt") or tool_input.get("prompt") or tool_input.get("goal") or ""
            if prompt_cand:
                try:
                    from core.orchestrator.task_triage import dnk_triage_task
                    from core.orchestrator.task_spec_generator import should_auto_spec, auto_generate_task_spec
                    triage_res = dnk_triage_task(str(prompt_cand))

                    # Auto-generate and cache Task Spec if unstructured prompt
                    if should_auto_spec(str(prompt_cand)):
                        generated_spec = auto_generate_task_spec(str(prompt_cand), triage_res)
                        tracker["active_task_spec"] = generated_spec
                        tracker["auto_spec_generated"] = True

                    if triage_res.mode == "SWARM_PARALLEL":
                        tracker["pending_swarm_dispatch"] = True
                        tracker["swarm_triage_complexity"] = triage_res.complexity_score
                        tracker["swarm_triage_domains"] = triage_res.domains_detected
                        tracker["swarm_solo_count"] = 0
                        save_tracker(session_id, tracker)
                    else:
                        tracker["pending_swarm_dispatch"] = False
                        tracker["swarm_solo_count"] = 0
                        save_tracker(session_id, tracker)
                except Exception:
                    pass

        elif tool_name in ("dnk_swarm_parallel", "dnk_swarm_dispatch", "dnk_swarm_pipeline"):
            tracker["pending_swarm_dispatch"] = False
            tracker["swarm_solo_count"] = 0
            save_tracker(session_id, tracker)

        elif tracker.get("pending_swarm_dispatch") and not bypass_swarm:
            allowed_prep_tools = (
                "dnk_scones_retrieve",
                "dnk_scones_get_memories",
                "scones_get_memories",
                "dnk_decompose_task_dna",
                "dnk_resolve_symbol",
                "dnk_swarm_status",
                "clarify",
            )
            if tool_name not in allowed_prep_tools:
                # Immediate block on direct mutation
                if tool_name in ("patch", "write_file"):
                    complexity = tracker.get("swarm_triage_complexity", "N/A")
                    domains = ", ".join(tracker.get("swarm_triage_domains", [])) or "cross-domain"
                    block_msg = {
                        "action": "block",
                        "message": (
                            f"🚨 BLOCKED by DNK Swarm Circuit Breaker: Task triage evaluated mode == 'SWARM_PARALLEL' "
                            f"(Complexity: {complexity}, Domains: {domains}).\n"
                            f"Direct file mutation ('{tool_name}') by Gerych Prime is prohibited under the STRICT DISPATCH LAW!\n"
                            f"You must dispatch parallel swarm workers via `dnk_swarm_parallel(tasks_json=...)` "
                            f"to execute domain tasks concurrently instead of mutating code solo.\n"
                            f"(To bypass if solo execution is explicitly demanded, run with DNK_BYPASS_SWARM=1)."
                        )
                    }
                    print(json.dumps(block_msg))
                    sys.exit(0)

                # Track exploratory tools (read_file, search_files, terminal, execute_code)
                if tool_name in ("terminal", "execute_code"):
                    cmd = tool_input.get("command") or tool_input.get("code") or ""
                    if any(v in cmd for v in ("verify_all.sh", "pytest", "npm test", "vitest", "git commit", "git push")):
                        tracker["pending_swarm_dispatch"] = False
                        tracker["swarm_solo_count"] = 0
                        save_tracker(session_id, tracker)
                    else:
                        solo_cnt = tracker.get("swarm_solo_count", 0) + 1
                        tracker["swarm_solo_count"] = solo_cnt
                        save_tracker(session_id, tracker)
                        if solo_cnt > 3:
                            complexity = tracker.get("swarm_triage_complexity", "N/A")
                            domains = ", ".join(tracker.get("swarm_triage_domains", [])) or "cross-domain"
                            block_msg = {
                                "action": "block",
                                "message": (
                                    f"🚨 BLOCKED by DNK Swarm Circuit Breaker: Task triage evaluated mode == 'SWARM_PARALLEL' "
                                    f"(Complexity: {complexity}, Domains: {domains}).\n"
                                    f"You have performed {solo_cnt} consecutive solo actions without dispatching the swarm!\n"
                                    f"Under the STRICT DISPATCH LAW, your immediate next action must be `dnk_swarm_parallel(tasks_json=...)` "
                                    f"using the parallel worker assignments from the triage execution plan.\n"
                                    f"Stop reading/searching solo. Dispatch the swarm now (or set DNK_BYPASS_SWARM=1 to bypass)."
                                )
                            }
                            print(json.dumps(block_msg))
                            sys.exit(0)

                elif tool_name in ("read_file", "search_files"):
                    solo_cnt = tracker.get("swarm_solo_count", 0) + 1
                    tracker["swarm_solo_count"] = solo_cnt
                    save_tracker(session_id, tracker)
                    if solo_cnt > 3:
                        complexity = tracker.get("swarm_triage_complexity", "N/A")
                        domains = ", ".join(tracker.get("swarm_triage_domains", [])) or "cross-domain"
                        block_msg = {
                            "action": "block",
                            "message": (
                                f"🚨 BLOCKED by DNK Swarm Circuit Breaker: Task triage evaluated mode == 'SWARM_PARALLEL' "
                                f"(Complexity: {complexity}, Domains: {domains}).\n"
                                f"You have performed {solo_cnt} consecutive solo actions without dispatching the swarm!\n"
                                f"Under the STRICT DISPATCH LAW, your immediate next action must be `dnk_swarm_parallel(tasks_json=...)` "
                                f"using the parallel worker assignments from the triage execution plan.\n"
                                f"Stop reading/searching solo. Dispatch the swarm now (or set DNK_BYPASS_SWARM=1 to bypass)."
                            )
                        }
                        print(json.dumps(block_msg))
                        sys.exit(0)

        # 9. Sentinel Circuit Breaker & Live Anomaly Loop Guard
        # Intercepts active anomaly loops detected by SessionSentinel via data/sentinel_alerts.json
        bypass_sentinel = (
            os.environ.get("DNK_BYPASS_SENTINEL", "").strip().lower() in ("1", "true", "yes")
            or os.environ.get("DNK_SWARM_WORKER", "").strip().lower() in ("1", "true", "yes")
            or bool(tool_input.get("bypass_sentinel"))
        )

        # Invariant: Never block error solution distillation / self-healing queries
        # Always allow dnk_query_error_solutions, dnk_record_error_solution, and dnk_distiller_tool
        is_self_healing_tool = (
            tool_name in ("dnk_query_error_solutions", "dnk_record_error_solution", "dnk_distiller_tool")
            or (tool_name == "tool_call" and tool_input.get("name") in ("dnk_query_error_solutions", "dnk_record_error_solution", "dnk_distiller_tool"))
        )

        if not bypass_sentinel and not is_self_healing_tool:
            alerts_file = repo_root / "data" / "sentinel_alerts.json"
            if alerts_file.exists():
                try:
                    # Fast mtime check: only consider alerts generated in the last 15 minutes (900 seconds)
                    if (time.time() - alerts_file.stat().st_mtime) < 900:
                        with open(alerts_file, "r", encoding="utf-8") as af:
                            sentinel_data = json.load(af)

                        alerts = sentinel_data.get("alerts", [])
                        # Look for active loop anomalies: TOOL_LOOP, ERROR_LOOP, BUDGET_BREACH, etc.
                        loop_alerts = [
                            a for a in alerts
                            if str(a.get("category", "")).upper() in ("TOOL_LOOP", "ERROR_LOOP", "BUDGET_BREACH")
                            or (str(a.get("severity", "")).upper() in ("CRITICAL", "HIGH") and "loop" in str(a.get("title", "")).lower())
                        ]

                        if loop_alerts:
                            # Allow verification commands so the agent can test and verify resolutions
                            is_verification_cmd = False
                            if tool_name in ("terminal", "execute_code"):
                                cmd = tool_input.get("command") or tool_input.get("code") or ""
                                if any(v in cmd for v in ("verify_all.sh", "pytest", "npm test", "vitest")):
                                    is_verification_cmd = True

                            if not is_verification_cmd:
                                top_alert = loop_alerts[0]
                                category = top_alert.get("category", "TOOL_LOOP")
                                severity = top_alert.get("severity", "HIGH")
                                title = top_alert.get("title", "Active Loop Anomaly Detected")
                                desc = top_alert.get("description", "A repetitive execution or error loop was detected by SessionSentinel.")
                                fix = top_alert.get("suggested_fix", "Query `dnk_query_error_solutions` for verified fixes or revise execution approach.")

                                block_msg = {
                                    "action": "block",
                                    "message": (
                                        f"🚨 BLOCKED by Sentinel Circuit Breaker: Active anomaly loop detected by SessionSentinel!\n"
                                        f"Category: {category} | Severity: {severity}\n"
                                        f"Alert: {title}\n"
                                        f"Details: {desc}\n"
                                        f"💡 Suggested Fix: {fix}\n"
                                        f"⚡ MANDATORY ACTION: Do NOT repeat failing commands or loops. "
                                        f"Immediately query `dnk_query_error_solutions(error_text=...)` to find verified fixes, "
                                        f"or run tests/verification directly. (Set DNK_BYPASS_SENTINEL=1 to override)."
                                    )
                                }
                                print(json.dumps(block_msg))
                                sys.exit(0)
                except Exception:
                    pass

        # Record this call in isolated session tracker
        call_history.append({
            "session_id": session_id,
            "tool_name": tool_name,
            "target_path": target_path,
            "timestamp": time.time()
        })
        save_tracker(session_id, tracker)

        # If we modified arguments or tool_name, return modify directive
        if modified_args or modified_tool_name:
            out_obj = {"action": "modify"}
            if modified_args:
                merged = dict(tool_input)
                merged.update(modified_args)
                out_obj["args"] = merged
            if modified_tool_name:
                out_obj["tool_name"] = modified_tool_name
            print(json.dumps(out_obj))
            sys.exit(0)

        # Allow execution unchanged
        print(json.dumps({}))
        sys.exit(0)

    except Exception:
        # Fall-safe: if hook errors internally, do not block agent
        print(json.dumps({}))
        sys.exit(0)


if __name__ == "__main__":
    main()

# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/session_sentinel.py"
# purpose: "Autonomous Shadow Observer & Self-Healing Loop: Monitors Gerych sessions in real time, classifies defects, synthesizes canonical Task Specs v2.5 for dnk_dev_fullstack, and enqueues onto DAG Canvas."
# canonical_source: true
# alters_files: [".scones/session_lessons.json", "docs/plans/self_heal/", "docs/audit/sessions/"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import os
import re
import json
import time
import sqlite3
import datetime
import logging
from pathlib import Path
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("session_sentinel")

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
SCONES_DIR = HUB_ROOT / ".scones"
LESSONS_FILE = SCONES_DIR / "session_lessons.json"
AUDIT_REPORTS_DIR = HUB_ROOT / "docs" / "audit" / "sessions"
SELF_HEAL_DIR = HUB_ROOT / "docs" / "plans" / "self_heal"
def _parse_timestamp_to_epoch(ts: Any) -> float:
    if not ts:
        return 0.0
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        try:
            return float(ts)
        except ValueError:
            pass
        try:
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            pass
    return 0.0


class AnomalySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class AnomalyCategory(str, Enum):
    AUTH_ERROR = "AUTH_ERROR"
    MODEL_REASONING = "MODEL_REASONING"
    RUNTIME_CRASH = "RUNTIME_CRASH"
    TOOL_LOOP = "TOOL_LOOP"
    BUDGET_BREACH = "BUDGET_BREACH"
    PATH_VIOLATION = "PATH_VIOLATION"
    MRH_MISSING = "MRH_MISSING"
    TEST_FAILURE = "TEST_FAILURE"
    FALSE_COMPLIANCE = "FALSE_COMPLIANCE"
    ERROR_LOOP = "ERROR_LOOP"
    CI_CD_VIOLATION = "CI_CD_VIOLATION"


class DetectedAnomaly(BaseModel):
    category: AnomalyCategory
    severity: AnomalySeverity
    title: str
    description: str
    raw_evidence: str
    suggested_fix_summary: str
    target_files: List[str] = Field(default_factory=list)
    occurred_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())


class SessionAuditResult(BaseModel):
    session_id: str
    task_id: Optional[str] = None
    agent_name: str = "gerych_builder"
    started_at: float = 0.0
    ended_at: Optional[float] = None
    duration_sec: float = 0.0
    total_messages: int = 0
    total_tool_calls: int = 0
    tool_breakdown: Dict[str, int] = Field(default_factory=dict)
    anomalies: List[DetectedAnomaly] = Field(default_factory=list)
    efficiency_pct: float = 100.0
    user_prompt_preview: str = ""
    assistant_final_preview: str = ""
    audit_report_path: Optional[str] = None
    self_heal_task_path: Optional[str] = None
    canvas_node_id: Optional[str] = None
    recursion_depth: int = 0
    dispatched_agent: Optional[str] = None
    dispatch_status: Optional[str] = None


class SessionSentinel:
    """
    Parallel Shadow Observer & Autonomous System Doctor Engine.
    Monitors active Gerych execution sessions, detects operational and architectural flaws,
    and synthesizes actionable self-healing tasks for developer agents.
    """

    def __init__(self, agent_name: str = "gerych_prime", hub_root: Path = HUB_ROOT):
        self.agent_name = agent_name
        self.hub_root = Path(hub_root)
        self.scones_dir = self.hub_root / ".scones"
        self.lessons_file = self.scones_dir / "session_lessons.json"
        self.audit_reports_dir = self.hub_root / "docs" / "audit" / "sessions"
        self.self_heal_dir = self.hub_root / "docs" / "plans" / "self_heal"
        self.alerts_file = self.hub_root / "data" / "sentinel_alerts.json"
        self.lineage_file = self.hub_root / "data" / "self_heal_lineage.json"

    @staticmethod
    def atomic_write(path: Path, content: str) -> None:
        """
        MitigationLogWriter Pattern (from Soup):
        Crash-resilient atomic file write using POSIX lock, temp file and atomic rename.
        Guarantees that audit trails, self-heal tasks, and lessons are never corrupted by partial writes.
        """
        try:
            from core.atomic_store import atomic_json_write
            try:
                data = json.loads(content)
                atomic_json_write(path, data)
                return
            except (json.JSONDecodeError, TypeError):
                pass
        except Exception:
            pass

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.name}.tmp.{os.getpid()}_{int(time.time() * 1000)}")
        try:
            tmp_path.write_text(content, encoding="utf-8")
            tmp_path.replace(path)
        except Exception:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            # Fallback direct write
            path.write_text(content, encoding="utf-8")


    def get_agent_db(self) -> Path:
        """Returns path to the Hermes SQLite state database for the configured agent."""
        import os
        hermes_home = os.environ.get("HERMES_HOME")
        if hermes_home:
            hh_db = Path(hermes_home) / "state.db"
            if hh_db.exists():
                return hh_db
        hub_agent_db = self.hub_root / "core" / "orchestrator" / "agents" / self.agent_name / "state.db"
        if hub_agent_db.exists():
            return hub_agent_db
        primary = Path.home() / ".hermes" / "profiles" / self.agent_name / "state.db"
        if primary.exists():
            return primary
        fallback = Path.home() / ".hermes" / "state.db"
        return fallback

    def _get_db_connection(self) -> Optional[sqlite3.Connection]:
        """Returns active SQLite connection to the agent database or None if not found."""
        db_path = self.get_agent_db()
        if not db_path.exists():
            return None
        return sqlite3.connect(db_path)

    def fetch_session_data(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Loads session record and full message trajectory from SQLite state.db."""
        db_path = self.get_agent_db()
        if not db_path.exists():
            return None

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        if session_id:
            cur.execute(
                "SELECT id, model, started_at, ended_at, title FROM sessions WHERE id = ? OR id LIKE ?",
                (session_id, f"%{session_id}%")
            )
        else:
            cur.execute(
                "SELECT id, model, started_at, ended_at, title FROM sessions ORDER BY started_at DESC LIMIT 1"
            )

        row = cur.fetchone()
        if not row:
            conn.close()
            return None

        sid, model, start_ts, end_ts, title = row

        cur.execute(
            "SELECT id, role, content, tool_name, tool_calls, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC",
            (sid,)
        )
        raw_messages = cur.fetchall()
        conn.close()

        return {
            "session_id": sid,
            "model": model or "unknown",
            "started_at": start_ts or 0.0,
            "ended_at": end_ts,
            "title": title or "Untitled Session",
            "messages": raw_messages
        }

    def detect_anomalies(self, session_data: Dict[str, Any], stderr_logs: Optional[str] = None) -> List[DetectedAnomaly]:
        """
        Heuristically classifies all operational, auth, and algorithmic defects
        from the message trajectory and tool calls.
        """
        messages = session_data.get("messages", [])
        anomalies: List[DetectedAnomaly] = []

        consecutive_reads: Dict[str, int] = {}
        total_tool_calls = 0
        wasted_nav_count = 0
        total_search_files = 0
        had_ast_symbol_resolve = False
        recent_errors: List[str] = []
        had_distillation_query = False
        had_verification_tool = False
        assistant_texts: List[str] = []
        unverified_mutations: Dict[str, int] = {}
        had_pr_creation_attempt = False

        # 1. Inspect Trajectory Messages
        for mid, role, content, tool_name, tool_calls, ts in messages:
            content_str = str(content or "")

            # A. Check for Authentication Errors
            if any(k in content_str for k in ("401 Unauthorized", "HTTP 401", "Expected OAuth 2 access token", "invalid authentication credentials")):
                anomalies.append(DetectedAnomaly(
                    category=AnomalyCategory.AUTH_ERROR,
                    severity=AnomalySeverity.CRITICAL,
                    title="API Authentication Failure (HTTP 401 / Invalid Credentials)",
                    description="The agent encountered an authentication failure when invoking auxiliary or primary models.",
                    raw_evidence=content_str[:300].strip(),
                    suggested_fix_summary="Rotate or re-authenticate credentials in ~/.hermes/config.yaml or refresh environment token.",
                    target_files=["core/hermes_agent/plugins/model-providers/vertex/__init__.py", "~/.hermes/config.yaml"]
                ))

            # B. Check for Model Reasoning & Token Exhaustion / NoneType Errors
            if any(k in content_str for k in ("'NoneType' object has no attribute 'content'", "Auxiliary title generation failed", "FinishReason.MAX_TOKENS")):
                anomalies.append(DetectedAnomaly(
                    category=AnomalyCategory.MODEL_REASONING,
                    severity=AnomalySeverity.HIGH,
                    title="Auxiliary Model Output Exhaustion / NoneType Attribute Error",
                    description="Auxiliary call failed or returned empty content because reasoning model thought tokens exhausted max_tokens budget.",
                    raw_evidence=content_str[:300].strip(),
                    suggested_fix_summary="Increase max_tokens (e.g. to 1024) for reasoning models and use getattr(choice.message, 'content') fallback.",
                    target_files=["core/hermes_agent/agent/title_generator.py"]
                ))

            # C. Check Tool Calls Arguments
            if role == "assistant":
                if content_str:
                    assistant_texts.append(content_str)
                if tool_calls:
                    try:
                        tcs = json.loads(tool_calls) if isinstance(tool_calls, str) else tool_calls
                    except Exception:
                        tcs = []

                    for tc in tcs:
                        total_tool_calls += 1
                        fn = tc.get("function", {})
                        fn_name = fn.get("name", "")
                        raw_args = fn.get("arguments", "{}")
                        try:
                            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        except Exception:
                            args = {}

                        if "query_error_solutions" in fn_name or "distiller" in fn_name:
                            had_distillation_query = True

                        # D. Absolute Path Invariant Violation Check
                        args_text = str(raw_args)
                        if "/Users/" in args_text:
                            anomalies.append(DetectedAnomaly(
                                category=AnomalyCategory.PATH_VIOLATION,
                                severity=AnomalySeverity.HIGH,
                                title="Absolute Path Invariant Violation (/Users/...)",
                                description="Agent passed an absolute system path in tool arguments instead of mandatory relative path.",
                                raw_evidence=args_text[:250].strip(),
                                suggested_fix_summary="Enforce relative path sanitization (./ or ../) before dispatching tool calls.",
                                target_files=["AGENTS.md"]
                            ))

                        # E. Exploratory Nav Waste (pwd, cd, ungrounded ls)
                        if fn_name in ("terminal", "run_command", "bash"):
                            cmd = args.get("command", "") or args.get("CommandLine", "")
                            if any(v in cmd for v in ("pytest", "verify_all.sh", "test_", "npm test", "cargo test", "vitest", "tsc")):
                                had_verification_tool = True
                                unverified_mutations.clear()
                            if any(cmd.strip() == c or cmd.strip().startswith(c + " ") for c in ("pwd", "cd", "ls -la")):
                                wasted_nav_count += 1

                        # F. AST Fast-Path & Search Tracking
                        if fn_name == "dnk_resolve_symbol":
                            had_ast_symbol_resolve = True
                        elif fn_name in ("search_files", "grep"):
                            total_search_files += 1

                        # G. Modification Churn Tracking
                        if fn_name in ("write_file", "patch", "replace_file_content", "multi_replace_file_content"):
                            mut_p = args.get("path") or args.get("AbsolutePath") or args.get("file_path") or ""
                            if mut_p:
                                unverified_mutations[mut_p] = unverified_mutations.get(mut_p, 0) + 1
                                if unverified_mutations[mut_p] >= 3:
                                    churn_title = f"Unverified File Modification Churn: {Path(mut_p).name}"
                                    if not any(a.category == AnomalyCategory.TOOL_LOOP and a.title == churn_title for a in anomalies):
                                        anomalies.append(DetectedAnomaly(
                                            category=AnomalyCategory.TOOL_LOOP,
                                            severity=AnomalySeverity.MEDIUM,
                                            title=churn_title,
                                            description=f"File {mut_p} was modified {unverified_mutations[mut_p]} times consecutively without running verification tests.",
                                            raw_evidence=f"File: {mut_p} (Unverified edits: {unverified_mutations[mut_p]})",
                                            suggested_fix_summary="Plan complete changes in advance or run verification tests between modifications.",
                                            target_files=[mut_p]
                                        ))

                        # H. Read-Loop Detection
                        if fn_name in ("view_file", "read_file"):
                            target_p = args.get("path") or args.get("AbsolutePath") or args.get("file_path") or ""
                            if target_p:
                                consecutive_reads[target_p] = consecutive_reads.get(target_p, 0) + 1
                                if consecutive_reads[target_p] >= 3:
                                    read_title = f"Read Loop Detected on: {Path(target_p).name}"
                                    if not any(a.category == AnomalyCategory.TOOL_LOOP and a.title == read_title for a in anomalies):
                                        anomalies.append(DetectedAnomaly(
                                            category=AnomalyCategory.TOOL_LOOP,
                                            severity=AnomalySeverity.MEDIUM,
                                            title=read_title,
                                            description=f"File {target_p} was read {consecutive_reads[target_p]} times consecutively without modifications.",
                                            raw_evidence=f"File: {target_p} (Consecutive read count: {consecutive_reads[target_p]})",
                                            suggested_fix_summary="Cache file content in working memory or force test/action slice instead of repeated reads.",
                                            target_files=[target_p]
                                        ))

                        # I. PR Creation Tracking
                        if fn_name in ("terminal", "run_command", "bash"):
                            cmd_str = args.get("command", "") or args.get("CommandLine", "")
                            if any(v in cmd_str for v in ("gh pr create", "gh pr edit")):
                                had_pr_creation_attempt = True
                        elif fn_name in ("mcp__github__create_pull_request", "fast_create_or_update_pr"):
                            had_pr_creation_attempt = True
                        elif fn_name == "tool_call" and args.get("name") == "mcp__github__create_pull_request":
                            had_pr_creation_attempt = True
                        else:
                            # Reset read counters on action/write
                            if fn_name in ("write_file", "replace_file_content", "multi_replace_file_content", "patch"):
                                consecutive_reads.clear()

            # G. Check Tool Execution Failure
            elif role == "tool":
                if content_str and any(err in content_str for err in ("exit 1", "exit 2", "FAILED tests/", "AssertionError")):
                    anomalies.append(DetectedAnomaly(
                        category=AnomalyCategory.TEST_FAILURE,
                        severity=AnomalySeverity.HIGH,
                        title=f"Tool Execution or Test Failure in [{tool_name}]",
                        description="A verification command or test suite failed during execution.",
                        raw_evidence=content_str[:300].replace("\n", " ").strip(),
                        suggested_fix_summary="Diagnose test failure via error distiller and apply atomic code fix.",
                        target_files=[]
                    ))

                # H. Semantic Error Repetition Check (Soup Loop-Hardening Pattern)
                err_match = re.search(r'\b([A-Za-z0-9_]+(?:Error|Exception))\b', content_str)
                if err_match:
                    err_type = err_match.group(1)
                    recent_errors.append(err_type)
                    if len(recent_errors) >= 2 and recent_errors[-1] == recent_errors[-2] and not had_distillation_query:
                        anomalies.append(DetectedAnomaly(
                            category=AnomalyCategory.ERROR_LOOP,
                            severity=AnomalySeverity.HIGH,
                            title=f"Error Loop: Repeated '{err_type}' Without Distillation",
                            description=f"Error pattern '{err_type}' occurred consecutively without querying error solutions database.",
                            raw_evidence=content_str[:250].replace("\n", " ").strip(),
                            suggested_fix_summary=f"Query dnk_query_error_solutions(error_text='{err_type}') immediately instead of repeated trial-and-error.",
                            target_files=[]
                        ))

        # 2. Check Stderr Logs if provided
        if stderr_logs:
            if "⚠ Auxiliary title generation failed" in stderr_logs:
                if not any(a.category == AnomalyCategory.MODEL_REASONING for a in anomalies):
                    anomalies.append(DetectedAnomaly(
                        category=AnomalyCategory.MODEL_REASONING,
                        severity=AnomalySeverity.HIGH,
                        title="Auxiliary Title Generation Failure in Stderr",
                        description="Stderr stream reported auxiliary title generation failure.",
                        raw_evidence=stderr_logs[:300].strip(),
                        suggested_fix_summary="Increase reasoning token headroom in core/hermes_agent/agent/title_generator.py.",
                        target_files=["core/hermes_agent/agent/title_generator.py"]
                    ))

        # 3. Budget Breach Check (MASE Invariant: <= 25 calls)
        if total_tool_calls > 25:
            anomalies.append(DetectedAnomaly(
                category=AnomalyCategory.BUDGET_BREACH,
                severity=AnomalySeverity.HIGH,
                title=f"MASE Tool Budget Breached ({total_tool_calls} > 25 calls)",
                description=f"Task executed with {total_tool_calls} tool calls, exceeding the atomic slice limit of 25 calls.",
                raw_evidence=f"Total tool calls: {total_tool_calls}",
                suggested_fix_summary="Decompose task into smaller atomic slices using task_spec_generator or zero_waste_slicer.",
                target_files=["AGENTS.md"]
            ))

        # 3.1 AST Fast-Path Invariant Check (Section 2 Invariant 16)
        if total_search_files >= 3 and not had_ast_symbol_resolve:
            anomalies.append(DetectedAnomaly(
                category=AnomalyCategory.TOOL_LOOP,
                severity=AnomalySeverity.MEDIUM,
                title="Missing AST Fast-Path: Repeated search_files instead of dnk_resolve_symbol",
                description=f"Agent performed {total_search_files} search_files calls without utilizing dnk_resolve_symbol (<20ms pre-indexed AST cache).",
                raw_evidence=f"Total search_files calls: {total_search_files}, dnk_resolve_symbol calls: 0",
                suggested_fix_summary="Invoke dnk_resolve_symbol(symbol=...) for sub-20ms AST symbol resolution instead of scanning files on disk.",
                target_files=[]
            ))

        # 4. False-Compliance Guard (Soup Verification Gate Pattern)
        compliance_phrases = (
            "all tests pass", "all tests passed", "100% green", "всі тести пройшли",
            "тести успішно", "fixed and tested", "verification passed", "passed 100%"
        )
        last_assistant_text = ""
        for txt in reversed(assistant_texts):
            if any(phrase in txt.lower() for phrase in compliance_phrases):
                last_assistant_text = txt
                break

        if last_assistant_text and not had_verification_tool:
            anomalies.append(DetectedAnomaly(
                category=AnomalyCategory.FALSE_COMPLIANCE,
                severity=AnomalySeverity.HIGH,
                title="False-Compliance: Completion Claimed Without Verification",
                description="Assistant claimed tests passed or completion, but no test/verification tool was executed.",
                raw_evidence=last_assistant_text[:250].replace("\n", " ").strip(),
                suggested_fix_summary="Execute physical verification command (e.g. pytest or bash scripts/verify_all.sh) before declaring task completion.",
                target_files=[]
            ))

        # 4.1 CI/CD Quality Gate & Evidence Check
        if had_pr_creation_attempt and (not had_verification_tool or unverified_mutations):
            anomalies.append(DetectedAnomaly(
                category=AnomalyCategory.CI_CD_VIOLATION,
                severity=AnomalySeverity.HIGH,
                title="Unverified Pull Request Attempt (CI/CD Quality Gate Breach)",
                description="Agent attempted to create or update a Pull Request without running verification tests or while having unverified file mutations.",
                raw_evidence="PR creation attempted without prior verification passes.",
                suggested_fix_summary="Run python3 scripts/system/generate_evidence.py to verify 100% Green and generate evidence before creating PRs.",
                target_files=["scripts/system/generate_evidence.py", "core/orchestrator/github_fast_path.py"]
            ))

        # Deduplicate anomalies by title
        unique_anomalies: List[DetectedAnomaly] = []
        seen_titles = set()
        for a in anomalies:
            if a.title not in seen_titles:
                seen_titles.add(a.title)
                unique_anomalies.append(a)

        return unique_anomalies

    def extract_task_id(self, user_prompt: str) -> Optional[str]:
        """Extracts canonical task ID from user prompt if present."""
        match = re.search(r"(TASK-DNK-[A-Z0-9_-]+|task_[0-9]{8}_[a-z0-9_]+)", user_prompt, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        return None

    def analyze_trajectory(self, session_data: Dict[str, Any], stderr_logs: Optional[str] = None) -> SessionAuditResult:
        """Full trajectory analysis returning complete telemetry and detected anomalies."""
        messages = session_data.get("messages", [])
        anomalies = self.detect_anomalies(session_data, stderr_logs)

        user_prompt = ""
        assistant_final = ""
        tool_counts: Dict[str, int] = {}
        total_tool_calls = 0

        for mid, role, content, tool_name, tool_calls, ts in messages:
            if role == "user" and not user_prompt:
                user_prompt = str(content or "")
            elif role == "assistant" and not tool_calls:
                assistant_final = str(content or "")
            elif role == "assistant" and tool_calls:
                try:
                    tcs = json.loads(tool_calls) if isinstance(tool_calls, str) else tool_calls
                    for tc in tcs:
                        total_tool_calls += 1
                        tool_name = tc.get("name") or (tc.get("function", {}).get("name") if isinstance(tc.get("function"), dict) else "unknown")
                        tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
                except Exception:
                    pass

        start_t = _parse_timestamp_to_epoch(session_data.get("started_at"))
        end_t_raw = session_data.get("ended_at")
        end_t = _parse_timestamp_to_epoch(end_t_raw) if end_t_raw else start_t
        duration = max(end_t - start_t, 0.0)

        # Efficiency calculation: deductions for anomalies and tool bloat
        penalty = len(anomalies) * 15.0
        if total_tool_calls > 25:
            penalty += (total_tool_calls - 25) * 2.0
        efficiency_pct = max(round(100.0 - penalty, 1), 10.0)

        task_id = self.extract_task_id(user_prompt)

        return SessionAuditResult(
            session_id=session_data["session_id"],
            task_id=task_id,
            agent_name=self.agent_name,
            started_at=start_t,
            ended_at=end_t,
            duration_sec=round(duration, 1),
            total_messages=len(messages),
            total_tool_calls=total_tool_calls,
            tool_breakdown=tool_counts,
            anomalies=anomalies,
            efficiency_pct=efficiency_pct,
            user_prompt_preview=user_prompt[:300].replace("\n", " ").strip(),
            assistant_final_preview=assistant_final[:300].replace("\n", " ").strip(),
        )

    def synthesize_self_heal_task_spec(self, audit: SessionAuditResult) -> Optional[Path]:
        """
        Synthesizes a standardized, production-grade Self-Healing Task Specification (v2.5)
        specifically targeted for dnk_dev_fullstack (The System Doctor).
        """
        if not audit.anomalies:
            return None

        self.self_heal_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        time_str = datetime.datetime.now().strftime("%H%M%S")
        task_id = f"TASK-DNK-SELFHEAL-{date_str}-{time_str}"
        task_file = self.self_heal_dir / f"{task_id}.md"

        cur_depth = self.get_session_recursion_depth(audit.session_id)
        next_depth = cur_depth + 1
        audit.recursion_depth = cur_depth


        # Determine dominant target domain & files
        all_targets = set()
        for a in audit.anomalies:
            for tf in a.target_files:
                if tf and not tf.startswith("~"):
                    all_targets.add(tf)
        target_files_list = sorted(list(all_targets)) or ["core/hermes_agent/agent/title_generator.py"]

        domain = "core/hermes_agent"
        if any("router" in f or "apps/api" in f for f in target_files_list):
            domain = "apps/api"
        elif any("apps/web" in f for f in target_files_list):
            domain = "apps/web"

        # Construct markdown content adhering to GERYCH_TASK_TEMPLATE.md v2.5
        anomalies_summary = "\n\n".join([
            f"### ⚠️ {i+1}. {a.title} (`{a.category.value}` - {a.severity.value})\n"
            f"- **Опис**: {a.description}\n"
            f"- **Лог / Стек**: ```text\n{re.sub(r'/Users/[^/\s]+', '$HOME', a.raw_evidence)}\n```\n"
            f"- **Пропоноване лікування**: {a.suggested_fix_summary}\n"
            f"- **Цільові файли**: {', '.join([f'`{f}`' for f in a.target_files]) or 'N/A'}"
            for i, a in enumerate(audit.anomalies)
        ])

        target_manifest = "\n".join([
            f"| `[MODIFY]` | `{f}` | Системне виправлення дефекту та підвищення стійкості |"
            for f in target_files_list
        ])

        content = f"""<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs/plans/self_heal/{task_id}.md"
# purpose: "Автономна задача самолікування системи (Self-Healing) після сесії {audit.session_id}."
# canonical_source: true
# alters_files: {json.dumps(target_files_list)}
# triggers_tasks: []
# status: "Active"
# version: "2.5.0"
# updated_at: "{datetime.datetime.now().strftime('%Y-%m-%d')}"
# author: "Session Sentinel (Shadow Auditor) & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---
-->

# 🏥 САМОЛІКУВАННЯ СИСТЕМИ: {audit.anomalies[0].title}

> **Автономна детекція від Session Sentinel (`gerych_auditor`)**
> Під час виконання сесії `{audit.session_id}` виявлено {len(audit.anomalies)} критичних або алгоритмічних дефектів.
> Ця задача призначена для агента-розробника ядра (`dnk_dev_fullstack`), щоб відновити 100% стабільність системи та запобігти повторенню дефектів.

---

## 🎯 Task Header & Metadata

- **Task ID**: `{task_id}`
- **Title**: `[Self-Heal] {audit.anomalies[0].title}`
- **Domain / Bounded Context**: `{domain}`
- **Primary Executor**: `dnk_dev_fullstack` (System Doctor & Fullstack Lead)
- **Collaborating Swarm Agents**: `gerych_auditor`, `dnk_scones_memory`
- **Execution Mode**: `MUTATION (Core System & Algorithm Patching)`
- **Estimated Complexity**: `P1 High`
- **Origin Session ID**: `{audit.session_id}`
- **Recursion Depth**: `{next_depth}`

---

## ⚡ Zero-Waste Execution Contract

| Параметр | Вимога | Призначення |
| :--- | :--- | :--- |
| **Max Tool Calls** | **≤ 15 tool calls** | Швидкий точковий патч без зайвої розвідки. |
| **Virtualenv SSOT** | `.venv/bin/python3` та `.venv/bin/pytest` | Жодних системних інтерпретаторів. |
| **Path Invariant** | **Тільки відносні шляхи (`./`, `../`)** | 0 абсолютних шляхів `/Users/...`. |
| **MRH Invariant** | Обов'язковий MRH заголовок | `DNK-STD-0075` комплаєнс. |
| **Quality Gate** | **100% Green Pytest Suite** | Регресійне тестування перед фіксацією. |

---

## 💡 1. Problem Statement & Raw Evidence

{anomalies_summary}

---

## 🗺️ 2. Targeted File Manifest

| Дія | Відносний шлях | Відповідальність та ключові сутності |
| :--- | :--- | :--- |
{target_manifest}

---

## 🧩 3. Mandatory Atomic Slices (MASE)

### 🔹 Slice 1: Core System Patching
- **Ціль**: Усунути кореневу причину помилки в цільових модулях, збільшити ліміти токенів або додати безпечний fallback.
- **Цільові файли**: `{', '.join(target_files_list)}`
- **Команда перевірки**:
  ```bash
  .venv/bin/pytest tests/verification/test_*.py -v
  ```
- **Бюджет**: ≤ 12 tool calls.

### 🔹 Slice 2: Evidence & SCONES Memory Confirmation
- **Ціль**: Перевірити відсутність регресій та оновити базу уроків.
- **Команда перевірки**:
  ```bash
  python3 scripts/system/session_sentinel.py --audit-latest
  ```
- **Бюджет**: ≤ 5 tool calls.

---

## ✅ 4. Definition of Done (DoD)

- [ ] Всі виявлені аномалії усунуто в коді цільових файлів.
- [ ] 0 абсолютних шляхів у змінених файлах.
- [ ] Тести проходять на 100% Green.
- [ ] Звіт передано ментору Antigravity та зафіксовано в git.
"""
        self.atomic_write(task_file, content)
        audit.self_heal_task_path = str(task_file.relative_to(self.hub_root))
        return task_file

    def enqueue_to_canvas(self, audit: SessionAuditResult, task_file: Optional[Path]) -> Optional[str]:
        """
        Inserts a new NodeTask into the DAG Canvas (NodeTaskPersistenceManager)
        under project 'dnk_core', making the self-healing task immediately visible.
        """
        if not audit.anomalies:
            return None

        try:
            from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager
            from services.dnk_node_tasks.models import NodeItem, NodeType, ExecutionStage, NodeStatus
        except ImportError:
            return None

        manager = NodeTaskPersistenceManager.get_instance()
        graph = manager.load_graph()

        node_id = f"task-selfheal-{int(datetime.datetime.now().timestamp() * 1000) % 1000000:06d}"
        first_anomaly = audit.anomalies[0]
        severity_priority = "critical" if any(a.severity == AnomalySeverity.CRITICAL for a in audit.anomalies) else "high"

        task_link = audit.self_heal_task_path or ""
        desc = (
            f"🏥 Auto-generated Self-Healing Task from Session `{audit.session_id}`.\n"
            f"Detected Anomalies: {len(audit.anomalies)} issues ({first_anomaly.title}).\n"
            f"Spec: [{Path(task_link).name}]({task_link})"
        )

        now_iso = datetime.datetime.now().isoformat()
        node = NodeItem(
            id=node_id,
            title=f"🏥 [Self-Heal] {first_anomaly.title[:65]}",
            description=desc,
            node_type=NodeType.TASK,
            stage=ExecutionStage.READY,
            status=NodeStatus.READY,
            progress=0.0,
            assigned_agent="dnk_dev_fullstack",
            target_module="core",
            target_files=[a.target_files[0] for a in audit.anomalies if a.target_files] or ["core/hermes_agent"],
            acceptance_criteria=[
                f"Fix defect: {a.title}" for a in audit.anomalies
            ] + ["100% Green Pytest passing"],
            tags=["self_heal", "system_doctor", "auto_generated"],
            priority=severity_priority,
            project_id="dnk_core",
            created_at=now_iso,
            updated_at=now_iso
        )

        graph.nodes[node_id] = node
        manager.save_graph(graph)
        audit.canvas_node_id = node_id
        return node_id

    def persist_scones_lessons(self, audit: SessionAuditResult):
        """Saves distilled lessons from anomalies into SCONES memory."""
        if not audit.anomalies:
            return

        self.scones_dir.mkdir(parents=True, exist_ok=True)
        all_lessons = []
        if self.lessons_file.exists():
            try:
                all_lessons = json.loads(self.lessons_file.read_text(encoding="utf-8"))
            except Exception:
                all_lessons = []

        existing_rules = {item.get("rule") for item in all_lessons}
        now_iso = datetime.datetime.now().isoformat()

        for a in audit.anomalies:
            rule_text = a.suggested_fix_summary
            if rule_text and rule_text not in existing_rules:
                all_lessons.append({
                    "session_id": audit.session_id,
                    "created_at": now_iso,
                    "category": a.category.value,
                    "observation": a.title,
                    "rule": rule_text
                })
                existing_rules.add(rule_text)

        if len(all_lessons) > 50:
            all_lessons = all_lessons[-50:]

        self.atomic_write(self.lessons_file, json.dumps(all_lessons, indent=2, ensure_ascii=False))

    def generate_markdown_audit_report(self, audit: SessionAuditResult) -> Path:
        """Generates structured DNK-MRH audit report in docs/audit/sessions/."""
        self.audit_reports_dir.mkdir(parents=True, exist_ok=True)
        sid = audit.session_id
        report_path = self.audit_reports_dir / f"AUDIT_{sid}.md"


        anomalies_md = "\n".join([
            f"- **[{a.category.value} - {a.severity.value}]**: {a.title}\n  *Fix*: {a.suggested_fix_summary}"
            for a in audit.anomalies
        ]) or "None (Clean execution)."

        tool_breakdown_md = "\n".join([
            f"  - `{k}`: {v}" for k, v in audit.tool_breakdown.items()
        ]) or "  - None"

        content = f"""<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/audit/sessions/AUDIT_{sid}.md"
purpose: "Autonomous Post-Session Audit for Session {sid} by Session Sentinel."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Active"
version: "1.0.0"
updated_at: "{datetime.datetime.now().strftime('%Y-%m-%d')}"
author: "Session Sentinel & Gerych Auditor"
--- END DNK-MRH-HEADER --- -->

# 🛡️ Session Sentinel: Post-Session Audit Report

- **Session ID**: `{sid}`
- **Task ID**: `{audit.task_id or 'N/A'}`
- **Agent**: `{audit.agent_name}`
- **Duration**: {audit.duration_sec}s
- **Efficiency Score**: **{audit.efficiency_pct}%**
- **Self-Healing Task**: {f'`{audit.self_heal_task_path}`' if audit.self_heal_task_path else 'None (System Stable)'}
- **Canvas Node**: {f'`{audit.canvas_node_id}`' if audit.canvas_node_id else 'None'}

---

## 📊 1. Execution Telemetry

| Metric | Value |
|--------|-------|
| **Total Messages** | {audit.total_messages} |
| **Total Tool Calls** | {audit.total_tool_calls} |
| **Anomalies Detected** | {len(audit.anomalies)} |
| **Tool Efficiency** | {audit.efficiency_pct}% |

### Tool Breakdown:
{tool_breakdown_md}

---

## 🧬 2. Detected Anomalies & Defect Telemetry

{anomalies_md}

---

## 🔍 3. Sentinel Verdict

{"✅ **PASSED**: Execution completed cleanly with zero critical defects." if not audit.anomalies else f"⚠️ **SELF-HEALING REQUIRED**: Detected {len(audit.anomalies)} anomalies. Self-healing task dispatched to `dnk_dev_fullstack`."}
"""
        self.atomic_write(report_path, content)
        audit.audit_report_path = str(report_path.relative_to(self.hub_root))
        return report_path

    def get_session_recursion_depth(self, session_id: str, session_data: Optional[Dict[str, Any]] = None) -> int:
        """
        Determines the recursion depth of a given session.
        1. Checks data/self_heal_lineage.json for recorded depth of session_id.
        2. If not recorded, scans session messages/prompt for depth indicators.
        3. Defaults to 0 (root session).
        """
        if self.lineage_file.exists():
            try:
                data = json.loads(self.lineage_file.read_text(encoding="utf-8"))
                sessions = data.get("sessions", {})
                if session_id in sessions:
                    return int(sessions[session_id].get("depth", 0))
            except Exception:
                pass

        if not session_data and session_id:
            session_data = self.fetch_session_data(session_id)

        if session_data:
            messages = session_data.get("messages", [])
            for msg in messages:
                if isinstance(msg, (tuple, list)) and len(msg) >= 3:
                    content = str(msg[2] or "")
                elif isinstance(msg, dict):
                    content = str(msg.get("content", ""))
                else:
                    content = str(msg or "")
                m = re.search(r"Self-Heal Autopilot Depth (\d+)/(\d+)", content)
                if m:
                    return int(m.group(1))
                m2 = re.search(r"Recursion Depth\*?:\s*`?(\d+)`?", content)
                if m2:
                    return int(m2.group(1))
        return 0

    def record_lineage(
        self,
        session_id: str,
        task_id: str,
        depth: int,
        parent_session_id: Optional[str] = None,
        agent: str = "dnk_dev_fullstack",
        status: str = "dispatched"
    ) -> None:
        """
        Records the lineage chain in data/self_heal_lineage.json to ensure recursive loop prevention.
        """
        try:
            self.lineage_file.parent.mkdir(parents=True, exist_ok=True)
            data = {"sessions": {}, "tasks": {}}
            if self.lineage_file.exists():
                try:
                    data = json.loads(self.lineage_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

            now_iso = datetime.datetime.now().isoformat()
            data.setdefault("sessions", {})[session_id] = {
                "depth": depth,
                "task_id": task_id,
                "parent_session_id": parent_session_id,
                "agent": agent,
                "status": status,
                "updated_at": now_iso
            }
            data.setdefault("tasks", {})[task_id] = {
                "depth": depth,
                "parent_session_id": parent_session_id,
                "session_id": session_id,
                "agent": agent,
                "status": status,
                "updated_at": now_iso
            }
            self.atomic_write(self.lineage_file, json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Failed to record lineage: {e}")

    def lookup_scones_remedy(self, text: str) -> Optional[Dict[str, Any]]:
        """Look up known distilled fixes from SCONES error knowledge base."""
        distill_file = self.hub_root / "docs" / "scones" / "error_distillations.json"
        if not distill_file.exists():
            return None
        try:
            with open(distill_file, "r", encoding="utf-8") as f:
                kb = json.load(f)
            for item in kb:
                pat = item.get("pattern", "")
                if pat and re.search(pat, text, re.IGNORECASE):
                    return item
        except Exception as e:
            logger.warning(f"Failed to query SCONES distillations: {e}")
        return None

    def dispatch_self_heal(self, audit: SessionAuditResult, max_recursion_depth: int = 2) -> Dict[str, Any]:
        """
        Autonomous closed-loop dispatch of self-healing task via dnk_swarm_dispatch
        with strict recursion depth control (Circuit Breaker) and SCONES distilled remedy injection.
        """
        if not audit.anomalies or not audit.self_heal_task_path:
            return {"status": "skipped", "reason": "no_anomalies_or_task"}

        cur_depth = self.get_session_recursion_depth(audit.session_id)
        audit.recursion_depth = cur_depth

        # Circuit Breaker Check
        if cur_depth >= max_recursion_depth:
            audit.dispatch_status = "recursion_depth_exceeded"
            logger.warning(
                f"🛑 [Self-Heal Circuit Breaker] Max recursion depth ({max_recursion_depth}) reached for session {audit.session_id}. "
                f"Current depth: {cur_depth}. Halting auto-dispatch."
            )
            breaker_alert = DetectedAnomaly(
                category=AnomalyCategory.ERROR_LOOP,
                severity=AnomalySeverity.CRITICAL,
                title=f"Self-Heal Recursion Limit Reached ({cur_depth}/{max_recursion_depth})",
                description=(
                    f"Session {audit.session_id} has reached maximum allowed self-healing recursion depth ({max_recursion_depth}). "
                    f"Auto-dispatch halted to prevent an infinite loop. Antigravity supervisor escalation required."
                ),
                raw_evidence=f"cur_depth={cur_depth}, max_depth={max_recursion_depth}, origin_session={audit.session_id}",
                suggested_fix_summary="Inspect defect root cause manually or adjust max_recursion_depth.",
                target_files=[audit.self_heal_task_path] if audit.self_heal_task_path else []
            )
            audit.anomalies.append(breaker_alert)
            self.write_in_flight_alerts(audit.session_id, [breaker_alert])
            return {
                "status": "blocked",
                "reason": "max_recursion_depth_reached",
                "depth": cur_depth,
                "max_depth": max_recursion_depth
            }

        next_depth = cur_depth + 1
        first_anomaly = audit.anomalies[0]

        # Intelligent agent routing based on anomaly category
        if first_anomaly.category in (
            AnomalyCategory.TEST_FAILURE,
            AnomalyCategory.CI_CD_VIOLATION,
            AnomalyCategory.FALSE_COMPLIANCE,
            AnomalyCategory.AUTH_ERROR,
        ):
            target_agent = "gerych_auditor"
        else:
            target_agent = "dnk_dev_fullstack"

        # SCONES Knowledge Retrieval for 1-Click Distilled Remedy
        remedy = self.lookup_scones_remedy(f"{first_anomaly.title}\n{first_anomaly.description}\n{first_anomaly.raw_evidence}")
        remedy_hint = f" [SCONES Fix: {remedy.get('solution', '')[:60]}...]" if remedy else ""

        all_targets = set()
        for a in audit.anomalies:
            for tf in a.target_files:
                if tf and not tf.startswith("~"):
                    all_targets.add(tf)
        target_files_list = sorted(list(all_targets))

        task_desc = (
            f"🏥 [Self-Heal Autopilot Depth {next_depth}/{max_recursion_depth}] "
            f"Fix detected anomalies for session {audit.session_id}: {first_anomaly.title}.{remedy_hint} "
            f"Spec: {audit.self_heal_task_path}"
        )
        params = {
            "task_spec_path": audit.self_heal_task_path,
            "recursion_depth": next_depth,
            "max_recursion_depth": max_recursion_depth,
            "parent_session_id": audit.session_id,
            "target_files": target_files_list,
            "anomalies_count": len(audit.anomalies),
            "scones_remedy": remedy
        }

        try:
            from core.hermes_agent.tools.dnk_swarm_tool import dnk_swarm_dispatch
            res_raw = dnk_swarm_dispatch(
                agent=target_agent,
                task_description=task_desc,
                workspace_id="ws-alpha-001",
                parameters=params
            )
            res_data = json.loads(res_raw) if isinstance(res_raw, str) else res_raw
            dispatch_status = "dispatched" if res_data.get("status") in ["dispatched", "success"] else res_data.get("status", "unknown")
        except Exception as e:
            logger.error(f"Failed to auto-dispatch self-heal task: {e}")
            res_data = {"error": str(e)}
            dispatch_status = "failed"

        audit.dispatched_agent = target_agent
        audit.dispatch_status = dispatch_status

        task_id = Path(audit.self_heal_task_path).stem if audit.self_heal_task_path else f"TASK-{int(time.time())}"
        self.record_lineage(
            session_id=audit.session_id,
            task_id=task_id,
            depth=next_depth,
            parent_session_id=audit.session_id,
            agent=target_agent,
            status=dispatch_status
        )

        return {
            "status": dispatch_status,
            "depth": next_depth,
            "agent": target_agent,
            "result": res_data
        }

    def run_post_task_pipeline(
        self,
        session_id: Optional[str] = None,
        stderr_logs: Optional[str] = None,
        auto_dispatch: bool = False,
        max_recursion_depth: int = 2
    ) -> Optional[SessionAuditResult]:
        """
        Orchestrates full post-task audit:
        1. Fetch session trajectory
        2. Classify anomalies
        3. Persist lessons to SCONES
        4. Synthesize self-heal task spec
        5. Enqueue to DAG Canvas
        6. Auto-dispatch via dnk_swarm_dispatch if enabled (with recursion control)
        7. Generate markdown audit report
        """
        session_data = self.fetch_session_data(session_id)
        if not session_data:
            return None

        audit = self.analyze_trajectory(session_data, stderr_logs)
        self.persist_scones_lessons(audit)

        if audit.anomalies:
            task_file = self.synthesize_self_heal_task_spec(audit)
            self.enqueue_to_canvas(audit, task_file)
            has_critical = any(a.severity == AnomalySeverity.CRITICAL for a in audit.anomalies)
            should_dispatch = auto_dispatch or has_critical or os.environ.get("DNK_SENTINEL_AUTO_DISPATCH", "").lower() in ("1", "true", "yes")
            if should_dispatch:
                self.dispatch_self_heal(audit, max_recursion_depth=max_recursion_depth)

        self.generate_markdown_audit_report(audit)
        return audit

    def write_in_flight_alerts(self, session_id: str, alerts: List[DetectedAnomaly]) -> None:
        """
        In-Flight Telemetry: Saves real-time warning alerts for external watchers or pre-tool hooks.
        """
        if not alerts:
            return
        payload = {
            "session_id": session_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "alert_count": len(alerts),
            "alerts": [
                {
                    "category": a.category.value,
                    "severity": a.severity.value,
                    "title": a.title,
                    "description": a.description,
                    "suggested_fix": a.suggested_fix_summary
                }
                for a in alerts
            ]
        }
        self.atomic_write(self.alerts_file, json.dumps(payload, indent=2, ensure_ascii=False))

    def poll_in_flight(self, session_id: Optional[str] = None, last_seen_msg_id: int = 0) -> Tuple[int, List[DetectedAnomaly]]:
        """
        In-Flight Watcher (from Soup Live Watchdog pattern):
        Incrementally queries newly appended messages in the active session and detects anomalies live.
        Returns: (new_last_seen_msg_id, newly_detected_anomalies)
        """
        conn = self._get_db_connection()
        if not conn:
            return last_seen_msg_id, []

        try:
            cur = conn.cursor()
            if not session_id:
                cur.execute("SELECT id FROM sessions ORDER BY started_at DESC LIMIT 1")
                row = cur.fetchone()
                if not row:
                    return last_seen_msg_id, []
                session_id = row[0]

            cur.execute(
                """
                SELECT id, role, content, tool_name, tool_calls, created_at
                FROM messages
                WHERE session_id = ? AND id > ?
                ORDER BY id ASC
                """,
                (session_id, last_seen_msg_id)
            )
            rows = cur.fetchall()
            if not rows:
                return last_seen_msg_id, []

            new_last_id = max(r[0] for r in rows)
            anomalies = self.detect_anomalies({"session_id": session_id, "messages": rows})
            if anomalies:
                self.write_in_flight_alerts(str(session_id or "unknown"), anomalies)

            return new_last_id, anomalies
        except Exception:
            return last_seen_msg_id, []
        finally:
            conn.close()

    def reconcile_orphaned_sessions(self, max_idle_seconds: float = 3600.0) -> List[SessionAuditResult]:
        """
        Orphaned Runs Reconciler (from Soup Run Lifecycle pattern):
        Scans for unfinalized sessions whose host process has died or timed out,
        finalizes their state, and runs post-task audit and self-healing triage.
        """
        conn = self._get_db_connection()
        if not conn:
            return []

        reconciled_audits: List[SessionAuditResult] = []
        try:
            cur = conn.cursor()
            # Inspect columns in sessions table
            cur.execute("PRAGMA table_info(sessions)")
            columns = {col[1] for col in cur.fetchall()}
            
            # Select unclosed sessions
            if "ended_at" in columns:
                cur.execute("SELECT id, started_at FROM sessions WHERE ended_at IS NULL")
            else:
                cur.execute("SELECT id, started_at FROM sessions ORDER BY started_at DESC LIMIT 5")

            active_rows = cur.fetchall()
            now_ts = datetime.datetime.now().timestamp()

            for sid, started_at in active_rows:
                # Run post-task pipeline for each orphaned session
                audit = self.run_post_task_pipeline(session_id=sid)
                if audit:
                    reconciled_audits.append(audit)

            # Close ended_at if column exists
            if "ended_at" in columns and active_rows:
                now_iso = datetime.datetime.now().isoformat()
                for sid, _ in active_rows:
                    try:
                        cur.execute("UPDATE sessions SET ended_at = ? WHERE id = ? AND ended_at IS NULL", (now_iso, sid))
                    except Exception:
                        pass
                conn.commit()

        except Exception:
            pass
        finally:
            conn.close()

        return reconciled_audits

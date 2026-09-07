# --- DNK-MRH-HEADER ---
# mrh_id: "core/accounting_engine.py"
# purpose: "Financial-Technical Accounting Engine (cost/token telemetry) (Gerych Mentorship Framework v3.0)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
import json
import tempfile
import stat
from typing import Dict, Any, List, Optional
import time
from core.atomic_store import atomic_json_read, atomic_json_write, atomic_json_update
try:
    from langfuse import Langfuse
except ImportError:
    Langfuse = None

class AccountingEngine:
    """
    AccountingEngine tracks cost telemetry: tokens_in, tokens_out, cost_usd,
    execution duration, and success rates. It generates aggregated metrics
    and ROI computations conforming to the Gerych Framework.
    """
    def __init__(self, log_path: str = "telemetry/accounting_log.json", max_records: int = 5000):
        self.log_path = log_path
        self.max_records = max_records
        dir_path = os.path.dirname(self.log_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        self._initialize_log()
        
        # Initialize Langfuse SDK
        self.langfuse = None
        try:
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
            secret_key = os.getenv("LANGFUSE_SECRET_KEY")
            host = os.getenv("LANGFUSE_HOST", "http://localhost:4000")
            if public_key and secret_key and Langfuse is not None:
                self.langfuse = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=host
                )
        except Exception:
            pass

    def _initialize_log(self) -> None:
        """Ensures telemetry file exists with correct permissions (0600)."""
        if not os.path.exists(self.log_path):
            self._save_records([])
            try:
                os.chmod(self.log_path, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass

    def _read_records(self) -> List[Dict[str, Any]]:
        """Reads telemetry list securely with shared lock."""
        data = atomic_json_read(self.log_path, default=[])
        return data if isinstance(data, list) else []

    def _save_records(self, records: List[Dict[str, Any]]) -> None:
        """Writes telemetry atomically with exclusive lock."""
        atomic_json_write(self.log_path, records)

    def log_workflow_telemetry(self, project_id: str, task_id: str, tokens_in: int, tokens_out: int,
                               cost_usd: float, duration_ms: int, success: bool,
                               token_savings_pct: float = 0.0, dev_time_saved_pct: float = 0.0,
                               estimated_usd_saved: float = 0.0, notes: str = "") -> Dict[str, Any]:
        """Logs an individual task execution event to the telemetry database."""
        record = {
            "timestamp": time.time(),
            "project_id": project_id,
            "task_id": task_id,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd,
            "duration_ms": duration_ms,
            "success": success,
            "token_savings_pct": token_savings_pct,
            "dev_time_saved_pct": dev_time_saved_pct,
            "estimated_usd_saved": estimated_usd_saved,
            "notes": notes
        }
        
        def updater(records):
            if not isinstance(records, list):
                records = []
            records.append(record)
            if len(records) > self.max_records:
                records = records[-self.max_records:]
            return records

        atomic_json_update(self.log_path, updater, default=[])

        # Log to local telemetry engine
        try:
            from core.local_telemetry import local_telemetry
            local_telemetry.log_metric("task_cost_usd", cost_usd, [project_id, task_id])
            local_telemetry.log_step("accounting", f"Logged telemetry for task {task_id}")
        except Exception:
            pass

        # Log trace and generation to Langfuse as well (asynchronous and non-blocking)
        if self.langfuse:
            try:
                trace = self.langfuse.trace(
                    name=f"Workflow_{task_id}",
                    id=f"trace_{task_id}_{int(time.time())}",
                    project_id=project_id,
                    metadata={
                        "task_id": task_id,
                        "notes": notes,
                        "token_savings_pct": token_savings_pct,
                        "dev_time_saved_pct": dev_time_saved_pct,
                        "estimated_usd_saved": estimated_usd_saved
                    }
                )
                trace.generation(
                    name=f"Execution_{task_id}",
                    input={"task_id": task_id, "notes": notes},
                    output={"success": success},
                    usage={
                        "input": tokens_in,
                        "output": tokens_out,
                        "total": tokens_in + tokens_out,
                        "unit": "TOKENS"
                    }
                )
            except Exception:
                pass

        return record

    def get_aggregated_metrics(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates aggregated telemetry statistics, ROI, and total savings."""
        records = self._read_records()
        if project_id:
            records = [r for r in records if r["project_id"] == project_id]

        if not records:
            return {
                "total_runs": 0,
                "success_rate": 100.0,
                "total_tokens_in": 0,
                "total_tokens_out": 0,
                "total_cost_usd": 0.0,
                "avg_duration_ms": 0.0,
                "total_usd_saved": 0.0,
                "avg_token_savings_pct": 0.0
            }

        total_runs = len(records)
        successful_runs = sum(1 for r in records if r["success"])
        success_rate = (successful_runs / total_runs) * 100.0
        
        total_tokens_in = sum(r["tokens_in"] for r in records)
        total_tokens_out = sum(r["tokens_out"] for r in records)
        total_cost_usd = sum(r["cost_usd"] for r in records)
        total_duration_ms = sum(r["duration_ms"] for r in records)
        avg_duration_ms = total_duration_ms / total_runs
        
        total_usd_saved = sum(r["estimated_usd_saved"] for r in records)
        avg_token_savings_pct = sum(r["token_savings_pct"] for r in records) / total_runs

        return {
            "total_runs": total_runs,
            "success_rate": round(success_rate, 2),
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "total_cost_usd": round(total_cost_usd, 6),
            "avg_duration_ms": round(avg_duration_ms, 2),
            "total_usd_saved": round(total_usd_saved, 2),
            "avg_token_savings_pct": round(avg_token_savings_pct, 2)
        }

# --- DNK-MRH-HEADER ---
# mrh_id: "core/local_telemetry.py"
# purpose: "Autonomous Local Telemetry & Tracing Engine isolating metrics, traces and trajectories."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
import json
import time
import tempfile
import stat
from typing import Dict, Any, List, Optional

class LocalTelemetryEngine:
    """
    Autonomous local bank for tracing, execution trajectories, metrics logging,
    and step diagnostics. Ensuring offline data ownership, compliance, and speed.
    """
    def __init__(self, telemetry_dir: str = "telemetry", logs_dir: str = "logs"):
        self.telemetry_dir = telemetry_dir
        self.logs_dir = logs_dir
        
        # Subdirectories for structural segregation
        self.traces_dir = os.path.join(telemetry_dir, "traces")
        self.trajectories_dir = os.path.join(telemetry_dir, "trajectories")
        self.metrics_dir = os.path.join(telemetry_dir, "metrics")

        # Guarantee physical existence of directories
        os.makedirs(self.traces_dir, exist_ok=True)
        os.makedirs(self.trajectories_dir, exist_ok=True)
        os.makedirs(self.metrics_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def _atomic_append_jsonl(self, file_path: str, record: Dict[str, Any]) -> None:
        """Appends a single JSON dictionary as a line atomically."""
        record["timestamp"] = record.get("timestamp", time.time())
        line = json.dumps(record, ensure_ascii=False) + "\n"
        
        # Open and write with owner-only permissions (0600)
        try:
            fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            pass

    def log_trace(self, task_id: str, tool_calls: List[Dict[str, Any]], 
                  inputs: Dict[str, Any], outputs: Dict[str, Any], 
                  duration_ms: int, cost_usd: float) -> Dict[str, Any]:
        """Logs an execution trace representing a workflow runtime segment."""
        record = {
            "task_id": task_id,
            "tool_calls": tool_calls,
            "inputs": inputs,
            "outputs": outputs,
            "duration_ms": duration_ms,
            "cost_usd": cost_usd
        }
        file_path = os.path.join(self.traces_dir, f"{task_id}_trace.jsonl")
        self._atomic_append_jsonl(file_path, record)
        return record

    def log_trajectory(self, task_id: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Logs the complete agent task trajectory securely as a structured JSON asset."""
        record = {
            "task_id": task_id,
            "timestamp": time.time(),
            "steps": steps
        }
        file_path = os.path.join(self.trajectories_dir, f"{task_id}_trajectory.json")
        dir_path = os.path.dirname(file_path)
        
        # Atomic Write protocol
        with tempfile.NamedTemporaryFile("w", dir=dir_path, suffix=".tmp", delete=False, encoding="utf-8") as temp_file:
            json.dump(record, temp_file, indent=2, ensure_ascii=False)
            temp_file_name = temp_file.name

        try:
            os.chmod(temp_file_name, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

        os.replace(temp_file_name, file_path)
        return record

    def log_metric(self, name: str, value: float, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Logs technical performance, latency, or token-count metrics."""
        record = {
            "name": name,
            "value": value,
            "tags": tags or []
        }
        file_path = os.path.join(self.metrics_dir, f"{name}_metrics.jsonl")
        self._atomic_append_jsonl(file_path, record)
        return record

    def log_step(self, module: str, message: str, level: str = "INFO") -> Dict[str, Any]:
        """Logs granular microservice, compiler, or step events asynchronously."""
        record = {
            "module": module,
            "message": message,
            "level": level.upper()
        }
        file_path = os.path.join(self.logs_dir, "step_logs.jsonl")
        self._atomic_append_jsonl(file_path, record)
        return record

    def read_traces(self, task_id: str) -> List[Dict[str, Any]]:
        """Reads and returns all parsed trace segments for a specific task."""
        file_path = os.path.join(self.traces_dir, f"{task_id}_trace.jsonl")
        if not os.path.exists(file_path):
            return []
        
        records = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            pass
        return records

    def read_trajectory(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Reads the pristine execution trajectory of a given task."""
        file_path = os.path.join(self.trajectories_dir, f"{task_id}_trajectory.json")
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

local_telemetry = LocalTelemetryEngine()

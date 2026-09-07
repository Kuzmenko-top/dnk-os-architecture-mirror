# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/subagent_sandbox.py"
# purpose: "Structured Subagent Sandbox, Environment Preparation, and Zero-Loss Artifact Handshake Protocol."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK Swarm (Gerych Prime & Swarm Architect)"
# --- END DNK-MRH-HEADER ---

import os
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("dnk_subagent_sandbox")


@dataclass
class SubagentContext:
    task_id: str
    agent_id: str
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)
    target_files: List[str] = field(default_factory=list)
    input_artifact_path: Optional[Path] = None
    output_artifact_path: Optional[Path] = None
    trace_id: str = ""
    timeout_seconds: int = 120


def prepare_subagent_environment(
    agent: str,
    task_id: str,
    action: str,
    payload: Dict[str, Any],
    trace_id: str,
    hub_root: Path,
    timeout_seconds: int = 120,
) -> Tuple[Dict[str, str], Path, Path]:
    """
    Sets up isolated execution environment and input artifact contract for a subagent worker.
    Returns:
        (env_overrides, input_artifact_path, output_artifact_path)
    """
    artifact_dir = hub_root / "data" / "swarm_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    input_artifact_path = artifact_dir / f"{task_id}_input.json"
    output_artifact_path = artifact_dir / f"{task_id}_output.json"

    target_files = payload.get("target_files", [])

    input_data = {
        "task_id": task_id,
        "agent": agent,
        "action": action,
        "payload": payload,
        "target_files": target_files,
        "timeout_seconds": timeout_seconds,
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_artifact": str(input_artifact_path.relative_to(hub_root)),
        "output_artifact": str(output_artifact_path.relative_to(hub_root)),
    }

    try:
        input_artifact_path.write_text(
            json.dumps(input_data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception as e:
        logger.warning(f"Failed to write input artifact to {input_artifact_path}: {e}")

    env = os.environ.copy()
    env["DNK_SWARM_WORKER"] = "1"
    env["DNK_AGENT_ID"] = agent
    env["DNK_TASK_ID"] = task_id
    env["DNK_TRACE_ID"] = trace_id
    env["DNK_INPUT_ARTIFACT"] = str(input_artifact_path)
    env["DNK_OUTPUT_ARTIFACT"] = str(output_artifact_path)
    env["DNK_HUB_ROOT"] = str(hub_root)

    return env, input_artifact_path, output_artifact_path


def get_subagent_context() -> Optional[SubagentContext]:
    """
    Retrieves execution context inside a running subagent worker process from environment & artifact.
    """
    if os.environ.get("DNK_SWARM_WORKER") != "1":
        return None

    agent_id = os.environ.get("DNK_AGENT_ID", "unknown_agent")
    task_id = os.environ.get("DNK_TASK_ID", "unknown_task")
    trace_id = os.environ.get("DNK_TRACE_ID", "")

    input_path_str = os.environ.get("DNK_INPUT_ARTIFACT")
    output_path_str = os.environ.get("DNK_OUTPUT_ARTIFACT")

    input_path = Path(input_path_str) if input_path_str else None
    output_path = Path(output_path_str) if output_path_str else None

    action = "execute"
    payload: Dict[str, Any] = {}
    target_files: List[str] = []
    timeout_seconds = 120

    if input_path and input_path.exists():
        try:
            raw = json.loads(input_path.read_text(encoding="utf-8"))
            action = raw.get("action", action)
            payload = raw.get("payload", {})
            target_files = raw.get("target_files", [])
            timeout_seconds = raw.get("timeout_seconds", 120)
        except Exception as e:
            logger.warning(f"Error reading subagent input artifact {input_path}: {e}")

    return SubagentContext(
        task_id=task_id,
        agent_id=agent_id,
        action=action,
        payload=payload,
        target_files=target_files,
        input_artifact_path=input_path,
        output_artifact_path=output_path,
        trace_id=trace_id,
        timeout_seconds=timeout_seconds,
    )


def emit_subagent_output(
    status: str,
    data: Dict[str, Any],
    modified_files: Optional[List[str]] = None,
    summary: str = "",
) -> Optional[Path]:
    """
    Writes structured output from subagent to the specified output artifact file.
    """
    output_path_str = os.environ.get("DNK_OUTPUT_ARTIFACT")
    if not output_path_str:
        task_id = os.environ.get("DNK_TASK_ID", f"task_{int(datetime.now(timezone.utc).timestamp())}")
        output_path = Path("data/swarm_artifacts") / f"{task_id}_output.json"
    else:
        output_path = Path(output_path_str)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    result_payload = {
        "task_id": os.environ.get("DNK_TASK_ID", "unknown"),
        "agent_id": os.environ.get("DNK_AGENT_ID", "unknown"),
        "trace_id": os.environ.get("DNK_TRACE_ID", ""),
        "status": status,
        "summary": summary,
        "modified_files": modified_files or [],
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        output_path.write_text(
            json.dumps(result_payload, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return output_path
    except Exception as e:
        logger.error(f"Failed to write subagent output artifact to {output_path}: {e}")
        return None


def harvest_subagent_output(output_artifact_path: Path) -> Dict[str, Any]:
    """
    Harvests and deserializes subagent output artifact.
    """
    if not output_artifact_path.exists():
        return {}

    try:
        return json.loads(output_artifact_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Failed to parse subagent output artifact {output_artifact_path}: {e}")
        return {}

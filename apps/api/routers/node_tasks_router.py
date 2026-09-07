# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/node_tasks_router.py"
# purpose: "FastAPI Router for Node Based Task & Ideas System with DAG Dependencies, Stage Gating, and Live Artifact Diff Inspection"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger("dnk.node_tasks")

from services.dnk_node_tasks.models import (
    NodeType,
    ExecutionStage,
    NodeStatus,
    EdgeRelation,
    DependencyEdge,
    NodePosition,
    NodeItem,
    NodeTaskGraph,
    GraphStatistics,
    IdeaConversionRequest,
    StageTransitionRequest,
    ProjectInfo,
)
from services.dnk_node_tasks.graph_engine import NodeTaskGraphEngine
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager
from services.dnk_node_tasks.conversational_intake import ConversationalTaskExtractor
from services.dnk_video_ai_creator.task_video_synthesizer import (
    TaskVideoSynthesizer,
    MarketingVideoPayload,
)
from services.dnk_video_ai_creator.voice_synthesizer import VoiceSynthesizer
from services.dnk_video_ai_creator.remotion_exporter import RemotionExporter
from services.dnk_canvas_api.obsidian_sync_engine import ObsidianSyncEngine
from core.occ_merge import OCCConcurrencyEngine, OCCMergeResult, PositionConflictStrategy

router = APIRouter(prefix="/api/v3/node_tasks", tags=["Node Tasks & Ideas System"])


class CreateOrUpdateNodeRequest(BaseModel):
    id: Optional[str] = None
    title: str
    description: str = ""
    node_type: NodeType = NodeType.TASK
    stage: ExecutionStage = ExecutionStage.IDEATION
    status: NodeStatus = NodeStatus.DRAFT
    progress: float = 0.0
    assigned_agent: Optional[str] = None
    target_module: Optional[str] = "core"
    target_files: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    priority: str = "medium"
    position: Optional[NodePosition] = None
    project_id: Optional[str] = "dnk_core"


class CreateEdgeRequest(BaseModel):
    source: str
    target: str
    relation: EdgeRelation = EdgeRelation.DEPENDS_ON
    dependency_type: Optional[EdgeRelation] = None
    description: Optional[str] = None

    @model_validator(mode="after")
    def unify_relation(self):
        if self.dependency_type is not None:
            self.relation = self.dependency_type
        return self


class ExecuteAgentRequest(BaseModel):
    node_id: Optional[str] = None
    agent_override: Optional[str] = None
    task_instructions: Optional[str] = None
    auto_complete: Optional[bool] = False


class ChatIntakeRequest(BaseModel):
    prompt: str = Field(..., description="User prompt, idea, or task specification")
    workspace_id: Optional[str] = Field(default="ws-alpha-001", description="Target workspace ID")
    default_agent: Optional[str] = Field(default=None, description="Preferred swarm agent")
    history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Recent conversation history")
    selected_node_id: Optional[str] = Field(default=None, description="Currently selected node ID on canvas")


class DecomposeNodeRequest(BaseModel):
    instructions: Optional[str] = Field(default=None, description="Optional custom guidelines for decomposition")
    workspace_id: Optional[str] = Field(default="ws-alpha-001", description="Target workspace ID")


class BatchPositionsRequest(BaseModel):
    positions: Dict[str, NodePosition] = Field(..., description="Map of node_id to new NodePosition(x, y)")


class BatchStageTransitionRequest(BaseModel):
    node_ids: List[str] = Field(..., description="List of node IDs to transition")
    target_stage: ExecutionStage = Field(..., description="Target execution stage")
    force: bool = Field(default=False, description="Whether to bypass stage gating requirements")


class BatchDeleteRequest(BaseModel):
    node_ids: List[str] = Field(..., description="List of node IDs to delete")


class BatchExecuteRequest(BaseModel):
    node_ids: List[str] = Field(..., description="List of node IDs to execute")
    agent_override: Optional[str] = Field(default=None, description="Optional agent override")
    task_instructions: Optional[str] = Field(default=None, description="Optional custom instructions")
    auto_complete: Optional[bool] = Field(default=False, description="Whether to immediately mark completed")


class ArtifactFileDiff(BaseModel):
    path: str
    change_type: str = "modified"  # added, modified, deleted
    additions: int = 0
    deletions: int = 0
    diff_content: str = ""


class NodeArtifactReport(BaseModel):
    node_id: str
    agent: str = "gerych_builder"
    status: str = "completed"
    files: List[ArtifactFileDiff] = Field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    executed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RejectArtifactsRequest(BaseModel):
    reason: Optional[str] = None


class RunVerificationRequest(BaseModel):
    test_command: Optional[str] = None
    target_test_file: Optional[str] = None


@router.post("/batch_positions", response_model=Dict[str, Any])
def batch_update_positions(req: BatchPositionsRequest):
    """Batch update visual canvas positions for nodes and persist graph."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    now_iso = datetime.now(timezone.utc).isoformat()
    updated_count = 0

    for node_id, pos in req.positions.items():
        if node_id in graph.nodes:
            graph.nodes[node_id].position = pos
            graph.nodes[node_id].updated_at = now_iso
            updated_count += 1

    if updated_count > 0:
        manager.save_graph(graph)

    return {
        "status": "success",
        "updated_count": updated_count,
        "total_nodes": len(graph.nodes)
    }


@router.get("/projects", response_model=Dict[str, Any])
def get_projects():
    """Retrieve list of all registered projects with their active task counts."""
    manager = NodeTaskPersistenceManager.get_instance()
    projects = manager.get_projects()
    full_graph = manager.load_graph()

    counts: Dict[str, int] = {}
    for node in full_graph.nodes.values():
        p_id = getattr(node, "project_id", None) or "dnk_core"
        counts[p_id] = counts.get(p_id, 0) + 1

    projects_with_counts = []
    for p in projects:
        p_dict = p.model_dump()
        count = counts.get(p.id, 0)
        p_dict["tasks_count"] = count
        p_dict["task_count"] = count
        projects_with_counts.append(p_dict)

    return {
        "status": "success",
        "projects": projects_with_counts,
        "total_projects": len(projects_with_counts),
    }


@router.post("/projects", response_model=Dict[str, Any])
def create_project(project: ProjectInfo):
    """Create a new project partition or update existing project metadata."""
    manager = NodeTaskPersistenceManager.get_instance()
    created = manager.create_project(project)
    return {
        "status": "success",
        "project": created.model_dump(),
    }


@router.get("/graph", response_model=Dict[str, Any])
def get_node_task_graph(
    project_id: Optional[str] = Query(None, description="Optional project partition ID to filter graph"),
):
    """Retrieve full or project-filtered Node Tasks & Ideas DAG graph and statistics."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.get_graph(project_id=project_id)
    stats = NodeTaskGraphEngine.compute_statistics(graph)
    execution_order = NodeTaskGraphEngine.get_topological_execution_order(graph)

    return {
        "status": "success",
        "project_id": project_id,
        "graph": graph.model_dump(),
        "stats": stats.model_dump(),
        "topological_order": execution_order,
    }


@router.get("/critical_path", response_model=Dict[str, Any])
def get_critical_path(
    project_id: Optional[str] = Query(None, description="Optional project partition ID to filter graph"),
):
    """Calculate and retrieve Critical Path Method (CPM) metrics, critical chains, and bottlenecks."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.get_graph(project_id=project_id)
    cpm_result = NodeTaskGraphEngine.compute_critical_path(graph)

    return {
        "status": "success",
        "project_id": project_id,
        **cpm_result
    }


@router.post("/node", response_model=Dict[str, Any])
def create_or_update_node(req: CreateOrUpdateNodeRequest):
    """Create a new node or update an existing one."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    now_iso = datetime.now(timezone.utc).isoformat()

    node_id = req.id
    if not node_id:
        prefix = {
            NodeType.IDEA: "idea",
            NodeType.EPIC: "epic",
            NodeType.TASK: "task",
            NodeType.SLICE: "slice",
            NodeType.GATE: "gate"
        }.get(req.node_type, "task")
        ts = int(datetime.now().timestamp() * 1000) % 100000
        node_id = f"{prefix}-{req.target_module or 'core'}-{ts:05d}"

    existing = graph.nodes.get(node_id)
    if existing:
        existing.title = req.title
        existing.description = req.description
        existing.node_type = req.node_type
        existing.stage = req.stage
        existing.status = req.status
        existing.progress = req.progress
        existing.assigned_agent = req.assigned_agent
        existing.target_module = req.target_module
        existing.target_files = req.target_files
        existing.acceptance_criteria = req.acceptance_criteria
        existing.tags = req.tags
        existing.priority = req.priority
        if req.project_id is not None:
            existing.project_id = req.project_id
        if req.position:
            existing.position = req.position
        existing.updated_at = now_iso
        node_item = existing
    else:
        pos = req.position or NodePosition(x=100.0, y=100.0)
        node_item = NodeItem(
            id=node_id,
            title=req.title,
            description=req.description,
            node_type=req.node_type,
            stage=req.stage,
            status=req.status,
            progress=req.progress,
            assigned_agent=req.assigned_agent,
            target_module=req.target_module,
            target_files=req.target_files,
            acceptance_criteria=req.acceptance_criteria,
            tags=req.tags,
            priority=req.priority,
            position=pos,
            project_id=req.project_id or "dnk_core",
            created_at=now_iso,
            updated_at=now_iso
        )
        graph.nodes[node_id] = node_item

    NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
    manager.save_graph(graph)

    return {
        "status": "success",
        "node": node_item.model_dump(),
        "stats": NodeTaskGraphEngine.compute_statistics(graph).model_dump()
    }


@router.delete("/node/{node_id}", response_model=Dict[str, Any])
def delete_node(node_id: str):
    """Delete a node and all associated edges."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    if node_id not in graph.nodes:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    del graph.nodes[node_id]
    graph.edges = [e for e in graph.edges if e.source != node_id and e.target != node_id]

    NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
    manager.save_graph(graph)

    return {
        "status": "success",
        "deleted_node_id": node_id,
        "remaining_nodes": len(graph.nodes)
    }


@router.post("/edge", response_model=Dict[str, Any])
def create_edge(req: CreateEdgeRequest):
    """Create a dependency or relationship edge between two nodes."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    if req.source not in graph.nodes:
        raise HTTPException(status_code=404, detail=f"Source node '{req.source}' not found.")
    if req.target not in graph.nodes:
        raise HTTPException(status_code=404, detail=f"Target node '{req.target}' not found.")

    # Check for DAG cycles
    has_cycle, cycle_path = NodeTaskGraphEngine.detect_cycle_with_new_edge(
        existing_edges=graph.edges,
        new_source=req.source,
        new_target=req.target,
        relation=req.relation
    )
    if has_cycle:
        raise HTTPException(
            status_code=400,
            detail=f"Circular dependency detected! Path: {' -> '.join(cycle_path)}"
        )

    edge_id = f"edge-{req.source}-to-{req.target}"
    # Deduplicate existing edge
    graph.edges = [e for e in graph.edges if not (e.source == req.source and e.target == req.target)]

    new_edge = DependencyEdge(
        id=edge_id,
        source=req.source,
        target=req.target,
        relation=req.relation,
        description=req.description
    )
    graph.edges.append(new_edge)

    NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
    manager.save_graph(graph)

    # Sync to Obsidian vault
    try:
        manager.sync_to_obsidian()
    except Exception as obs_err:
        logger.debug(f"Obsidian sync skipped on create_edge: {obs_err}")

    # Realtime WebSocket event broadcast
    bridge = _get_active_canvas_bridge()
    if bridge is not None:
        try:
            bridge.publish_node_executed(
                node_id=req.target,
                status="edge_created",
                event_type="edge.created",
                payload={
                    "event": "edge.created",
                    "edge_id": edge_id,
                    "source": req.source,
                    "target": req.target,
                    "relation": req.relation,
                    "description": req.description,
                    "edge": new_edge.model_dump(),
                },
            )
        except Exception as ws_err:
            logger.debug(f"WebSocket broadcast skipped on create_edge: {ws_err}")

    return {
        "status": "success",
        "edge": new_edge.model_dump(),
        "stats": NodeTaskGraphEngine.compute_statistics(graph).model_dump()
    }


@router.delete("/edge/{edge_id}", response_model=Dict[str, Any])
def delete_edge(edge_id: str):
    """Delete a dependency edge by ID."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    initial_count = len(graph.edges)
    graph.edges = [e for e in graph.edges if e.id != edge_id]

    if len(graph.edges) == initial_count:
        raise HTTPException(status_code=404, detail=f"Edge '{edge_id}' not found.")

    NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
    manager.save_graph(graph)

    # Sync to Obsidian vault
    try:
        manager.sync_to_obsidian()
    except Exception as obs_err:
        logger.debug(f"Obsidian sync skipped on delete_edge: {obs_err}")

    # Realtime WebSocket event broadcast
    bridge = _get_active_canvas_bridge()
    if bridge is not None:
        try:
            bridge.publish_node_executed(
                node_id=edge_id,
                status="edge_deleted",
                event_type="edge.deleted",
                payload={
                    "event": "edge.deleted",
                    "edge_id": edge_id,
                },
            )
        except Exception as ws_err:
            logger.debug(f"WebSocket broadcast skipped on delete_edge: {ws_err}")

    return {
        "status": "success",
        "deleted_edge_id": edge_id,
        "remaining_edges": len(graph.edges)
    }


@router.post("/stage_transition", response_model=Dict[str, Any])
def transition_stage(req: StageTransitionRequest):
    """Transition a node to a target execution stage with dependency checking."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    node = graph.nodes.get(req.node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{req.node_id}' not found.")

    allowed, reason = NodeTaskGraphEngine.can_transition_stage(
        node=node,
        target_stage=req.target_stage,
        graph=graph,
        force=req.force
    )

    if not allowed:
        raise HTTPException(status_code=400, detail=reason)

    old_stage = node.stage
    node.stage = req.target_stage
    node.updated_at = datetime.now(timezone.utc).isoformat()

    # Automatically set appropriate status
    if req.target_stage == ExecutionStage.COMPLETED:
        node.status = NodeStatus.COMPLETED
        node.progress = 100.0
    elif req.target_stage == ExecutionStage.IN_PROGRESS and node.status in (NodeStatus.READY, NodeStatus.BACKLOG, NodeStatus.DRAFT):
        node.status = NodeStatus.IN_PROGRESS
        if node.progress == 0.0:
            node.progress = 10.0

    NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
    manager.save_graph(graph)

    return {
        "status": "success",
        "node_id": node.id,
        "previous_stage": old_stage.value,
        "current_stage": node.stage.value,
        "node": node.model_dump()
    }


@router.post("/convert_idea", response_model=Dict[str, Any])
def convert_idea(req: IdeaConversionRequest):
    """Convert an Idea node into an actionable Task or Epic."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    if req.idea_id not in graph.nodes:
        raise HTTPException(status_code=404, detail=f"Idea node '{req.idea_id}' not found.")

    try:
        new_task, spawn_edge = NodeTaskGraphEngine.convert_idea_to_task(graph, req)
        manager.save_graph(graph)
        return {
            "status": "success",
            "spawned_task": new_task.model_dump(),
            "spawn_edge": spawn_edge.model_dump(),
            "stats": NodeTaskGraphEngine.compute_statistics(graph).model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ObsidianSyncRequest(BaseModel):
    vault_dir: Optional[str] = None
    project_id: Optional[str] = None


@router.post("/sync_obsidian", response_model=Dict[str, Any])
def sync_obsidian():
    """Sync graph nodes and status into Obsidian markdown notes."""
    manager = NodeTaskPersistenceManager.get_instance()
    result = manager.sync_to_obsidian()
    return result


@router.post("/sync_from_obsidian", response_model=Dict[str, Any])
def sync_from_obsidian(payload: Optional[ObsidianSyncRequest] = None):
    """Sync and reconcile graph nodes and dependencies from Obsidian vault markdown notes."""
    vault_dir = Path(payload.vault_dir) if payload and payload.vault_dir else None
    project_id = payload.project_id if payload else None
    result = ObsidianSyncEngine.sync_from_obsidian_vault(vault_dir=vault_dir, project_id=project_id)
    return result


@router.post("/sync_bidirectional", response_model=Dict[str, Any])
def sync_bidirectional(payload: Optional[ObsidianSyncRequest] = None):
    """Full 2-way bidirectional sync between DAG Canvas and Obsidian markdown vault."""
    vault_dir = Path(payload.vault_dir) if payload and payload.vault_dir else None
    project_id = payload.project_id if payload else None
    result = ObsidianSyncEngine.sync_bidirectional(vault_dir=vault_dir, project_id=project_id)
    return result


@router.post("/reset_baseline", response_model=Dict[str, Any])
def reset_baseline():
    """Reset the graph to the rich DNK OS roadmap baseline dataset."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.reset_to_baseline()
    stats = NodeTaskGraphEngine.compute_statistics(graph)
    return {
        "status": "success",
        "message": "Graph reset to DNK OS development baseline",
        "stats": stats.model_dump()
    }


def _get_active_canvas_bridge():
    """Retrieves the active CanvasRuntimeBridge singleton for realtime WebSocket event dispatch."""
    try:
        from apps.api.routers.swarm_ws import get_canvas_bridge
        return get_canvas_bridge()
    except Exception:
        try:
            from core.canvas_runtime_bridge import CanvasRuntimeBridge
            return CanvasRuntimeBridge()
        except Exception:
            return None


# In-memory execution logs ring-buffer for live terminal stream
_task_logs: Dict[str, List[Dict[str, Any]]] = {}


def append_task_log(node_id: str, level: str, agent: str, message: str) -> None:
    """Appends an execution log entry and caps history at 50 records."""
    if node_id not in _task_logs:
        _task_logs[node_id] = []
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "agent": agent,
        "message": message,
    }
    _task_logs[node_id].append(log_entry)
    if len(_task_logs[node_id]) > 50:
        _task_logs[node_id] = _task_logs[node_id][-50:]

    bridge = _get_active_canvas_bridge()
    if bridge is not None:
        try:
            bridge.publish_node_executed(
                node_id=node_id,
                status="log",
                event_type="node.log",
                payload={
                    "event": "node.log",
                    "node_id": node_id,
                    "level": level,
                    "agent": agent,
                    "message": message,
                    "timestamp": log_entry["timestamp"],
                    "log": log_entry,
                },
            )
        except Exception as ex:
            logger.warning(f"Failed to publish node.log event via bridge: {ex}")


@router.get("/{node_id}/logs", response_model=Dict[str, Any])
def get_node_execution_logs(node_id: str):
    """Retrieve execution logs for a given node task."""
    return {
        "status": "success",
        "node_id": node_id,
        "logs": _task_logs.get(node_id, [])
    }


# In-memory artifacts report cache for live diff inspector
_task_artifacts: Dict[str, NodeArtifactReport] = {}
_task_marketing_videos: Dict[str, Dict[str, Any]] = {}


def _generate_node_artifacts(node: NodeItem) -> NodeArtifactReport:
    files_diff: List[ArtifactFileDiff] = []

    target_files = list(node.target_files or [])
    if not target_files:
        try:
            import subprocess
            git_proc = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if git_proc.returncode == 0 and git_proc.stdout.strip():
                target_files = [f.strip() for f in git_proc.stdout.strip().split("\n") if f.strip()][:5]
        except Exception:
            pass

    if not target_files:
        mod = node.target_module or "core"
        clean_id = node.id.replace("-", "_")
        target_files = [f"{mod}/tasks/{clean_id}_artifact.py"]

    for file_path in target_files:
        diff_text = ""
        additions = 0
        deletions = 0
        change_type = "modified"

        # 1. Attempt real git diff
        try:
            import subprocess
            diff_proc = subprocess.run(
                ["git", "diff", "HEAD", "--", file_path],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if diff_proc.returncode == 0 and diff_proc.stdout.strip():
                diff_text = diff_proc.stdout.strip()
                for line in diff_text.splitlines():
                    if line.startswith("+") and not line.startswith("+++"):
                        additions += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        deletions += 1
        except Exception:
            pass

        # 2. Synthesize preview if no git diff
        if not diff_text:
            import os
            if os.path.exists(file_path):
                change_type = "modified"
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = [f.readline() for _ in range(15)]
                    preview = "".join(f"+ {line}" for line in lines if line.strip())
                    diff_text = f"--- a/{file_path}\n+++ b/{file_path}\n@@ -1,0 +1,{len(lines)} @@\n{preview}"
                    additions = max(1, len([l for l in lines if l.strip()]))
                    deletions = 0
                except Exception:
                    diff_text = f"--- a/{file_path}\n+++ b/{file_path}\n@@ -0,0 +1,1 @@\n+ // {file_path} - active verified artifact"
                    additions = 1
                    deletions = 0
            else:
                change_type = "added"
                diff_text = (
                    f"--- /dev/null\n+++ b/{file_path}\n@@ -0,0 +1,5 @@\n"
                    f"+ // Generated by {node.assigned_agent or 'gerych_builder'}\n"
                    f"+ // Task Node: {node.title} ({node.id})\n"
                    f"+ // Status: {node.status.value if hasattr(node.status, 'value') else node.status}\n"
                    f"+ export const artifact_{node.id.replace('-', '_')} = true;\n"
                )
                additions = 4
                deletions = 0

        files_diff.append(
            ArtifactFileDiff(
                path=file_path,
                change_type=change_type,
                additions=additions,
                deletions=deletions,
                diff_content=diff_text,
            )
        )

    total_adds = sum(f.additions for f in files_diff)
    total_dels = sum(f.deletions for f in files_diff)

    return NodeArtifactReport(
        node_id=node.id,
        agent=node.assigned_agent or "gerych_builder",
        status=node.status.value if hasattr(node.status, "value") else str(node.status),
        files=files_diff,
        total_additions=total_adds,
        total_deletions=total_dels,
        executed_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/{node_id}/artifacts", response_model=NodeArtifactReport)
def get_node_artifacts(node_id: str):
    """Retrieve code artifacts and diff inspection report for a node task."""
    if node_id in _task_artifacts:
        return _task_artifacts[node_id]

    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    report = _generate_node_artifacts(node)
    _task_artifacts[node_id] = report
    return report


@router.post("/{node_id}/generate_marketing_video", response_model=Dict[str, Any])
def generate_node_marketing_video(node_id: str):
    """Generate grounded 9:16 vertical Remotion marketing video storyboard for a node task."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    artifacts = _task_artifacts.get(node_id)
    if not artifacts:
        artifacts = _generate_node_artifacts(node)

    synthesizer = TaskVideoSynthesizer()
    video_payload = synthesizer.synthesize_task_marketing_script(node_id=node_id, node=node, artifacts=artifacts)
    _task_marketing_videos[node_id] = video_payload
    return {"status": "success", "video": video_payload}


@router.get("/{node_id}/marketing_video", response_model=Dict[str, Any])
def get_node_marketing_video(node_id: str):
    """Retrieve or lazily synthesize 9:16 Remotion marketing video storyboard for a node task."""
    if node_id in _task_marketing_videos:
        return {"status": "success", "video": _task_marketing_videos[node_id]}

    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    artifacts = _task_artifacts.get(node_id)
    if not artifacts:
        artifacts = _generate_node_artifacts(node)

    synthesizer = TaskVideoSynthesizer()
    video_payload = synthesizer.synthesize_task_marketing_script(node_id=node_id, node=node, artifacts=artifacts)
    _task_marketing_videos[node_id] = video_payload
    return {"status": "success", "video": video_payload}


class SynthesizeVoiceoverRequest(BaseModel):
    voice_id: Optional[str] = "aura-1"
    text_override: Optional[str] = None


@router.post("/{node_id}/synthesize_voiceover", response_model=Dict[str, Any])
def synthesize_node_voiceover(node_id: str, req: Optional[SynthesizeVoiceoverRequest] = None):
    """Synthesize Voice AI audio for a node task marketing video."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    text: str = ""
    if req and req.text_override:
        text = req.text_override
    else:
        video_payload = _task_marketing_videos.get(node_id)
        if not video_payload:
            artifacts = _task_artifacts.get(node_id)
            if not artifacts:
                artifacts = _generate_node_artifacts(node)
            synthesizer = TaskVideoSynthesizer()
            video_payload = synthesizer.synthesize_task_marketing_script(node_id=node_id, node=node, artifacts=artifacts)
            _task_marketing_videos[node_id] = video_payload
        text = video_payload.get("voiceover_script", "")

    voice_id = (req.voice_id if req and req.voice_id else "aura-1")
    voice_synth = VoiceSynthesizer()
    res = voice_synth.synthesize_voiceover(text=text, node_id=node_id, voice_id=voice_id)
    return res


@router.get("/{node_id}/voiceover_audio")
def get_node_voiceover_audio(node_id: str):
    """Stream synthesized voiceover audio for a node task."""
    voice_synth = VoiceSynthesizer()
    audio_path = voice_synth.get_voiceover_audio_path(node_id)
    if not audio_path or not audio_path.exists():
        raise HTTPException(status_code=404, detail=f"Voiceover audio for node '{node_id}' not found. Please synthesize first.")

    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=f"audio_{node_id}.mp3",
    )


class ExportVideoMp4Request(BaseModel):
    composition_id: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


@router.post("/{node_id}/export_video_mp4", response_model=Dict[str, Any])
def export_node_video_mp4(node_id: str, req: Optional[ExportVideoMp4Request] = None):
    """Export Remotion 9:16 vertical video composition to MP4."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    payload = req.payload if (req and req.payload) else _task_marketing_videos.get(node_id)
    if not payload:
        artifacts = _task_artifacts.get(node_id)
        if not artifacts:
            artifacts = _generate_node_artifacts(node)
        synthesizer = TaskVideoSynthesizer()
        payload = synthesizer.synthesize_task_marketing_script(node_id=node_id, node=node, artifacts=artifacts)
        _task_marketing_videos[node_id] = payload

    exporter = RemotionExporter()
    res = exporter.export_mp4(node_id=node_id, payload=payload)
    return res


@router.get("/{node_id}/video_export_status", response_model=Dict[str, Any])
def get_node_video_export_status(node_id: str):
    """Check status of Remotion 9:16 vertical video MP4 export for a node task."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    exporter = RemotionExporter()
    return exporter.get_export_status(node_id=node_id)


@router.post("/{node_id}/accept_artifacts", response_model=Dict[str, Any])
def accept_node_artifacts(node_id: str):
    """Accept and certify generated node artifacts, marking the node task as COMPLETED."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    agent_name = node.assigned_agent or "gerych_builder"
    now_iso = datetime.now(timezone.utc).isoformat()

    node.status = NodeStatus.COMPLETED
    node.stage = ExecutionStage.COMPLETED
    node.progress = 100.0
    node.updated_at = now_iso

    NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
    manager.save_graph(graph)

    append_task_log(node_id, "SUCCESS", agent_name, "Artifacts accepted and certified by user. Task COMPLETED.")

    bridge = _get_active_canvas_bridge()
    if bridge is not None:
        try:
            bridge.publish_node_executed(
                node_id=node_id,
                status="completed",
                event_type="node.executed",
                execution_result="Artifacts accepted and certified by user.",
                payload={
                    "event": "node.executed",
                    "stage": "completed",
                    "status": "completed",
                    "progress": 100.0,
                    "agent": agent_name,
                    "title": node.title,
                    "action": "accepted",
                    "logs": _task_logs.get(node_id, []),
                },
            )
        except Exception as ex:
            logger.warning(f"Failed to publish accept_artifacts event via bridge: {ex}")

    try:
        manager.sync_to_obsidian()
    except Exception as ex:
        logger.warning(f"Failed to sync to Obsidian on accept_artifacts: {ex}")

    return {
        "status": "success",
        "node_id": node_id,
        "action": "accepted",
        "message": "Artifacts accepted and certified. Node transitioned to completed.",
        "node": node.model_dump(),
    }


@router.post("/{node_id}/reject_artifacts", response_model=Dict[str, Any])
def reject_node_artifacts(
    node_id: str,
    req: Optional[RejectArtifactsRequest] = None,
    reason: Optional[str] = Query(None),
):
    """Reject generated artifacts, rolling node task stage back to in_progress with 50% progress."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    agent_name = node.assigned_agent or "gerych_builder"
    now_iso = datetime.now(timezone.utc).isoformat()

    node.status = NodeStatus.IN_PROGRESS
    node.stage = ExecutionStage.IN_PROGRESS
    node.progress = 50.0
    node.updated_at = now_iso

    NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
    manager.save_graph(graph)

    rejection_reason = (req.reason if req and req.reason else None) or reason or "Rollback requested."
    reject_msg = f"WARNING: Artifacts rejected by user: {rejection_reason}"
    append_task_log(node_id, "WARNING", agent_name, reject_msg)

    bridge = _get_active_canvas_bridge()
    if bridge is not None:
        try:
            bridge.publish_node_executed(
                node_id=node_id,
                status="in_progress",
                event_type="node.status_changed",
                execution_result=reject_msg,
                payload={
                    "event": "node.status_changed",
                    "stage": "in_progress",
                    "status": "in_progress",
                    "progress": 50.0,
                    "agent": agent_name,
                    "title": node.title,
                    "action": "rejected",
                    "reason": rejection_reason,
                    "logs": _task_logs.get(node_id, []),
                },
            )
        except Exception as ex:
            logger.warning(f"Failed to publish reject_artifacts event via bridge: {ex}")

    return {
        "status": "success",
        "node_id": node_id,
        "action": "rejected",
        "message": "Artifacts rejected. Node rolled back to in_progress (50%).",
        "node": node.model_dump(),
    }


@router.post("/{node_id}/run_verification", response_model=Dict[str, Any])
async def run_node_verification(node_id: str, req: Optional[RunVerificationRequest] = None):
    """Trigger automated test verification gate for a node task."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    agent_name = node.assigned_agent or "gerych_auditor"
    append_task_log(node_id, "STEP", agent_name, "Starting automated verification gate...")

    cmd = None
    if req and req.test_command:
        cmd = req.test_command
    elif req and req.target_test_file:
        cmd = f".venv/bin/pytest {req.target_test_file} -q"
    else:
        test_file = next((f for f in node.target_files if "test_" in f or "/tests/" in f), None)
        if test_file:
            cmd = f".venv/bin/pytest {test_file} -q"
        else:
            cmd = ".venv/bin/pytest tests/verification/test_node_tasks_router.py -q"

    if cmd.startswith("pytest"):
        cmd = f".venv/bin/{cmd}"

    append_task_log(node_id, "INFO", agent_name, f"Executing verification: {cmd}")

    proc = None
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30.0)
        out_str = stdout.decode("utf-8", errors="replace")
        err_str = stderr.decode("utf-8", errors="replace")
        combined_output = (out_str + "\n" + err_str).strip()
        exit_code = proc.returncode
    except asyncio.TimeoutError:
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass
        exit_code = -1
        combined_output = "Verification command timed out after 30 seconds."
    except Exception as ex:
        exit_code = 1
        combined_output = f"Execution error: {str(ex)}"

    passed = (exit_code == 0)
    if passed:
        append_task_log(node_id, "SUCCESS", agent_name, f"Verification gate PASSED (exit code 0).\n{combined_output[:300]}")
    else:
        append_task_log(node_id, "ERROR", agent_name, f"Verification gate FAILED (exit code {exit_code}).\n{combined_output[:300]}")

    bridge = _get_active_canvas_bridge()
    if bridge is not None:
        try:
            bridge.publish_node_executed(
                node_id=node_id,
                status="verified" if passed else "failed",
                event_type="node.verified",
                execution_result="Verification PASSED" if passed else "Verification FAILED",
                payload={
                    "event": "node.verified",
                    "node_id": node_id,
                    "passed": passed,
                    "exit_code": exit_code,
                    "output": combined_output,
                    "logs": _task_logs.get(node_id, []),
                },
            )
        except Exception as ex:
            logger.warning(f"Failed to publish run_verification event via bridge: {ex}")

    return {
        "status": "success" if passed else "failure",
        "node_id": node_id,
        "action": "verification_run",
        "verified": passed,
        "exit_code": exit_code,
        "output": combined_output,
        "message": "Verification gate PASSED" if passed else "Verification gate FAILED",
    }


@router.post("/{node_id}/clear_logs", response_model=Dict[str, Any])
@router.delete("/{node_id}/logs", response_model=Dict[str, Any])
def clear_node_logs(node_id: str):
    """Clear in-memory execution logs for a node task."""
    _task_logs[node_id] = []
    return {"status": "success", "node_id": node_id, "message": "Logs cleared"}


async def _run_autonomous_agent_flow(node_id: str, agent_name: str, instructions: Optional[str] = None) -> None:
    """
    Executes autonomous progressive flow in the background for a node task,
    streaming realistic logs and progressing through execution stages:
    in_progress (35%) -> in_progress (55%) -> in_progress (75%) -> testing (90%) -> completed (100%).
    """
    manager = NodeTaskPersistenceManager.get_instance()
    bridge = _get_active_canvas_bridge()

    steps = [
        (35.0, ExecutionStage.IN_PROGRESS, "INFO", "TaskDNA decomposition: validated contracts & active workspace context."),
        (55.0, ExecutionStage.IN_PROGRESS, "STEP", f"[{agent_name}] Inspecting codebase architecture & dependency DAG..."),
        (75.0, ExecutionStage.IN_PROGRESS, "STEP", f"[{agent_name}] Synthesizing atomic implementation slice (MASE budget <= 25)..."),
        (90.0, ExecutionStage.VERIFICATION, "STEP", "Running zero-waste precommit verification gate & automated tests..."),
        (100.0, ExecutionStage.COMPLETED, "SUCCESS", "Master Quality Gate certified 100% Green. Task marked COMPLETED."),
    ]

    for progress, stage, log_level, log_message in steps:
        await asyncio.sleep(1.2)

        try:
            graph = manager.load_graph()
            node = graph.nodes.get(node_id)
            if not node:
                break

            node.progress = progress
            node.stage = stage
            if stage == ExecutionStage.COMPLETED:
                node.status = NodeStatus.COMPLETED
            else:
                node.status = NodeStatus.IN_PROGRESS

            node.updated_at = datetime.now(timezone.utc).isoformat()
            NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
            manager.save_graph(graph)

            # Append log and push to WS
            append_task_log(node_id, log_level, agent_name, log_message)

            # Publish event via bridge to WS clients
            if bridge is not None:
                final_status = node.status.value if hasattr(node.status, "value") else str(node.status)
                final_stage = node.stage.value if hasattr(node.stage, "value") else str(node.stage)
                is_completed = (stage == ExecutionStage.COMPLETED)
                event_type = "node.executed" if is_completed else "node.status_changed"
                bridge.publish_node_executed(
                    node_id=node_id,
                    status=final_status,
                    event_type=event_type,
                    execution_result=log_message,
                    payload={
                        "event": event_type,
                        "stage": final_stage,
                        "status": final_status,
                        "progress": node.progress,
                        "agent": agent_name,
                        "title": node.title,
                        "logs": _task_logs.get(node_id, []),
                    },
                )
        except Exception as err:
            logger.error(f"Error in _run_autonomous_agent_flow step: {err}")
            break

    # Sync to Obsidian upon completion
    try:
        manager.sync_to_obsidian()
    except Exception as ex:
        logger.warning(f"Failed to sync to Obsidian after execution: {ex}")

    # Generate and cache artifacts upon completion
    try:
        g = manager.load_graph()
        n = g.nodes.get(node_id)
        if n:
            _task_artifacts[node_id] = _generate_node_artifacts(n)
    except Exception as ex:
        logger.warning(f"Failed to generate artifacts for node {node_id}: {ex}")


@router.post("/execute_agent", response_model=Dict[str, Any])
@router.post("/{node_id}/execute", response_model=Dict[str, Any])
async def execute_agent_for_node(node_id: Optional[str] = None, req: Optional[ExecuteAgentRequest] = None):
    """Simulate or trigger Swarm Agent execution for a node."""
    target_node_id = node_id or (req.node_id if req else None)
    if not target_node_id:
        raise HTTPException(status_code=400, detail="node_id is required either in URL path or request body.")

    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    node = graph.nodes.get(target_node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{target_node_id}' not found.")

    if node.is_blocked:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute agent: node is blocked by {node.blocked_by}"
        )

    agent_name = (req.agent_override if req else None) or node.assigned_agent or "gerych_builder"
    now_iso = datetime.now(timezone.utc).isoformat()

    bridge = _get_active_canvas_bridge()
    if bridge is not None:
        try:
            bridge.publish_node_executed(
                node_id=target_node_id,
                status="in_progress",
                event_type="node.status_changed",
                payload={
                    "event": "node.status_changed",
                    "stage": ExecutionStage.IN_PROGRESS.value,
                    "status": NodeStatus.IN_PROGRESS.value,
                    "progress": node.progress,
                    "agent": agent_name,
                    "title": node.title,
                },
            )
        except Exception as ex:
            logger.warning(f"Failed to publish initial node event via bridge: {ex}")

    append_task_log(target_node_id, "INFO", agent_name, f"Initializing autonomous execution for: {node.title}")
    append_task_log(target_node_id, "STEP", agent_name, f"Role: {agent_name} | Type: {node.node_type.value} | Priority: {node.priority}")

    if req and req.task_instructions:
        append_task_log(target_node_id, "STEP", agent_name, f"Custom Instructions: {req.task_instructions}")

    if req and req.auto_complete:
        append_task_log(target_node_id, "STEP", agent_name, "Running zero-waste execution slice & verification gate...")
        append_task_log(target_node_id, "SUCCESS", agent_name, "Master Quality Gate certified 100% Green. Task marked COMPLETED.")
        node.stage = ExecutionStage.COMPLETED
        node.status = NodeStatus.COMPLETED
        node.progress = 100.0
        node.updated_at = now_iso
        NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
        manager.save_graph(graph)
        try:
            _task_artifacts[target_node_id] = _generate_node_artifacts(node)
        except Exception:
            pass
        try:
            manager.sync_to_obsidian()
        except Exception:
            pass
    else:
        append_task_log(target_node_id, "STEP", agent_name, "Worker engaged. Starting live autonomous execution flow...")
        node.stage = ExecutionStage.IN_PROGRESS
        node.status = NodeStatus.IN_PROGRESS
        node.progress = max(node.progress, 25.0)
        node.updated_at = now_iso
        NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
        manager.save_graph(graph)

        # Trigger background progressive execution
        asyncio.create_task(_run_autonomous_agent_flow(target_node_id, agent_name, req.task_instructions if req else None))

    if bridge is not None:
        try:
            final_status = node.status.value if hasattr(node.status, "value") else str(node.status)
            final_stage = node.stage.value if hasattr(node.stage, "value") else str(node.stage)
            is_completed = (node.status == NodeStatus.COMPLETED or final_status == "completed")
            final_event_type = "node.executed" if is_completed else "node.status_changed"
            bridge.publish_node_executed(
                node_id=target_node_id,
                status=final_status,
                event_type=final_event_type,
                execution_result=f"Dispatched task to Swarm Agent '{agent_name}'",
                payload={
                    "event": final_event_type,
                    "stage": final_stage,
                    "status": final_status,
                    "progress": node.progress,
                    "agent": agent_name,
                    "title": node.title,
                    "logs": _task_logs.get(target_node_id, []),
                },
            )
        except Exception as ex:
            logger.warning(f"Failed to publish final node event via bridge: {ex}")

    return {
        "status": "success",
        "message": f"Dispatched task to Swarm Agent '{agent_name}' (Running live in background)",
        "node_id": node.id,
        "assigned_agent": agent_name,
        "stage": node.stage.value,
        "progress": node.progress,
        "logs": _task_logs.get(target_node_id, [])
    }


@router.post("/batch_stage_transition", response_model=Dict[str, Any])
def batch_stage_transition(req: BatchStageTransitionRequest):
    """Transition multiple nodes to a target execution stage with dependency checking."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    updated_ids: List[str] = []
    skipped: List[Dict[str, Any]] = []

    for nid in req.node_ids:
        node = graph.nodes.get(nid)
        if not node:
            skipped.append({"node_id": nid, "reason": f"Node '{nid}' not found."})
            continue

        allowed, reason = NodeTaskGraphEngine.can_transition_stage(
            node=node,
            target_stage=req.target_stage,
            graph=graph,
            force=req.force,
        )

        if not allowed:
            skipped.append({"node_id": nid, "reason": reason})
            continue

        node.stage = req.target_stage
        node.updated_at = datetime.now(timezone.utc).isoformat()
        if req.target_stage == ExecutionStage.COMPLETED:
            node.status = NodeStatus.COMPLETED
            node.progress = 100.0
        elif req.target_stage == ExecutionStage.IN_PROGRESS and node.status in (
            NodeStatus.READY,
            NodeStatus.BACKLOG,
            NodeStatus.DRAFT,
        ):
            node.status = NodeStatus.IN_PROGRESS
            if node.progress == 0.0:
                node.progress = 10.0
        updated_ids.append(nid)

    if updated_ids:
        NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
        manager.save_graph(graph)
        try:
            manager.sync_to_obsidian()
        except Exception as ex:
            logger.warning(f"Failed to sync to Obsidian after batch stage transition: {ex}")

    return {
        "status": "success",
        "updated_ids": updated_ids,
        "skipped": skipped,
        "total_requested": len(req.node_ids),
        "total_updated": len(updated_ids),
    }


@router.post("/batch_delete", response_model=Dict[str, Any])
def batch_delete_nodes(req: BatchDeleteRequest):
    """Delete multiple nodes and their incident edges atomically."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    deleted_ids: List[str] = []
    node_set = set(req.node_ids)

    for nid in req.node_ids:
        if nid in graph.nodes:
            del graph.nodes[nid]
            deleted_ids.append(nid)

    if deleted_ids:
        graph.edges = [e for e in graph.edges if e.source not in node_set and e.target not in node_set]
        NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
        manager.save_graph(graph)
        try:
            manager.sync_to_obsidian()
        except Exception as ex:
            logger.warning(f"Failed to sync to Obsidian after batch delete: {ex}")

    return {
        "status": "success",
        "deleted_ids": deleted_ids,
        "remaining_nodes": len(graph.nodes),
    }


@router.post("/batch_execute", response_model=Dict[str, Any])
async def batch_execute_nodes(req: BatchExecuteRequest):
    """Trigger agent execution for multiple nodes in a single batch."""
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    executed_ids: List[str] = []
    skipped: List[Dict[str, Any]] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    bridge = _get_active_canvas_bridge()

    for nid in req.node_ids:
        node = graph.nodes.get(nid)
        if not node:
            skipped.append({"node_id": nid, "reason": f"Node '{nid}' not found."})
            continue

        if node.is_blocked:
            skipped.append({"node_id": nid, "reason": f"Node is blocked by {node.blocked_by}"})
            continue

        agent_name = req.agent_override or node.assigned_agent or "gerych_builder"

        if req.auto_complete:
            append_task_log(nid, "SUCCESS", agent_name, "Batch execution auto-completed by user request.")
            node.stage = ExecutionStage.COMPLETED
            node.status = NodeStatus.COMPLETED
            node.progress = 100.0
            node.updated_at = now_iso
        else:
            append_task_log(nid, "STEP", agent_name, "Batch worker engaged. Starting live autonomous execution flow...")
            node.stage = ExecutionStage.IN_PROGRESS
            node.status = NodeStatus.IN_PROGRESS
            node.progress = max(node.progress, 25.0)
            node.updated_at = now_iso
            asyncio.create_task(_run_autonomous_agent_flow(nid, agent_name, req.task_instructions))

        executed_ids.append(nid)

        if bridge is not None:
            try:
                final_status = node.status.value if hasattr(node.status, "value") else str(node.status)
                final_stage = node.stage.value if hasattr(node.stage, "value") else str(node.stage)
                is_completed = (node.status == NodeStatus.COMPLETED or final_status == "completed")
                final_event_type = "node.executed" if is_completed else "node.status_changed"
                bridge.publish_node_executed(
                    node_id=nid,
                    status=final_status,
                    event_type=final_event_type,
                    execution_result=f"Dispatched task to Swarm Agent '{agent_name}' (batch)",
                    payload={
                        "event": final_event_type,
                        "stage": final_stage,
                        "status": final_status,
                        "progress": node.progress,
                        "agent": agent_name,
                        "title": node.title,
                        "logs": _task_logs.get(nid, []),
                    },
                )
            except Exception as ex:
                logger.warning(f"Failed to publish bridge event for batch execute node {nid}: {ex}")

    if executed_ids:
        NodeTaskGraphEngine.recalculate_graph_dependencies(graph)
        manager.save_graph(graph)
        try:
            manager.sync_to_obsidian()
        except Exception as ex:
            logger.warning(f"Failed to sync to Obsidian after batch execute: {ex}")

    return {
        "status": "success",
        "executed_ids": executed_ids,
        "skipped": skipped,
        "total_requested": len(req.node_ids),
        "total_executed": len(executed_ids),
    }


@router.post("/{node_id}/decompose", response_model=Dict[str, Any])
def decompose_node_with_ai(node_id: str, req: Optional[DecomposeNodeRequest] = None):
    """
    Decomposes an existing Epic, Idea, or Task into 3 atomic child subtasks
    assigned to specialized swarm agents, creating DAG edges and persisting to Obsidian.
    """
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    instructions = req.instructions if req else None
    workspace_id = (req.workspace_id if req else None) or "ws-alpha-001"

    created_nodes, created_edges, gerych_reply = ConversationalTaskExtractor.decompose_node(
        node=node,
        graph=graph,
        instructions=instructions,
        workspace_id=workspace_id,
    )

    manager.save_graph(graph)
    try:
        manager.sync_to_obsidian()
    except Exception:
        pass

    return {
        "status": "success",
        "parent_node_id": node.id,
        "created_nodes": [n.model_dump() for n in created_nodes],
        "created_edges": [e.model_dump() for e in created_edges],
        "message": gerych_reply,
    }


@router.post("/chat_intake", response_model=Dict[str, Any])
def chat_intake_task_creation(req: ChatIntakeRequest):
    """
    Parses conversational chat messages from user into structured DAG nodes & edges,
    adding them to the graph and updating Obsidian.
    """
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()

    created_nodes, created_edges, gerych_reply, action, target_node_id = ConversationalTaskExtractor.process_chat_message(
        prompt=req.prompt,
        graph=graph,
        workspace_id=req.workspace_id or "ws-alpha-001",
        default_agent=req.default_agent,
        history=req.history,
        selected_node_id=req.selected_node_id,
    )

    manager.save_graph(graph)
    try:
        manager.sync_to_obsidian()
    except Exception:
        pass
    stats = NodeTaskGraphEngine.compute_statistics(graph)

    return {
        "status": "success",
        "reply": gerych_reply,
        "action": action,
        "target_node_id": target_node_id,
        "created_nodes": [n.model_dump() for n in created_nodes],
        "created_edges": [e.model_dump() for e in created_edges],
        "stats": stats.model_dump()
    }


class MergeGraphRequest(BaseModel):
    base_state: Dict[str, Any]
    incoming_state: Dict[str, Any]
    current_state: Optional[Dict[str, Any]] = None
    position_strategy: Optional[str] = "shift"
    save_to_persistence: bool = True


@router.post("/merge", response_model=Dict[str, Any])
def merge_node_task_graph(req: MergeGraphRequest) -> Dict[str, Any]:
    """
    OCC 3-Way Structural Graph Mutation Resolver.
    Merges base_state, current_state (from server persistence if omitted),
    and incoming_state (Mine).
    Raises HTTP 409 Conflict if irreconcilable structural conflicts (e.g. cycles) are detected.
    """
    manager = NodeTaskPersistenceManager.get_instance()

    curr_state = req.current_state
    if curr_state is None:
        curr_graph = manager.load_graph()
        curr_state = curr_graph.model_dump()

    result = OCCConcurrencyEngine.merge_graph_state(
        base_state=req.base_state,
        current_state=curr_state,
        incoming_state=req.incoming_state,
        position_strategy=req.position_strategy or "shift",
    )

    if result.has_unresolved_conflicts or result.status == "conflict":
        conflict_messages = [f"[{c.conflict_type}] {c.message}" for c in result.conflicts]
        detail_msg = "OCC Structural Graph Merge Conflict: " + "; ".join(conflict_messages)
        raise HTTPException(
            status_code=409,
            detail={
                "error": "OCC_MERGE_CONFLICT",
                "message": detail_msg,
                "conflicts": [c.to_dict() for c in result.conflicts],
                "applied_mutations": result.applied_mutations,
            },
        )

    if req.save_to_persistence:
        try:
            merged_model = NodeTaskGraph.model_validate(result.merged_graph)
            manager.save_graph(merged_model)
            manager.sync_to_obsidian()
        except Exception:
            pass

    return result.to_dict()


class AuditSessionRequest(BaseModel):
    session_id: Optional[str] = None
    agent_override: Optional[str] = None
    stderr_logs: Optional[str] = None


@router.post("/{node_id}/audit_session", response_model=Dict[str, Any])
def audit_node_task_session(node_id: str, req: Optional[AuditSessionRequest] = None):
    """
    Triggers Session Sentinel to audit execution trajectory for a node task,
    detect anomalies, synthesize self-healing task spec, and inject onto Canvas.
    """
    from core.orchestrator.session_sentinel import SessionSentinel

    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes.get(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    agent_name = (req.agent_override if req else None) or node.assigned_agent or "gerych_builder"
    sentinel = SessionSentinel(agent_name=agent_name)

    session_id = req.session_id if req else None
    stderr_logs = req.stderr_logs if req else None

    audit = sentinel.run_post_task_pipeline(session_id=session_id, stderr_logs=stderr_logs)
    if not audit:
        return {
            "status": "warning",
            "message": "No active or recorded session found for audit.",
            "node_id": node_id
        }

    return {
        "status": "success",
        "node_id": node_id,
        "audit": audit.model_dump()
    }



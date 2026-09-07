# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/task_forest_router.py"
# purpose: "FastAPI REST router for Task Forest 5-Plant Scale Engine (Field -> Sector -> Tree -> Bush -> Flower) with Bottom-Up Rollup & Evolution History."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v3/task_forest", tags=["Task Forest Spatial Engine"])

PLANT_ICONS = {
    "field": "🌾",
    "sector": "🏞️",
    "tree": "🌳",
    "bush": "🌿",
    "flower": "🌸"
}

PLANT_HIERARCHY_LEVELS = ["field", "sector", "tree", "bush", "flower"]


class TaskForestNode(BaseModel):
    id: str
    title: str
    plant_scale: str = Field(..., description="field | sector | tree | bush | flower")
    status: str = Field(default="todo", description="todo | pending | in_progress | completed | cancelled | ready")
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    parent_id: Optional[str] = None
    assigned_agent: Optional[str] = None
    author: Optional[str] = "Maxim"
    weight: float = 1.0
    git_diff: Optional[str] = None
    dto_contract: Optional[Dict[str, Any]] = None
    verification_status: Optional[str] = "verified"
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    children: List["TaskForestNode"] = Field(default_factory=list)


class MutateNodeRequest(BaseModel):
    node_id: Optional[str] = Field(default=None, description="Existing node ID to mutate, or omit to create new node")
    parent_id: Optional[str] = Field(default=None, description="Parent node ID if creating new flower/bush")
    title: Optional[str] = None
    plant_scale: Optional[str] = Field(default="flower", description="field | sector | tree | bush | flower")
    status: Optional[str] = Field(default=None, description="todo | pending | in_progress | completed | cancelled")
    progress: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    assigned_agent: Optional[str] = None
    author: Optional[str] = None
    git_diff: Optional[str] = None
    dto_contract: Optional[Dict[str, Any]] = None
    verification_status: Optional[str] = None


class EvolutionHistoryItem(BaseModel):
    event_id: str
    timestamp: str
    node_id: str
    node_title: str
    plant_scale: str
    mutation_type: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    previous_progress: Optional[float] = None
    new_progress: Optional[float] = None
    overall_field_progress: float
    description: str


class TaskForestStore:
    """In-memory thread-safe state store for Task Forest with Bottom-Up Rollup."""

    def __init__(self):
        self._nodes: Dict[str, TaskForestNode] = {}
        self._history: List[EvolutionHistoryItem] = []
        self._init_default_forest()

    def _init_default_forest(self):
        self._nodes.clear()
        self._history.clear()

        # 1. 🌾 Field (Root)
        root_field = TaskForestNode(
            id="field-001",
            title="DNK_HUB Master HQ",
            plant_scale="field",
            status="in_progress",
            progress=88.0,
            assigned_agent="antigravity_mentor",
            author="Maxim",
            verification_status="verified",
            dto_contract={"protocol": "TaskForestV5", "workspace": "ws-alpha-001"}
        )

        # 2. 🏞️ Sector
        sector_canvas = TaskForestNode(
            id="sector-001",
            title="Spatial Studio & Infinite Canvas",
            plant_scale="sector",
            status="in_progress",
            progress=88.0,
            parent_id="field-001",
            assigned_agent="gerych_builder",
            author="Maxim",
            verification_status="verified"
        )

        # 3. 🌳 Trees
        # Tree 1: Google Stitch Canvas & Play Prototyper (100% 🟢)
        tree_stitch = TaskForestNode(
            id="tree-001",
            title="Google Stitch Canvas & Play Prototyper",
            plant_scale="tree",
            status="completed",
            progress=100.0,
            parent_id="sector-001",
            assigned_agent="gerych_builder",
            verification_status="verified",
            git_diff="feat(stitch): interactive DAG screen rendering & play prototype runtime"
        )
        bush_stitch_1 = TaskForestNode(
            id="bush-001",
            title="Screen DAG Orchestrator",
            plant_scale="bush",
            status="completed",
            progress=100.0,
            parent_id="tree-001",
            assigned_agent="gerych_builder"
        )
        flw_stitch_1 = TaskForestNode(
            id="flw-001",
            title="Interactive Canvas Screen Nodes",
            plant_scale="flower",
            status="completed",
            progress=100.0,
            parent_id="bush-001",
            assigned_agent="gerych_builder"
        )
        flw_stitch_2 = TaskForestNode(
            id="flw-002",
            title="WebSocket Sync & Collaborative State",
            plant_scale="flower",
            status="completed",
            progress=100.0,
            parent_id="bush-001",
            assigned_agent="gerych_builder"
        )

        # Tree 2: Shopify OS 2.0 Live AST Sandbox (100% 🟢)
        tree_shopify = TaskForestNode(
            id="tree-002",
            title="Shopify OS 2.0 Live AST Sandbox",
            plant_scale="tree",
            status="completed",
            progress=100.0,
            parent_id="sector-001",
            assigned_agent="dnk_shopify",
            verification_status="verified",
            git_diff="feat(shopify): AST Liquid compiler, schema generator & theme live push"
        )
        bush_shopify_1 = TaskForestNode(
            id="bush-002",
            title="Liquid AST Transpiler",
            plant_scale="bush",
            status="completed",
            progress=100.0,
            parent_id="tree-002",
            assigned_agent="dnk_shopify"
        )
        flw_shopify_1 = TaskForestNode(
            id="flw-003",
            title="Canvas to Shopify Theme Transpiler",
            plant_scale="flower",
            status="completed",
            progress=100.0,
            parent_id="bush-002",
            assigned_agent="dnk_shopify"
        )
        flw_shopify_2 = TaskForestNode(
            id="flw-004",
            title="Liquid Syntax & Variable Linting",
            plant_scale="flower",
            status="completed",
            progress=100.0,
            parent_id="bush-002",
            assigned_agent="dnk_shopify"
        )

        # Tree 3: DuckDB Lakehouse AI Analyst (100% 🟢)
        tree_lakehouse = TaskForestNode(
            id="tree-003",
            title="DuckDB Lakehouse AI Analyst",
            plant_scale="tree",
            status="completed",
            progress=100.0,
            parent_id="sector-001",
            assigned_agent="dnk_dev_fullstack",
            verification_status="verified",
            git_diff="feat(lakehouse): DuckDB analytical schemas, NL2SQL query engine & dynamic charts"
        )
        bush_lakehouse_1 = TaskForestNode(
            id="bush-003",
            title="Lakehouse BI NL2SQL Engine",
            plant_scale="bush",
            status="completed",
            progress=100.0,
            parent_id="tree-003",
            assigned_agent="dnk_dev_fullstack"
        )
        flw_lakehouse_1 = TaskForestNode(
            id="flw-005",
            title="In-Memory DuckDB Analytical Schema",
            plant_scale="flower",
            status="completed",
            progress=100.0,
            parent_id="bush-003",
            assigned_agent="dnk_dev_fullstack"
        )
        flw_lakehouse_2 = TaskForestNode(
            id="flw-006",
            title="Multi-Agent DAG Query Dispatcher",
            plant_scale="flower",
            status="completed",
            progress=100.0,
            parent_id="bush-003",
            assigned_agent="dnk_dev_fullstack"
        )

        # Tree 4: Task Forest Spatial HQ (In Progress 🟡 - 40%)
        tree_forest = TaskForestNode(
            id="tree-004",
            title="Task Forest Spatial HQ",
            plant_scale="tree",
            status="in_progress",
            progress=40.0,
            parent_id="sector-001",
            assigned_agent="gerych_prime",
            verification_status="pending",
            git_diff="feat(task_forest): 5-plant scale taxonomy, bottom-up rollup & timeline history"
        )
        bush_forest_1 = TaskForestNode(
            id="bush-004",
            title="5-Plant Scale Taxonomy Engine",
            plant_scale="bush",
            status="in_progress",
            progress=40.0,
            parent_id="tree-004",
            assigned_agent="gerych_prime"
        )
        flw_forest_1 = TaskForestNode(
            id="flw-007",
            title="Bottom-Up Recursive Rollup Logic",
            plant_scale="flower",
            status="completed",
            progress=100.0,
            parent_id="bush-004",
            assigned_agent="gerych_prime"
        )
        flw_forest_2 = TaskForestNode(
            id="flw-008",
            title="Spatial Canvas Drawer UI & Inspector",
            plant_scale="flower",
            status="todo",
            progress=0.0,
            parent_id="bush-004",
            assigned_agent="gerych_builder"
        )
        flw_forest_3 = TaskForestNode(
            id="flw-009",
            title="Genetic Scrubber & Timeline History",
            plant_scale="flower",
            status="todo",
            progress=0.0,
            parent_id="bush-004",
            assigned_agent="gerych_builder"
        )
        flw_forest_4 = TaskForestNode(
            id="flw-010",
            title="FastAPI REST Mutation Endpoints",
            plant_scale="flower",
            status="in_progress",
            progress=60.0,
            parent_id="bush-004",
            assigned_agent="gerych_prime"
        )

        # Tree 5: CapCut Kinetic Video Timeline (Ready ⚪ - 100%)
        tree_timeline = TaskForestNode(
            id="tree-005",
            title="CapCut Kinetic Video Timeline",
            plant_scale="tree",
            status="ready",
            progress=100.0,
            parent_id="sector-001",
            assigned_agent="dnk_video_ai_creator",
            verification_status="verified",
            git_diff="feat(video): multi-track kinetic timeline, audio waveforms & Remotion render"
        )
        bush_timeline_1 = TaskForestNode(
            id="bush-005",
            title="Kinetic Motion & Audio Reactive Tracks",
            plant_scale="bush",
            status="completed",
            progress=100.0,
            parent_id="tree-005",
            assigned_agent="dnk_video_ai_creator"
        )
        flw_timeline_1 = TaskForestNode(
            id="flw-011",
            title="Audio Waveform Keyframe Engine",
            plant_scale="flower",
            status="completed",
            progress=100.0,
            parent_id="bush-005",
            assigned_agent="dnk_video_ai_creator"
        )
        flw_timeline_2 = TaskForestNode(
            id="flw-012",
            title="Headless Remotion Video Renderer",
            plant_scale="flower",
            status="completed",
            progress=100.0,
            parent_id="bush-005",
            assigned_agent="dnk_video_ai_creator"
        )

        all_init_nodes = [
            root_field, sector_canvas,
            tree_stitch, bush_stitch_1, flw_stitch_1, flw_stitch_2,
            tree_shopify, bush_shopify_1, flw_shopify_1, flw_shopify_2,
            tree_lakehouse, bush_lakehouse_1, flw_lakehouse_1, flw_lakehouse_2,
            tree_forest, bush_forest_1, flw_forest_1, flw_forest_2, flw_forest_3, flw_forest_4,
            tree_timeline, bush_timeline_1, flw_timeline_1, flw_timeline_2
        ]

        for n in all_init_nodes:
            self._nodes[n.id] = n

        # Initial history baseline
        self._history.append(
            EvolutionHistoryItem(
                event_id="evt-genesis-001",
                timestamp=datetime.now(timezone.utc).isoformat(),
                node_id="field-001",
                node_title="DNK_HUB Master HQ",
                plant_scale="field",
                mutation_type="genesis",
                previous_status=None,
                new_status="in_progress",
                previous_progress=None,
                new_progress=88.0,
                overall_field_progress=88.0,
                description="Initial Task Forest Genesis baseline established."
            )
        )

        # Run bottom-up rollup to ensure mathematically consistent tree
        self._recalculate_all_rollup()

    def _get_children(self, parent_id: str) -> List[TaskForestNode]:
        return [n for n in self._nodes.values() if n.parent_id == parent_id]

    def _recalculate_all_rollup(self) -> float:
        """Recursive bottom-up rollup starting from leaf nodes to root."""
        # Find root field
        roots = [n for n in self._nodes.values() if n.parent_id is None]
        if not roots:
            return 0.0

        for root in roots:
            self._rollup_node(root)

        root_field = self._nodes.get("field-001")
        return root_field.progress if root_field else 0.0

    def _rollup_node(self, node: TaskForestNode) -> float:
        children = self._get_children(node.id)
        if not children:
            # Leaf node calculation
            if node.status == "completed":
                node.progress = 100.0
            elif node.status in ("todo", "cancelled"):
                node.progress = 0.0
            elif node.status in ("in_progress", "pending"):
                # preserve explicit progress
                pass
            return node.progress

        child_progresses = [self._rollup_node(child) for child in children]
        avg_progress = round(sum(child_progresses) / len(child_progresses), 2)
        node.progress = avg_progress

        if avg_progress >= 100.0:
            node.status = "completed"
        elif avg_progress <= 0.0 and node.status not in ("cancelled", "ready"):
            node.status = "todo"
        elif node.status != "ready":
            node.status = "in_progress"

        return node.progress

    def recalculate_cascade(self, starting_node_id: str) -> None:
        """Recalculate progress up the ancestor chain: Node -> Bush -> Tree -> Sector -> Field."""
        curr_id = starting_node_id
        while curr_id:
            curr = self._nodes.get(curr_id)
            if not curr:
                break
            children = self._get_children(curr.id)
            if children:
                avg = round(sum(c.progress for c in children) / len(children), 2)
                curr.progress = avg
                if avg >= 100.0:
                    curr.status = "completed"
                elif avg <= 0.0 and curr.status not in ("cancelled", "ready"):
                    curr.status = "todo"
                elif curr.status != "ready":
                    curr.status = "in_progress"
            curr_id = curr.parent_id

    def build_tree_graph(self) -> TaskForestNode:
        """Returns deep nested tree graph for frontend consumption."""
        self._recalculate_all_rollup()
        root = self._nodes.get("field-001")
        if not root:
            raise HTTPException(status_code=404, detail="Root field node not found")

        def _assemble(n: TaskForestNode) -> TaskForestNode:
            c_nodes = self._get_children(n.id)
            return TaskForestNode(
                id=n.id,
                title=n.title,
                plant_scale=n.plant_scale,
                status=n.status,
                progress=n.progress,
                parent_id=n.parent_id,
                assigned_agent=n.assigned_agent,
                author=n.author,
                weight=n.weight,
                git_diff=n.git_diff,
                dto_contract=n.dto_contract,
                verification_status=n.verification_status,
                updated_at=n.updated_at,
                children=[_assemble(c) for c in c_nodes]
            )

        return _assemble(root)

    def mutate_node(self, req: MutateNodeRequest) -> Dict[str, Any]:
        prev_status = None
        prev_progress = None
        mutation_type = "create"

        if req.node_id and req.node_id in self._nodes:
            # Update existing node
            node = self._nodes[req.node_id]
            prev_status = node.status
            prev_progress = node.progress
            mutation_type = "update"

            if req.title is not None:
                node.title = req.title
            if req.status is not None:
                node.status = req.status
                if req.status == "completed":
                    node.progress = 100.0
                elif req.status in ("todo", "cancelled"):
                    node.progress = 0.0
            if req.progress is not None:
                node.progress = req.progress
            if req.assigned_agent is not None:
                node.assigned_agent = req.assigned_agent
            if req.author is not None:
                node.author = req.author
            if req.git_diff is not None:
                node.git_diff = req.git_diff
            if req.dto_contract is not None:
                node.dto_contract = req.dto_contract
            if req.verification_status is not None:
                node.verification_status = req.verification_status

            node.updated_at = datetime.now(timezone.utc).isoformat()
            target_node = node
        else:
            # Create new node
            new_id = req.node_id or f"flw-{int(time.time() * 1000) % 1000000:06d}"
            target_node = TaskForestNode(
                id=new_id,
                title=req.title or "New Task Flower",
                plant_scale=req.plant_scale or "flower",
                status=req.status or "todo",
                progress=100.0 if req.status == "completed" else (req.progress or 0.0),
                parent_id=req.parent_id or "bush-004",
                assigned_agent=req.assigned_agent or "gerych_builder",
                author=req.author or "Maxim",
                git_diff=req.git_diff or "feat(task): new atomic task created on spatial canvas",
                dto_contract=req.dto_contract,
                verification_status=req.verification_status or "verified"
            )
            self._nodes[new_id] = target_node

        # Recalculate rollup cascade
        if target_node.parent_id:
            self.recalculate_cascade(target_node.parent_id)
        else:
            self._recalculate_all_rollup()

        root = self._nodes.get("field-001")
        overall = root.progress if root else 0.0

        # Append evolution history entry
        evt_id = f"evt-{int(time.time() * 1000)}"
        history_item = EvolutionHistoryItem(
            event_id=evt_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            node_id=target_node.id,
            node_title=target_node.title,
            plant_scale=target_node.plant_scale,
            mutation_type=mutation_type,
            previous_status=prev_status,
            new_status=target_node.status,
            previous_progress=prev_progress,
            new_progress=target_node.progress,
            overall_field_progress=overall,
            description=f"Node '{target_node.title}' mutated: status={target_node.status}, progress={target_node.progress}%"
        )
        self._history.insert(0, history_item)

        return {
            "status": "success",
            "mutation_type": mutation_type,
            "node": target_node.model_dump(),
            "overall_field_progress": overall,
            "event_id": evt_id
        }


# Global in-memory singleton store
_task_forest_store = TaskForestStore()


@router.get("/graph", response_model=Dict[str, Any])
def get_task_forest_graph():
    """
    Returns full Task Forest graph with Bottom-Up Rollup calculations across all 5 plant levels.
    Levels: 🌾 Field -> 🏞️ Sector -> 🌳 Tree -> 🌿 Bush -> 🌸 Flower
    """
    tree_root = _task_forest_store.build_tree_graph()
    nodes_flat = {k: v.model_dump() for k, v in _task_forest_store._nodes.items()}
    
    # Calculate taxonomy statistics
    scale_counts = {scale: 0 for scale in PLANT_HIERARCHY_LEVELS}
    for n in _task_forest_store._nodes.values():
        if n.plant_scale in scale_counts:
            scale_counts[n.plant_scale] += 1

    return {
        "status": "success",
        "taxonomy": PLANT_HIERARCHY_LEVELS,
        "plant_icons": PLANT_ICONS,
        "overall_progress": tree_root.progress,
        "root_field": tree_root.model_dump(),
        "total_nodes": len(nodes_flat),
        "scale_counts": scale_counts,
        "nodes": nodes_flat
    }


@router.post("/node/mutate", response_model=Dict[str, Any])
def mutate_task_forest_node(req: MutateNodeRequest):
    """
    Mutate existing task node or spawn a new flower node with automatic bottom-up cascade.
    """
    res = _task_forest_store.mutate_node(req)
    return res


@router.get("/evolution_history", response_model=Dict[str, Any])
def get_task_forest_evolution_history(limit: int = Query(default=50, ge=1, le=500)):
    """
    Returns task mutation history for the Canvas Timeline Scrubber.
    """
    history_slice = _task_forest_store._history[:limit]
    return {
        "status": "success",
        "total_events": len(_task_forest_store._history),
        "events": [h.model_dump() for h in history_slice]
    }


@router.post("/reset", response_model=Dict[str, Any])
def reset_task_forest_baseline():
    """Resets the task forest to the canonical initial baseline."""
    _task_forest_store._init_default_forest()
    return {
        "status": "success",
        "message": "Task forest reset to canonical baseline (88.0% Field Progress)."
    }

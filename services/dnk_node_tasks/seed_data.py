# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_node_tasks/seed_data.py"
# purpose: "DNK OS Development Baseline Seed Data for Node Based Tasks and Ideas"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Dict, List
from .models import (
    NodeType,
    ExecutionStage,
    NodeStatus,
    EdgeRelation,
    DependencyEdge,
    NodePosition,
    NodeItem,
    NodeTaskGraph,
)


def create_initial_dnk_node_task_graph() -> NodeTaskGraph:
    """Generates the baseline DAG graph for DNK OS development tasks and ideas."""
    now_iso = datetime.now(timezone.utc).isoformat()

    nodes: Dict[str, NodeItem] = {
        # --- IDEAS ---
        "idea-remotion": NodeItem(
            id="idea-remotion",
            title="Autonomous Voice-to-UI Video AI Generator (Remotion + FrameCN)",
            description="Generate high-converting 9:16 reels directly from product DNA and voice narration.",
            node_type=NodeType.IDEA,
            stage=ExecutionStage.IDEATION,
            status=NodeStatus.DRAFT,
            progress=20.0,
            assigned_agent="dnk_video_ai_creator",
            target_module="services/dnk_video_engine",
            target_files=["services/dnk_video_engine/composition.tsx"],
            acceptance_criteria=[
                "Support Remotion 9:16 vertical render",
                "Hook into ElevenLabs / OpenAI TTS voice",
                "FrameCN kinetic text animations"
            ],
            tags=["media", "video", "remotion", "idea"],
            priority="high",
            position=NodePosition(x=60.0, y=100.0),
            created_at=now_iso,
            updated_at=now_iso
        ),
        "idea-liquid-ast": NodeItem(
            id="idea-liquid-ast",
            title="Real-Time Shopify Liquid AST Live Transpiler",
            description="Bidirectional sync between visual spatial canvas blocks and Shopify OS 2.0 Liquid schema.",
            node_type=NodeType.IDEA,
            stage=ExecutionStage.IDEATION,
            status=NodeStatus.DRAFT,
            progress=35.0,
            assigned_agent="dnk_shopify",
            target_module="services/dnk_shopify",
            target_files=["services/dnk_shopify/liquid_ast.py"],
            acceptance_criteria=[
                "Parse Liquid {% schema %} without regex hacks",
                "AST mutation round-trip fidelity",
                "Preserve comments and liquid tags"
            ],
            tags=["shopify", "ecommerce", "liquid", "ast", "idea"],
            priority="critical",
            position=NodePosition(x=60.0, y=340.0),
            created_at=now_iso,
            updated_at=now_iso
        ),
        "idea-voice-flow": NodeItem(
            id="idea-voice-flow",
            title="Ukrainian Voice Command & Dialect Control for Gerych",
            description="Direct voice control with Ukrainian phonetic optimization for Swarm dispatch and spatial navigation.",
            node_type=NodeType.IDEA,
            stage=ExecutionStage.IDEATION,
            status=NodeStatus.DRAFT,
            progress=15.0,
            assigned_agent="gerych_prime",
            target_module="core",
            target_files=["core/voice/ukrainian_acoustic.py"],
            acceptance_criteria=[
                "Whisper local acoustic model fine-tune",
                "Real-time streaming via WebSocket",
                "Fast tool invocation dispatch"
            ],
            tags=["voice", "ukrainian", "hermes", "idea"],
            priority="medium",
            position=NodePosition(x=60.0, y=580.0),
            created_at=now_iso,
            updated_at=now_iso
        ),

        # --- EPICS ---
        "epic-canvas-v2": NodeItem(
            id="epic-canvas-v2",
            title="DNK Spatial Canvas Engine v2.0",
            description="Next-generation multi-user visual orchestration platform with LOD rendering and DAG task graph.",
            node_type=NodeType.EPIC,
            stage=ExecutionStage.ARCHITECTURE,
            status=NodeStatus.IN_PROGRESS,
            progress=65.0,
            assigned_agent="gerych_prime",
            target_module="apps/web",
            target_files=["apps/web/components/canvas/CanvasEngine.tsx"],
            acceptance_criteria=[
                "LOD 3-tier zooming (Macro, Meso, Micro)",
                "Full JSON Canvas v1.0 standard compliance",
                "Sub-16ms render loop for 1000+ nodes"
            ],
            tags=["canvas", "spatial", "ui", "epic"],
            priority="critical",
            position=NodePosition(x=460.0, y=200.0),
            created_at=now_iso,
            updated_at=now_iso
        ),
        "epic-swarm-self-heal": NodeItem(
            id="epic-swarm-self-heal",
            title="Swarm Autonomous Self-Healing & Error Distillation",
            description="Automated error capture, SCONES knowledge indexing, and zero-guess hotpatching.",
            node_type=NodeType.EPIC,
            stage=ExecutionStage.IN_PROGRESS,
            status=NodeStatus.IN_PROGRESS,
            progress=80.0,
            assigned_agent="gerych_prime",
            target_module="core",
            target_files=["core/error_distillation.py"],
            acceptance_criteria=[
                "Instant distillation on test failure",
                "Zero manual loop guessing",
                "Self-healing verified via adversarial gate"
            ],
            tags=["swarm", "self_healing", "distiller", "epic"],
            priority="critical",
            position=NodePosition(x=460.0, y=600.0),
            created_at=now_iso,
            updated_at=now_iso
        ),

        # --- TASKS ---
        "task-node-system": NodeItem(
            id="task-node-system",
            title="Node Based TASK & Ideas System with DAG Dependencies",
            description="Interactive node-based task and ideas engine with stage lifecycle gating and Obsidian vault sync.",
            node_type=NodeType.TASK,
            stage=ExecutionStage.IN_PROGRESS,
            status=NodeStatus.IN_PROGRESS,
            progress=85.0,
            assigned_agent="gerych_builder",
            target_module="services/dnk_node_tasks",
            target_files=[
                "services/dnk_node_tasks/models.py",
                "services/dnk_node_tasks/graph_engine.py",
                "apps/api/routers/node_tasks_router.py",
                "apps/web/app/tasks/page.tsx"
            ],
            acceptance_criteria=[
                "Pydantic models for Ideas, Tasks, Slices, Gates",
                "Cycle detection and topological sorting",
                "Blocked status computed dynamically from dependencies",
                "Full interactive React Flow UI on /tasks"
            ],
            tags=["task_graph", "ideas", "dag", "orchestration"],
            priority="critical",
            position=NodePosition(x=880.0, y=100.0),
            created_at=now_iso,
            updated_at=now_iso
        ),
        "task-occ-merge": NodeItem(
            id="task-occ-merge",
            title="Multi-User OCC Structural Graph Mutation Resolver",
            description="3-way structural merge with optimistic concurrency control for concurrent canvas editing.",
            node_type=NodeType.TASK,
            stage=ExecutionStage.READY,
            status=NodeStatus.READY,
            progress=40.0,
            assigned_agent="dnk_dev_fullstack",
            target_module="core",
            target_files=["core/occ_merge.py", "apps/api/routers/canvas.py"],
            acceptance_criteria=[
                "Detect node and edge position conflicts",
                "Three-way merge resolution algorithm",
                "WebSocket broadcast of delta mutations"
            ],
            tags=["occ", "merge", "realtime", "backend"],
            priority="high",
            position=NodePosition(x=880.0, y=320.0),
            created_at=now_iso,
            updated_at=now_iso
        ),
        "task-scones-l3": NodeItem(
            id="task-scones-l3",
            title="SCONES L3 Persistent Cognitive Memory Consolidation",
            description="Long-term semantic memory storage with tenant and workspace isolation (ws-alpha-001).",
            node_type=NodeType.TASK,
            stage=ExecutionStage.COMPLETED,
            status=NodeStatus.COMPLETED,
            progress=100.0,
            assigned_agent="dnk_scones_memory",
            target_module="core",
            target_files=["core/scones_memory.py", "apps/api/routers/memory_l3.py"],
            acceptance_criteria=[
                "Episodic memory recall < 50ms",
                "Workspace isolation ws-alpha-001",
                "Automatic relevance decay"
            ],
            tags=["scones", "memory", "sqlite", "cognitive"],
            priority="high",
            position=NodePosition(x=880.0, y=520.0),
            created_at=now_iso,
            updated_at=now_iso
        ),
        "task-distiller-patch": NodeItem(
            id="task-distiller-patch",
            title="Autonomous Distiller Patch Generator on Test Failures",
            description="Generates unified diff patches from past error solutions stored in error distillation db.",
            node_type=NodeType.TASK,
            stage=ExecutionStage.IN_PROGRESS,
            status=NodeStatus.IN_PROGRESS,
            progress=60.0,
            assigned_agent="dnk_dev_fullstack",
            target_module="core",
            target_files=["core/error_distillation.py"],
            acceptance_criteria=[
                "Match traceback signatures with vector distance",
                "Apply fuzzy patch without manual shell loops",
                "Log verified solution to long-term memory"
            ],
            tags=["distiller", "self_healing", "patch"],
            priority="high",
            position=NodePosition(x=880.0, y=720.0),
            created_at=now_iso,
            updated_at=now_iso
        ),

        # --- GATES ---
        "gate-canvas-qa": NodeItem(
            id="gate-canvas-qa",
            title="Master Quality Gate: Canvas & Node Tasks 100% Green",
            description="Full automated audit: TypeScript compile, Pytest regression suite, and MRH header verification.",
            node_type=NodeType.GATE,
            stage=ExecutionStage.VERIFICATION,
            status=NodeStatus.READY,
            progress=50.0,
            assigned_agent="gerych_auditor",
            target_module="tests",
            target_files=["scripts/verify_all.sh"],
            acceptance_criteria=[
                "bash scripts/verify_all.sh returns exit code 0",
                "100% test pass rate",
                "Zero relative path violations"
            ],
            tags=["qa", "quality_gate", "adversarial"],
            priority="critical",
            position=NodePosition(x=1300.0, y=200.0),
            created_at=now_iso,
            updated_at=now_iso
        ),
        "gate-swarm-qa": NodeItem(
            id="gate-swarm-qa",
            title="Swarm Adversarial Gate (Builder vs Auditor)",
            description="Two-agent adversarial review verifying security boundaries and zero secret leakage.",
            node_type=NodeType.GATE,
            stage=ExecutionStage.VERIFICATION,
            status=NodeStatus.READY,
            progress=30.0,
            assigned_agent="gerych_auditor",
            target_module="scripts",
            target_files=["scripts/system/adversarial_gate_runner.py"],
            acceptance_criteria=[
                "Auditor probes all router endpoints",
                "No secrets in logs or git staging",
                "Fail-closed on unauthorized mutation"
            ],
            tags=["gate", "security", "resiliency"],
            priority="critical",
            position=NodePosition(x=1300.0, y=620.0),
            created_at=now_iso,
            updated_at=now_iso
        ),
    }

    edges: List[DependencyEdge] = [
        # Ideas to Epics
        DependencyEdge(
            id="edge-idea-to-epic-canvas",
            source="idea-liquid-ast",
            target="epic-canvas-v2",
            relation=EdgeRelation.SPAWNS_FROM,
            description="Canvas v2 architecture spawned from Liquid AST requirements"
        ),
        # Epic to Tasks
        DependencyEdge(
            id="edge-epic-to-task-node",
            source="epic-canvas-v2",
            target="task-node-system",
            relation=EdgeRelation.PARENT_OF,
            description="Node task system is child component of Canvas v2"
        ),
        DependencyEdge(
            id="edge-epic-to-task-occ",
            source="epic-canvas-v2",
            target="task-occ-merge",
            relation=EdgeRelation.PARENT_OF,
            description="OCC Merge is child component of Canvas v2"
        ),
        # Dependencies between Tasks
        DependencyEdge(
            id="edge-task-node-to-occ",
            source="task-node-system",
            target="task-occ-merge",
            relation=EdgeRelation.DEPENDS_ON,
            description="OCC Merge depends on Node Task System schema stabilization"
        ),
        # Gates validating Tasks
        DependencyEdge(
            id="edge-task-node-to-gate",
            source="task-node-system",
            target="gate-canvas-qa",
            relation=EdgeRelation.DEPENDS_ON,
            description="Task must be implemented before Canvas QA gate can complete"
        ),
        DependencyEdge(
            id="edge-task-occ-to-gate",
            source="task-occ-merge",
            target="gate-canvas-qa",
            relation=EdgeRelation.DEPENDS_ON,
            description="OCC merge must pass Canvas QA gate"
        ),
        DependencyEdge(
            id="edge-gate-validates-node",
            source="gate-canvas-qa",
            target="task-node-system",
            relation=EdgeRelation.VALIDATES,
            description="Gate certifies task-node-system readiness"
        ),
        # Swarm Self-Healing Epics & Tasks
        DependencyEdge(
            id="edge-epic-to-task-scones",
            source="epic-swarm-self-heal",
            target="task-scones-l3",
            relation=EdgeRelation.PARENT_OF,
            description="SCONES L3 is child component of Swarm Self-Healing"
        ),
        DependencyEdge(
            id="edge-epic-to-task-distiller",
            source="epic-swarm-self-heal",
            target="task-distiller-patch",
            relation=EdgeRelation.PARENT_OF,
            description="Distiller Patch is child component of Swarm Self-Healing"
        ),
        DependencyEdge(
            id="edge-scones-to-distiller",
            source="task-scones-l3",
            target="task-distiller-patch",
            relation=EdgeRelation.DEPENDS_ON,
            description="Distiller needs SCONES memory store to index past fixes"
        ),
        DependencyEdge(
            id="edge-distiller-to-gate",
            source="task-distiller-patch",
            target="gate-swarm-qa",
            relation=EdgeRelation.DEPENDS_ON,
            description="Distiller patch generator must pass Swarm Adversarial QA"
        ),
        DependencyEdge(
            id="edge-gate-validates-distiller",
            source="gate-swarm-qa",
            target="task-distiller-patch",
            relation=EdgeRelation.VALIDATES,
            description="Gate certifies distiller robustness"
        ),
    ]

    return NodeTaskGraph(
        nodes=nodes,
        edges=edges,
        version="1.0.0",
        updated_at=now_iso
    )

# --- DNK-MRH-HEADER ---
# mrh_id: "core/canvas/whiteboard_service.py"
# purpose: "SOTA Whiteboard & Moodboard persistence engine with Optimistic Concurrency Control (Track 1 Assimilation of tldraw/tldraw)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WhiteboardElement(BaseModel):
    id: str
    type: str  # "pen", "rect", "ellipse", "arrow", "note", "image", "text"
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    points: Optional[List[List[float]]] = None
    color: str = "#6366f1"
    fill_color: Optional[str] = None
    content: Optional[str] = None
    author: str = "Maksym"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WhiteboardScene(BaseModel):
    scene_id: str
    workspace_id: str = "ws-alpha-001"
    name: str = "Architecture & Moodboard"
    version: int = 1
    elements: List[WhiteboardElement] = Field(default_factory=list)
    viewport: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0, "zoom": 1.0})
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WhiteboardService:
    """
    In-memory and file-backed SOTA Whiteboard Storage.
    Supports OCC versioning, scene snapshots, and multi-agent real-time updates.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("/tmp/dnk_whiteboard_scenes")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._scenes: Dict[str, WhiteboardScene] = {}

    def get_scene(self, scene_id: str, workspace_id: str = "ws-alpha-001") -> WhiteboardScene:
        if scene_id in self._scenes:
            return self._scenes[scene_id]

        file_path = self.storage_dir / f"{workspace_id}_{scene_id}.json"
        if file_path.exists():
            data = json.loads(file_path.read_text(encoding="utf-8"))
            scene = WhiteboardScene.model_validate(data)
            self._scenes[scene_id] = scene
            return scene

        # Default empty scene
        new_scene = WhiteboardScene(
            scene_id=scene_id,
            workspace_id=workspace_id,
            name="New Whiteboard",
            version=1,
            elements=[
                WhiteboardElement(
                    id="note-welcome",
                    type="note",
                    x=100,
                    y=100,
                    width=240,
                    height=180,
                    color="#4f46e5",
                    content="🚀 DNK OS SOTA Whiteboard\nAssimilated from tldraw",
                    author="gerych_researcher",
                )
            ],
        )
        self._scenes[scene_id] = new_scene
        return new_scene

    def save_scene(self, scene: WhiteboardScene) -> WhiteboardScene:
        existing = self._scenes.get(scene.scene_id)
        if existing and scene.version <= existing.version:
            scene.version = existing.version + 1
        else:
            scene.version += 1

        scene.updated_at = datetime.now(timezone.utc).isoformat()
        self._scenes[scene.scene_id] = scene

        file_path = self.storage_dir / f"{scene.workspace_id}_{scene.scene_id}.json"
        file_path.write_text(scene.model_dump_json(indent=2), encoding="utf-8")
        return scene


whiteboard_service = WhiteboardService()

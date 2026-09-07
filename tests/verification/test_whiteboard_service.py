# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_whiteboard_service.py"
# purpose: "Unit tests verifying SOTA Whiteboard service OCC persistence and element manipulation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import sys
import uuid
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MVP_PATH = HUB_ROOT
if str(MVP_PATH) not in sys.path:
    sys.path.insert(0, str(MVP_PATH))

from core.canvas.whiteboard_service import (
    whiteboard_service,
    WhiteboardScene,
    WhiteboardElement,
)


def test_whiteboard_service_lifecycle_and_occ():
    unique_suffix = uuid.uuid4().hex[:8]
    scene_id = f"test-wb-{unique_suffix}"
    ws_id = "ws-alpha-001"

    # 1. Fetch initial scene
    scene = whiteboard_service.get_scene(scene_id, workspace_id=ws_id)
    assert isinstance(scene, WhiteboardScene)
    assert scene.scene_id == scene_id
    assert len(scene.elements) >= 1
    assert scene.version == 1

    # 2. Add elements
    new_el = WhiteboardElement(
        id=f"note-{unique_suffix}",
        type="note",
        x=300,
        y=200,
        width=200,
        height=150,
        color="#10b981",
        content="TikTok Ad Hook: Stop scrolling!",
        author="dnk_marketing_cmo",
    )
    scene.elements.append(new_el)

    # 3. Save scene (OCC increment)
    saved = whiteboard_service.save_scene(scene)
    assert saved.version == 2
    assert len(saved.elements) == 2

    # 4. Fetch from service and verify persistence
    fetched = whiteboard_service.get_scene(scene_id, workspace_id=ws_id)
    assert fetched.version == 2
    assert len(fetched.elements) == 2
    assert fetched.elements[1].author == "dnk_marketing_cmo"

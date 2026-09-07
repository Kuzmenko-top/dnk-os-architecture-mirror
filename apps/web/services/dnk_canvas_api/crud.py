# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_canvas_api/crud.py"
# purpose: "CRUD & Delta Sync operations for PostgreSQL 16 (hub_memory schema) Canvas Documents & Revisions"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import func


def compute_scene_checksum(scene: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 for a scene dictionary."""
    scene_str = json.dumps(scene, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(scene_str.encode("utf-8")).hexdigest()


def get_or_create_canvas_doc(
    db: Session,
    canvas_id: str,
    workspace_id: str = "ws-alpha-001",
    name: str = "DNK Studio Canvas"
):
    """Retrieve an existing CanvasDocument or create a new one in hub_memory."""
    # Import locally to avoid circular dependencies
    from services.dnk_canvas_api.main import CanvasDocument, CanvasRevision

    doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
    if not doc:
        now = datetime.now(timezone.utc)
        doc = CanvasDocument(
            id=canvas_id,
            workspace_id=workspace_id,
            name=name,
            current_revision_id=None,
            created_at=now,
            updated_at=now,
            is_archived=False,
            excalidraw_version=2,
            meta={"created_via": "dnk_studio_canvas_crud"}
        )
        db.add(doc)
        db.flush()

        # Create initial baseline revision (revision 0)
        initial_scene = {
            "type": "dnk_studio_canvas",
            "nodes": [],
            "edges": [],
            "sketches": [],
            "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0}
        }
        checksum = compute_scene_checksum(initial_scene)
        initial_rev = CanvasRevision(
            id=str(uuid4()),
            document_id=canvas_id,
            revision_number=0,
            scene_json=initial_scene,
            scene_checksum=checksum,
            created_by="system",
            created_at=now,
            change_summary="Initial canvas creation",
            parent_revision_id=None
        )
        db.add(initial_rev)
        db.flush()

        doc.current_revision_id = initial_rev.id
        db.commit()
        db.refresh(doc)
    return doc


def get_canvas_full_state(
    db: Session,
    canvas_id: str,
    workspace_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Fetch complete canvas state with latest revision and scene content."""
    from services.dnk_canvas_api.main import CanvasDocument, CanvasRevision

    query = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id)
    if workspace_id:
        query = query.filter(CanvasDocument.workspace_id == workspace_id)
    doc = query.first()
    if not doc:
        return None

    current_rev = None
    if doc.current_revision_id:
        current_rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()

    scene = current_rev.scene_json if current_rev else {
        "nodes": [],
        "edges": [],
        "sketches": [],
        "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0}
    }

    return {
        "id": doc.id,
        "name": doc.name,
        "workspace_id": doc.workspace_id,
        "revision_number": current_rev.revision_number if current_rev else 0,
        "revision_id": doc.current_revision_id,
        "scene": scene,
        "checksum": current_rev.scene_checksum if current_rev else "",
        "updated_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else str(doc.updated_at),
        "is_archived": doc.is_archived
    }


def apply_delta_sync(
    db: Session,
    canvas_id: str,
    delta: Dict[str, Any],
    actor_id: str = "system",
    workspace_id: str = "ws-alpha-001"
) -> Dict[str, Any]:
    """
    Apply incremental delta changes to canvas scene in PostgreSQL hub_memory.
    Implements Conflict Resolution via Last-Write-Wins (LWW) + Revision History tracking.
    """
    from services.dnk_canvas_api.main import CanvasDocument, CanvasRevision

    doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).with_for_update().first()
    if not doc:
        doc = get_or_create_canvas_doc(db, canvas_id, workspace_id)

    # Current revision
    current_rev = None
    current_rev_num = 0
    current_scene = {
        "type": "dnk_studio_canvas",
        "nodes": [],
        "edges": [],
        "sketches": [],
        "viewport": {"x": 0.0, "y": 0.0, "zoom": 1.0}
    }
    if doc.current_revision_id:
        current_rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()
        if current_rev and isinstance(current_rev.scene_json, dict):
            current_rev_num = current_rev.revision_number
            current_scene = dict(current_rev.scene_json)
            # Ensure keys exist
            for k in ["nodes", "edges", "sketches"]:
                if k not in current_scene:
                    current_scene[k] = []
            if "viewport" not in current_scene:
                current_scene["viewport"] = {"x": 0.0, "y": 0.0, "zoom": 1.0}

    # Conflict check
    client_rev = delta.get("client_revision")
    has_conflict = False
    conflict_notes = []
    if client_rev is not None and client_rev < current_rev_num:
        has_conflict = True
        conflict_notes.append(
            f"LWW resolution applied: client revision {client_rev} merged into server revision {current_rev_num}"
        )

    # Extract delta payload
    upsert_nodes = delta.get("upsert_nodes", [])
    delete_node_ids = set(delta.get("delete_node_ids", []))
    upsert_edges = delta.get("upsert_edges", [])
    delete_edge_ids = set(delta.get("delete_edge_ids", []))
    sketches = delta.get("sketches")
    viewport = delta.get("viewport")
    change_summary = delta.get("change_summary", "Delta sync update")

    # 1. Mutate Nodes
    node_map = {n["id"]: n for n in current_scene.get("nodes", []) if "id" in n}
    for n_id in delete_node_ids:
        node_map.pop(n_id, None)
    for node in upsert_nodes:
        if isinstance(node, dict) and "id" in node:
            node_map[node["id"]] = node
    current_scene["nodes"] = list(node_map.values())

    # 2. Mutate Edges
    edge_map = {e["id"]: e for e in current_scene.get("edges", []) if "id" in e}
    for e_id in delete_edge_ids:
        edge_map.pop(e_id, None)
    for edge in upsert_edges:
        if isinstance(edge, dict) and "id" in edge:
            edge_map[edge["id"]] = edge
    current_scene["edges"] = list(edge_map.values())

    # 3. Mutate Sketches (Whiteboard elements)
    if sketches is not None and isinstance(sketches, list):
        current_scene["sketches"] = sketches

    # 4. Mutate Viewport
    if viewport is not None and isinstance(viewport, dict):
        current_scene["viewport"] = viewport

    # 5. Compute new checksum
    new_checksum = compute_scene_checksum(current_scene)
    next_rev_num = current_rev_num + 1
    now = datetime.now(timezone.utc)

    # 6. Insert new CanvasRevision
    new_rev = CanvasRevision(
        id=str(uuid4()),
        document_id=canvas_id,
        revision_number=next_rev_num,
        scene_json=current_scene,
        scene_checksum=new_checksum,
        created_by=actor_id,
        created_at=now,
        change_summary=change_summary + (f" ({'; '.join(conflict_notes)})" if conflict_notes else ""),
        parent_revision_id=doc.current_revision_id
    )
    db.add(new_rev)
    db.flush()

    # 7. Update CanvasDocument head
    doc.current_revision_id = new_rev.id
    doc.updated_at = now
    db.commit()

    return {
        "success": True,
        "revision_number": next_rev_num,
        "revision_id": new_rev.id,
        "scene_checksum": new_checksum,
        "scene": current_scene,
        "has_conflict": has_conflict,
        "conflict_notes": conflict_notes,
        "updated_at": now.isoformat()
    }


def list_revision_history(
    db: Session,
    canvas_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Retrieve paginated revision history for time-travel & audit."""
    from services.dnk_canvas_api.main import CanvasRevision

    revs = (
        db.query(CanvasRevision)
        .filter(CanvasRevision.document_id == canvas_id)
        .order_by(CanvasRevision.revision_number.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    history = []
    for r in revs:
        history.append({
            "id": r.id,
            "revision_number": r.revision_number,
            "scene_checksum": r.scene_checksum,
            "change_summary": r.change_summary,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
            "parent_revision_id": r.parent_revision_id
        })
    return history


def get_revision_by_id(
    db: Session,
    canvas_id: str,
    revision_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieve full details of a specific revision."""
    from services.dnk_canvas_api.main import CanvasRevision

    r = db.query(CanvasRevision).filter(
        CanvasRevision.id == revision_id,
        CanvasRevision.document_id == canvas_id
    ).first()
    if not r:
        return None
    return {
        "id": r.id,
        "revision_number": r.revision_number,
        "scene": r.scene_json,
        "scene_checksum": r.scene_checksum,
        "change_summary": r.change_summary,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
        "parent_revision_id": r.parent_revision_id
    }


def restore_revision(
    db: Session,
    canvas_id: str,
    revision_id: str,
    actor_id: str = "system",
    workspace_id: str = "ws-alpha-001"
) -> Dict[str, Any]:
    """
    Restore a past revision as a new HEAD revision in PostgreSQL hub_memory.
    Enables undo beyond session boundaries.
    """
    from services.dnk_canvas_api.main import CanvasDocument, CanvasRevision

    doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).with_for_update().first()
    if not doc:
        raise ValueError("Canvas document not found")

    target_rev = db.query(CanvasRevision).filter(
        CanvasRevision.id == revision_id,
        CanvasRevision.document_id == canvas_id
    ).first()
    if not target_rev:
        raise ValueError("Target revision not found")

    current_rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()
    current_rev_num = current_rev.revision_number if current_rev else 0

    now = datetime.now(timezone.utc)
    next_rev_num = current_rev_num + 1

    restored_scene = target_rev.scene_json
    checksum = compute_scene_checksum(restored_scene)

    new_rev = CanvasRevision(
        id=str(uuid4()),
        document_id=canvas_id,
        revision_number=next_rev_num,
        scene_json=restored_scene,
        scene_checksum=checksum,
        created_by=actor_id,
        created_at=now,
        change_summary=f"Restored from revision #{target_rev.revision_number} ({revision_id[:8]})",
        parent_revision_id=doc.current_revision_id
    )
    db.add(new_rev)
    db.flush()

    doc.current_revision_id = new_rev.id
    doc.updated_at = now
    db.commit()

    return {
        "success": True,
        "restored_from_revision": target_rev.revision_number,
        "new_revision_number": next_rev_num,
        "revision_id": new_rev.id,
        "scene": restored_scene,
        "updated_at": now.isoformat()
    }

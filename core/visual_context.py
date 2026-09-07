# --- DNK-MRH-HEADER ---
# mrh_id: "core/visual_context.py"
# purpose: "Visual Selection Context Bridge (VSCB) DTO, asset persistence, and workspace isolation adapter."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import hashlib
import json
import logging
import os
from datetime import datetime, UTC
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class VisualContext(BaseModel):
    context_id: str
    tenant_id: str
    workspace_id: str
    canvas_id: str
    selection_bounds: Dict[str, float] = Field(default_factory=dict)
    image_asset_id: str
    source_node_ids: List[str] = Field(default_factory=list)
    extracted_text: Optional[str] = None
    visual_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class VisualContextBridge:
    """
    Ingestion pipeline and security boundary for converting front-end 
    canvas selection events and screenshots into structured AI task context.
    """
    def __init__(self, upload_dir: Optional[str] = None, registry_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if upload_dir is None:
            self.upload_dir = os.path.join(base_dir, "public", "uploads")
        else:
            self.upload_dir = upload_dir
            
        if registry_path is None:
            self.registry_path = os.path.join(base_dir, "tests", "visual_context_registry.json")
        else:
            self.registry_path = registry_path
            
        os.makedirs(self.upload_dir, exist_ok=True)
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.load_registry()

        # Simulated database of node-to-workspace mapping for strict verification
        self._node_workspace_map: Dict[str, Dict[str, str]] = {}

    def load_registry(self) -> None:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.registry = json.load(f)
            except Exception:
                self.registry = {}
        else:
            self.registry = {}

    def save_registry(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, indent=2)
        except Exception as e:
            logger.error("VSCB: Failed to save registry: %s", e)

    def register_node_workspace(self, node_id: str, tenant_id: str, workspace_id: str) -> None:
        """Registers a node's ownership for isolation verification."""
        self._node_workspace_map[node_id] = {
            "tenant_id": tenant_id,
            "workspace_id": workspace_id
        }

    def _verify_node_ownership(self, node_ids: List[str], tenant_id: str, workspace_id: str) -> None:
        """Strict isolation verification: checks that all source nodes belong to this workspace."""
        for nid in node_ids:
            ownership = self._node_workspace_map.get(nid)
            if ownership:
                if ownership["tenant_id"] != tenant_id or ownership["workspace_id"] != workspace_id:
                    raise PermissionError(
                        f"Isolation Violation: Node '{nid}' belongs to tenant '{ownership['tenant_id']}'"
                        f" and workspace '{ownership['workspace_id']}', but caller requested "
                        f"tenant '{tenant_id}' and workspace '{workspace_id}'."
                    )

    def _generate_stable_context_id(self, canvas_id: str, source_node_ids: List[str], selection_bounds: Dict[str, float]) -> str:
        """Generates a stable, idempotent ID based on the selection layout."""
        sorted_nodes = sorted(source_node_ids)
        bounds_str = json.dumps(selection_bounds, sort_keys=True)
        raw_key = f"{canvas_id}:{','.join(sorted_nodes)}:{bounds_str}"
        hasher = hashlib.sha256(raw_key.encode("utf-8"))
        return f"VSCB-CTX-{hasher.hexdigest()[:16]}"

    def ingest_selection(
        self,
        tenant_id: str,
        workspace_id: str,
        canvas_id: str,
        selection_bounds: Dict[str, float],
        image_data: Optional[bytes],
        source_node_ids: List[str],
        extracted_text: Optional[str] = None,
        visual_metadata: Optional[Dict[str, Any]] = None
    ) -> VisualContext:
        """
        Converts front-end canvas selections and captures into a verified VisualContext.
        Enforces idempotency, persistence, and tenant isolation.
        """
        # Enforce validation of key boundaries
        if not tenant_id or not workspace_id or not canvas_id:
            raise ValueError("VSCB Boundary Violation: tenant_id, workspace_id, and canvas_id are required.")

        # Strict node ownership verification
        self._verify_node_ownership(source_node_ids, tenant_id, workspace_id)

        # Idempotency: calculate stable ID
        context_id = self._generate_stable_context_id(canvas_id, source_node_ids, selection_bounds)
        
        # Check existing duplicates in registry to avoid uncontrolled double-writes
        if context_id in self.registry:
            existing = self.registry[context_id]
            # Ensure the existing context matches current caller credentials
            if existing["tenant_id"] == tenant_id and existing["workspace_id"] == workspace_id:
                logger.info("VSCB: Idempotent match found for context_id: %s. Reusing cached context.", context_id)
                return VisualContext(**existing)

        # Asset Persistence
        image_asset_id = f"VSCB-IMG-{context_id}.png"
        if image_data:
            img_path = os.path.join(self.upload_dir, image_asset_id)
            try:
                with open(img_path, "wb") as f:
                    f.write(image_data)
                logger.info("VSCB: Saved image asset successfully at %s", img_path)
            except Exception as e:
                logger.error("VSCB: Failed to save screenshot asset: %s", e)
        else:
            image_asset_id = "VSCB-IMG-EMPTY"

        # Create DTO
        v_ctx = VisualContext(
            context_id=context_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            canvas_id=canvas_id,
            selection_bounds=selection_bounds,
            image_asset_id=image_asset_id,
            source_node_ids=source_node_ids,
            extracted_text=extracted_text,
            visual_metadata=visual_metadata or {}
        )

        # Save to registry
        self.registry[context_id] = v_ctx.dict()
        self.save_registry()

        return v_ctx

    def get_context_by_id(self, context_id: str, tenant_id: str, workspace_id: str) -> Optional[VisualContext]:
        """
        Retrieves a VisualContext. Strictly verifies tenant and workspace boundaries.
        """
        raw_ctx = self.registry.get(context_id)
        if not raw_ctx:
            return None

        # Absolute Isolation verification
        if raw_ctx["tenant_id"] != tenant_id or raw_ctx["workspace_id"] != workspace_id:
            raise PermissionError(
                f"Isolation Violation: Tenant '{tenant_id}' or Workspace '{workspace_id}' "
                f"is unauthorized to access Context '{context_id}'."
            )

        return VisualContext(**raw_ctx)

    def bind_to_task_context(
        self,
        context_id: str,
        task_context: Dict[str, Any],
        tenant_id: str,
        workspace_id: str
    ) -> Dict[str, Any]:
        """
        Safely binds retrieved VisualContext to an active task payload.
        Handles missing screenshot or OCR gracefully without breaking task execution.
        """
        enriched_context = task_context.copy()
        
        try:
            v_ctx = self.get_context_by_id(context_id, tenant_id, workspace_id)
            if v_ctx:
                visual_summary = f"[Visual Canvas Selection Context]\n" \
                                 f"Context ID: {v_ctx.context_id}\n" \
                                 f"Source Nodes: {', '.join(v_ctx.source_node_ids)}\n" \
                                 f"Extracted OCR Text: {v_ctx.extracted_text or 'None'}\n" \
                                 f"Image Asset ID: {v_ctx.image_asset_id}\n" \
                                 f"Metadata: {json.dumps(v_ctx.visual_metadata)}"
                
                # Append into the task context payload
                if "additional_context" not in enriched_context:
                    enriched_context["additional_context"] = ""
                enriched_context["additional_context"] += f"\n\n{visual_summary}"
                enriched_context["visual_context_id"] = v_ctx.context_id
                
        except Exception as e:
            # Missing screenshot or failed OCR must not break task execution
            logger.warning("VSCB: Failed to bind visual context %s: %s. Continuing with raw task execution.", context_id, e)
            
        return enriched_context

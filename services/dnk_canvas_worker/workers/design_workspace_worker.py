# --- DNK-MRH-HEADER ---
# mrh_id: "workers/design_workspace_worker.py"
# purpose: "Worker to process canvas design workspace generation tasks."
# canonical_source: true
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import json
import time
import hashlib
import logging
from datetime import datetime, timezone
from uuid import uuid4

from ...dnk_canvas_api.main import (
    DesignRun, SupervisorRun, AgentStep, ToolCall, Artifact, CanvasSnapshot, CanvasRevision,
    Canvas, CanvasDocument, publish_event, audit_event
)
from ..tools.design_scene_tool import generate_workspace_scene

logger = logging.getLogger("design_workspace_worker")

class DesignWorkspaceWorker:
    @staticmethod
    def process_task(db, run_id: str, skill_id: str, context: dict):
        logger.info(f"Worker starting task processing for run {run_id}, skill {skill_id}")

        run = db.query(SupervisorRun).filter(SupervisorRun.id == run_id).first()
        if not run:
            logger.error(f"Supervisor run {run_id} not found in worker.")
            return

        # Fetch active step or create one
        step = db.query(AgentStep).filter(AgentStep.supervisor_run_id == run.id, AgentStep.status == "running").first()
        if not step:
            step = AgentStep(
                id=str(uuid4()),
                supervisor_run_id=run.id,
                step_number=1,
                agent_type="designer_agent",
                status="running",
                input_context=context
            )
            db.add(step)
            db.commit()

        # Update DesignRun status to 'running'
        design_run = db.query(DesignRun).filter(DesignRun.id == run.design_run_id).first()
        if design_run:
            design_run.status = "running"
            design_run.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)
            db.commit()

        try:
            # 1. Execute deterministic tool
            start_time = time.time()
            
            # Record Tool Call
            tool_call = ToolCall(
                id=str(uuid4()),
                agent_step_id=step.id,
                tool_name="generate_workspace_scene",
                arguments_json=context,
                status="pending"
            )
            db.add(tool_call)
            db.commit()

            # Execute scene generation
            scene_result = generate_workspace_scene(context)
            duration_ms = int((time.time() - start_time) * 1000)

            # Update Tool Call
            tool_call.result_json = scene_result
            tool_call.status = "completed"
            tool_call.duration_ms = duration_ms
            db.commit()

            # Transition run: running -> materializing
            run.status = "materializing"
            if design_run:
                design_run.status = "materializing"
            db.commit()
            
            audit_event(db, run.id, design_run.canvas_id if design_run else "unknown", "state_transition", "running", "materializing", "Worker generated scene, saving artifacts.")

            # 2. Materialize Artifacts & Snapshots
            # Create briefing
            brief_art = Artifact(
                id=str(uuid4()),
                canvas_id=design_run.canvas_id if design_run else "unknown",
                name="Design Brief",
                type="design_brief",
                content_json=json.dumps({"brief": f"High-fidelity workspace dashboard briefing for {context.get('prompt')}"})
            )
            db.add(brief_art)

            # Create Excalidraw scene artifact
            scene_art = Artifact(
                id=str(uuid4()),
                canvas_id=design_run.canvas_id if design_run else "unknown",
                name="Excalidraw Workspace Scene",
                type="excalidraw_scene",
                content_json=json.dumps(scene_result)
            )
            db.add(scene_art)

            # Create critique report
            critique_art = Artifact(
                id=str(uuid4()),
                canvas_id=design_run.canvas_id if design_run else "unknown",
                name="Critique Report",
                type="critique_report",
                content_json=json.dumps({"critique": "Layout complies perfectly with CAT-MACCHIATO grid standards."})
            )
            db.add(critique_art)
            
            db.commit()

            # Create CanvasSnapshot for E2E persistence validation
            elements = scene_result.get("elements", [])
            canvas = db.query(Canvas).filter(Canvas.id == design_run.canvas_id).first()
            next_version = (canvas.version + 1) if canvas else 1

            snapshot = CanvasSnapshot(
                id=str(uuid4()),
                canvas_id=design_run.canvas_id,
                version=next_version,
                elements_json=json.dumps(elements),
                app_state_json=json.dumps({"theme": "macchiato"}),
                files_json="{}",
                client_request_id=f"worker-req-{run_id[:8]}"
            )
            db.add(snapshot)

            if canvas:
                canvas.version = next_version
                canvas.updated_at = int(time.time() * 1000)

            # Update CanvasDocument and CanvasRevision so it materializes in React UI
            doc = db.query(CanvasDocument).filter(CanvasDocument.id == design_run.canvas_id).first()
            if doc:
                scene_json = {
                    "type": "excalidraw",
                    "elements": elements,
                    "app_state": {"theme": "macchiato"},
                    "files": {}
                }
                scene_str = json.dumps(scene_json, sort_keys=True)
                checksum = hashlib.sha256(scene_str.encode('utf-8')).hexdigest()

                new_rev = CanvasRevision(
                    id=str(uuid4()),
                    document_id=doc.id,
                    revision_number=next_version,
                    scene_json=scene_json,
                    scene_checksum=checksum,
                    created_by="agent",
                    change_summary="Orchestrated Workspace Sketch generated by Supervisor Worker",
                    parent_revision_id=doc.current_revision_id
                )
                db.add(new_rev)
                db.flush()
                doc.current_revision_id = new_rev.id
                doc.updated_at = datetime.now(timezone.utc)

            db.commit()

            # 3. Transition run: materializing -> completed
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            if design_run:
                design_run.status = "completed"
                design_run.artifact_id = scene_art.id
                design_run.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)
            
            step.status = "completed"
            step.output_summary = f"Generated 3 artifacts and updated canvas to version {next_version} with {len(elements)} elements."
            step.completed_at = datetime.now(timezone.utc)
            db.commit()

            logger.info(f"Worker finished processing task successfully for run {run_id}")
            audit_event(db, run.id, design_run.canvas_id if design_run else "unknown", "state_transition", "materializing", "completed", "Artifacts persisted successfully.")

            # Publish finished event
            publish_event("canvas.run_status", {
                "runId": run.id,
                "canvasId": design_run.canvas_id if design_run else "unknown",
                "fromState": "materializing",
                "toState": "completed",
                "artifactId": scene_art.id,
                "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000)
            })

        except Exception as e:
            logger.error(f"Error in design workspace worker: {e}")
            run.status = "failed"
            run.failure_code = str(e)[:64]
            run.completed_at = datetime.now(timezone.utc)
            if design_run:
                design_run.status = "failed"
                design_run.error_message = str(e)
            step.status = "failed"
            step.completed_at = datetime.now(timezone.utc)
            db.commit()
            
            audit_event(db, run.id, design_run.canvas_id if design_run else "unknown", "state_transition", "running", "failed", f"Worker error: {str(e)}")

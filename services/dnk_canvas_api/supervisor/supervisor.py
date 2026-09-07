# --- DNK-MRH-HEADER ---
# mrh_id: "supervisor/supervisor.py"
# purpose: "DNK Supervisor layer coordinating skill resolution, policy check, model gateway, validation, and dispatcher."
# canonical_source: true
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

from ..main import (
    DesignRun, SupervisorRun, AgentStep, ToolCall, DesignContext, ArtifactReview,
    DesignValidationResult, SessionLocal, publish_event, audit_event, CanvasDocument
)
from .state_machine import SupervisorStateMachine, InvalidStateTransitionException
from .policy_gate import PolicyGate, PolicyViolationException
from .context_builder import ContextBuilder
from .dispatcher import WorkerDispatcher
from .validation import StructuredDesignValidator
from ..skills.registry import registry

logger = logging.getLogger("dnk_supervisor")

class DNKSupervisor:
    def __init__(self, r_client=None):
        self.dispatcher = WorkerDispatcher(r_client)

    def transition_supervisor_run(self, db, run: SupervisorRun, to_state: str, error_msg: Optional[str] = None):
        from_state = run.status
        try:
            SupervisorStateMachine.validate_transition(from_state, to_state)
        except InvalidStateTransitionException as e:
            logger.error(str(e))
            raise e

        run.status = to_state
        if to_state in ["completed", "failed", "cancelled"]:
            run.completed_at = datetime.now(timezone.utc)
        if error_msg:
            run.failure_code = error_msg[:64]
        db.commit()

        # Update primary DesignRun as well
        design_run = db.query(DesignRun).filter(DesignRun.id == run.design_run_id).first()
        if design_run:
            design_run.status = to_state
            design_run.error_message = error_msg
            design_run.updated_at = int(datetime.now(timezone.utc).timestamp() * 1000)
            db.commit()

        # Audit and publish
        audit_event(db, run.id, design_run.canvas_id if design_run else "unknown", "state_transition", from_state, to_state, error_msg or f"Transition to {to_state}")

    def create_supervisor_run(self, db, design_run_id: str, canvas_id: str, payload: Dict[str, Any]) -> SupervisorRun:
        run = SupervisorRun(
            id=str(uuid4()),
            design_run_id=design_run_id,
            workflow_id=payload.get("workflow_id", "default_workflow"),
            status="queued",
            current_step=0,
            supervisor_version="1.0.0",
            model_policy="gemma-4"
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    async def execute_run_workflow_async(self, db, run_id: str):
        run = db.query(SupervisorRun).filter(SupervisorRun.id == run_id).first()
        if not run:
            logger.error(f"Supervisor run {run_id} not found.")
            return

        design_run = db.query(DesignRun).filter(DesignRun.id == run.design_run_id).first()
        if not design_run:
            logger.error(f"Design run {run.design_run_id} not found.")
            return

        payload = design_run.payload_json
        try:
            payload_dict = json.loads(payload)
        except Exception:
            payload_dict = {}

        try:
            # 1. queued -> planning
            self.transition_supervisor_run(db, run, "planning")

            # 2. Skill Resolution
            skill_id = payload_dict.get("skill_id", "dnk.ui.generate_workspace")
            skill = registry.get_skill(skill_id)
            if not skill:
                raise ValueError(f"Skill '{skill_id}' is not registered in the Skill Registry.")

            # 3. Policy Gate check
            PolicyGate.check_skill_risk(skill_id, skill.contract.risk_level, approved=False)

            # 4. Context Builder
            context = ContextBuilder.build_context(
                db,
                project_id=payload_dict.get("project_id", str(uuid4())),
                canvas_id=design_run.canvas_id,
                prompt=payload_dict.get("prompt", "Створи головний екран кабінету DNK OS"),
                design_system_id=payload_dict.get("design_system_id", "dnk-default")
            )

            # Save Context to DB
            design_ctx = DesignContext(
                id=str(uuid4()),
                supervisor_run_id=run.id,
                project_id=context["project_id"],
                canvas_id=context["canvas_id"],
                prompt=context["prompt"],
                design_system_id=context["design_system_id"],
                collected_data=context
            )
            db.add(design_ctx)
            db.commit()

            # 5. planning -> running
            self.transition_supervisor_run(db, run, "running")

            # Check LLM Mode: vertex, claude, shadow, validated, fixture (fallback)
            llm_mode = os.getenv("LLM_PROVIDER_MODE", "fixture").lower()
            
            # Retrieve Canvas Document to inspect workspace matching for canary validation
            doc = db.query(CanvasDocument).filter(CanvasDocument.id == design_run.canvas_id).first()
            workspace_id = doc.workspace_id if doc else None
            canary_workspace_id = os.getenv("LLM_CANARY_WORKSPACE_ID")
            
            # Validated/Canary mode: active live mode only if active workspace matches canary workspace or is whitelisted
            if llm_mode == "validated":
                whitelisted_env = os.getenv("LLM_WHITELISTED_WORKSPACES", "")
                whitelisted_ids = [w.strip() for w in whitelisted_env.split(",") if w.strip()]
                
                if (canary_workspace_id and workspace_id == canary_workspace_id) or (workspace_id in whitelisted_ids):
                    logger.info(f"Workspace Match: Workspace '{workspace_id}' is active for validated rollout. Running in Live mode.")
                else:
                    logger.info(f"No Match: Workspace '{workspace_id}' is not in canary/whitelist. Degrading to Shadow mode.")
                    llm_mode = "shadow"
            
            if llm_mode in ["vertex", "claude", "shadow", "validated"]:
                # Transition running -> model_requested
                self.transition_supervisor_run(db, run, "model_requested")

                # Lazy import gateway to avoid circular imports
                from ..model_gateway.gateway import DNKModelGateway
                system_prompt = "You are a master UI/UX layout compiler for DNK OS."
                messages = [{"role": "user", "content": context["prompt"]}]

                # Call model gateway
                result = await DNKModelGateway.request_generation(
                    db=db,
                    supervisor_run_id=run.id,
                    system_prompt=system_prompt,
                    messages=messages,
                    response_schema=StructuredDesignValidator.SCHEMA
                )

                # Transition model_requested -> model_completed -> validating
                self.transition_supervisor_run(db, run, "model_completed")
                self.transition_supervisor_run(db, run, "validating")

                # Validate design
                passed, errs = StructuredDesignValidator.validate_design(result.output)
                
                # Log Validation Results
                val_res = DesignValidationResult(
                    id=str(uuid4()),
                    supervisor_run_id=run.id,
                    status="passed" if passed else "failed",
                    errors_json=errs
                )
                db.add(val_res)
                db.commit()

                if not passed:
                    raise ValueError(f"schema_validation_failed: {'; '.join(errs)}")

                # Transition validating -> tool_pending
                self.transition_supervisor_run(db, run, "tool_pending")

                if llm_mode == "shadow":
                    logger.info("Shadow mode: Logging success but bypassing actual materialization.")
                    # Fallback to deterministic dispatch so the E2E is preserved
                    self.dispatcher.dispatch_to_worker(run.id, skill_id, context)
                else:
                    # Materialize actual elements from structured output in vertex/claude mode
                    self.dispatcher.dispatch_to_worker(run.id, skill_id, result.output)

            else:
                # Local Thread / Fixture Fallback Mode
                # Create step
                step = AgentStep(
                    id=str(uuid4()),
                    supervisor_run_id=run.id,
                    step_number=1,
                    agent_type="supervisor",
                    status="running",
                    input_context=context
                )
                db.add(step)
                db.commit()

                self.dispatcher.dispatch_to_worker(run.id, skill_id, context)

        except PolicyViolationException as e:
            logger.error(f"Policy violation: {e}")
            self.transition_supervisor_run(db, run, "failed", error_msg=f"POLICY_VIOLATION: {str(e)}")
        except Exception as e:
            logger.error(f"Supervisor error executing workflow: {e}")
            err_msg = str(e)
            if "schema_validation_failed" in err_msg:
                self.transition_supervisor_run(db, run, "failed", error_msg="schema_validation_failed")
            else:
                self.transition_supervisor_run(db, run, "failed", error_msg=err_msg)

    def execute_run_workflow(self, db, run_id: str):
        # Synchronous wrapper for background tasks compatibility
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            asyncio.ensure_future(self.execute_run_workflow_async(db, run_id))
        else:
            loop.run_until_complete(self.execute_run_workflow_async(db, run_id))

    def recover_incomplete_runs(self, db):
        incomplete = db.query(SupervisorRun).filter(SupervisorRun.status.in_(["queued", "planning", "running"])).all()
        for run in incomplete:
            logger.info(f"Recovering incomplete run {run.id} with status {run.status}")
            self.transition_supervisor_run(db, run, "failed", error_msg="RECOVERY_RESET: Process restarted.")

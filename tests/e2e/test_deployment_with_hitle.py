# --- DNK-MRH-HEADER ---
# mrh_id: "tests/e2e/test_deployment_with_hitle.py"
# purpose: "E2E deployment scenario with HITL approval gate integration tests"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from dnk_os.core.supervisor import DNKSupervisor
from dnk_os.core.worker import DNKWorker
from dnk_os.core.approval_gate import DNKApprovalGate, ApprovalStatus


class TestDeploymentWithHITL:
    """E2E Test suite for deployment scenarios requiring Human-in-the-Loop approval."""

    def test_deployment_with_hitle(self):
        """Test deployment scenario with approval gate workflow."""
        supervisor = DNKSupervisor(name="Antigravity")
        worker = DNKWorker(name="Герич", capabilities=["deploy"])
        approval_gate = DNKApprovalGate(checkpointer_backend="memory")

        supervisor.register_worker(
            worker_name="Герич",
            worker_config={"name": "Герич"},
            capabilities=["deploy"],
        )
        supervisor.create_state_graph()
        supervisor.compile()

        thread_id = "thread_deploy_001"

        # Step 1: Request approval for sensitive deployment action
        request_id = approval_gate.request_approval(
            action="deploy",
            context={"environment": "production", "version": "1.0.0"},
            thread_id=thread_id,
        )
        assert request_id is not None

        # Verify initial status is PENDING
        initial_status = approval_gate.get_approval_status(request_id=request_id, thread_id=thread_id)
        assert initial_status == ApprovalStatus.PENDING

        # Step 2: Human Approver approves request
        approved = approval_gate.approve(
            request_id=request_id,
            thread_id=thread_id,
            approver_id="admin",
            comments="Approved deployment to production",
        )
        assert approved is True

        # Step 3: Verify approval status updated to APPROVED
        status = approval_gate.get_approval_status(request_id=request_id, thread_id=thread_id)
        assert status == ApprovalStatus.APPROVED

        # Step 4: Execute deployment via Supervisor after approval
        deploy_res = supervisor.delegate_task(
            task="Deploy v1.0.0 to production",
            selected_worker="Герич",
            thread_id=thread_id,
        )
        assert deploy_res["status"] in ["completed", "success"]
        assert deploy_res["worker"] == "Герич"

    def test_deployment_rejection_flow(self):
        """Test deployment scenario rejection workflow."""
        approval_gate = DNKApprovalGate(checkpointer_backend="memory")
        thread_id = "thread_deploy_002"

        request_id = approval_gate.request_approval(
            action="deploy_critical",
            context={"env": "prod"},
            thread_id=thread_id,
        )

        rejected = approval_gate.reject(
            request_id=request_id,
            thread_id=thread_id,
            approver_id="security_lead",
            reason="Security review incomplete",
        )
        assert rejected is True

        status = approval_gate.get_approval_status(request_id=request_id, thread_id=thread_id)
        assert status == ApprovalStatus.REJECTED

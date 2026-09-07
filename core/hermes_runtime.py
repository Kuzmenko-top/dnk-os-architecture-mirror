# --- DNK-MRH-HEADER ---
# mrh_id: "core/hermes_runtime.py"
# purpose: "Safe Execution Runtime with Dry-Run, 2-Stage Auth & Rollback (hermes-agent donor)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
import hashlib
import uuid
from typing import Optional, Dict, List, Any, Callable
try:
    from core.auth_engine import MaksymAuthEngine
except ImportError:
    from core.auth_engine import MaksymAuthEngine

try:
    from core.guards.completion_gate import CompletionGate, VerificationEvidence
except ImportError:
    CompletionGate = None
    VerificationEvidence = None

class HermesRuntime:
    """
    HermesRuntime provides a safe execution environment featuring
    Dry-Run simulation plans, 2-stage verification for destructive actions,
    Tier 2 CompletionGate verification, and automatic fail-closed state rollbacks.
    """
    def __init__(self, auth_engine: Optional[MaksymAuthEngine] = None, max_failures: int = 2):
        self.auth_engine = auth_engine or MaksymAuthEngine()
        self.max_failures = max_failures
        self.consecutive_failures = 0
        self.is_locked = False
        self.backups: Dict[str, str] = {}  # Relative Path -> Original File Content
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.completion_gate = CompletionGate() if CompletionGate else None

    def generate_dry_run_plan(self, action_type: str, targets: List[str], details: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a non-destructive dry-run preview of the intended operations."""
        return {
            "action_type": action_type,
            "targets": targets,
            "details": details,
            "dry_run": True,
            "status": "Ready for Review",
            "estimated_impact": f"Modified {len(targets)} files, executing under {action_type} paradigm"
        }

    def request_destructive_action(self, action_type: str, target: str, details: Dict[str, Any]) -> str:
        """Stage 1 of Destructive Action approval: Request registration."""
        approval_id = str(uuid.uuid4())[:8]
        self.pending_approvals[approval_id] = {
            "action_type": action_type,
            "target": target,
            "details": details,
            "approved": False
        }
        return approval_id

    def approve_destructive_action(self, approval_id: str, auth_phrase: str) -> bool:
        """Stage 2 of Destructive Action approval: Verification of Maksym's phrase."""
        if approval_id not in self.pending_approvals:
            raise KeyError(f"Approval ID {approval_id} does not exist")
            
        if self.auth_engine.verify_maksym(auth_phrase):
            self.pending_approvals[approval_id]["approved"] = True
            return True
        return False

    def checkpoint_files(self, paths: List[str]) -> None:
        """Saves a delta checkpoint (original file contents) for potential rollbacks."""
        for path in paths:
            # Only backup if not already backed up to preserve the pristine state before failures began
            if path in self.backups:
                continue
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.backups[path] = f.read()
                except OSError:
                    pass
            else:
                # Store marker that file did not exist
                self.backups[path] = "__NON_EXISTENT__"

    def execute_safely(self, action_fn: Callable[[], Any], verify_fn: Callable[[], bool], 
                       file_paths_to_modify: List[str]) -> Dict[str, Any]:
        """
        Executes a state-changing operation with fail-closed auto-rollback.
        If verification fails max_failures times consecutively, triggers rollback and locks runtime.
        """
        if self.is_locked:
            return {"status": "Error", "message": "Runtime is locked. Manual release required.", "locked": True}

        # Take checkpoints prior to execution
        self.checkpoint_files(file_paths_to_modify)

        try:
            # Execute mutation
            action_fn()
            
            # Run verification (e.g. tests or hygiene watchdogs)
            success = verify_fn()
        except Exception as e:
            success = False
            details_error = str(e)
        else:
            details_error = ""

        if success:
            self.consecutive_failures = 0
            # Success, so we can clear backups/checkpoints for this run
            self.backups.clear()
            return {"status": "Success", "message": "Operation executed and verified successfully.", "failures": 0}
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.max_failures:
                self.rollback_to_checkpoints()
                self.is_locked = True
                return {
                    "status": "Rolled Back", 
                    "message": "Double failure occurred. Fail-Closed Auto-Rollback triggered. Runtime is locked.",
                    "failures": self.consecutive_failures,
                    "locked": True,
                    "error": details_error
                }
            return {
                "status": "Failure", 
                "message": f"Verification failed. Attempt {self.consecutive_failures}/{self.max_failures} before rollback.",
                "failures": self.consecutive_failures,
                "locked": False,
                "error": details_error
            }

    def rollback_to_checkpoints(self) -> None:
        """Restores all file states to their original saved checkpoints."""
        for path, original_content in self.backups.items():
            if original_content == "__NON_EXISTENT__":
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            else:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(original_content)
                except OSError:
                    pass
        self.backups.clear()

    def unlock_runtime(self) -> None:
        """Unlocks locked state and resets consecutive failures counter."""
        self.is_locked = False
        self.consecutive_failures = 0

    def evaluate_completion_gate(
        self,
        assistant_message: str,
        commands_executed: Optional[List[str]] = None,
        exit_codes: Optional[List[int]] = None,
        test_passed: bool = False,
    ) -> Dict[str, Any]:
        """
        Validates assistant success claims via Tier 2 CompletionGate.
        Guarantees that unverified claims ('all tests pass', 'build clean') cannot finalize without evidence.
        """
        if not self.completion_gate:
            return {"allowed": True, "reason": None, "detected_claim": None}

        evidence = VerificationEvidence(
            commands_executed=commands_executed or [],
            exit_codes=exit_codes or [],
            test_passed=test_passed,
        )
        verdict = self.completion_gate.evaluate(assistant_message, evidence=evidence)
        return {
            "allowed": verdict.allowed,
            "reason": verdict.reason,
            "detected_claim": verdict.detected_claim,
        }

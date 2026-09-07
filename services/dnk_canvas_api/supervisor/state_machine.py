# --- DNK-MRH-HEADER ---
# mrh_id: "supervisor/state_machine.py"
# purpose: "Implement extended state machine and valid state transitions for design runs."
# canonical_source: true
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from typing import Set, Dict

class InvalidStateTransitionException(Exception):
    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"409 INVALID_STATE_TRANSITION: Cannot transition from '{from_state}' to '{to_state}'")

class SupervisorStateMachine:
    # Set of valid states including new intermediate LLM workflow steps
    STATES = {
        "queued", "planning", "awaiting_context", "running", 
        "model_requested", "model_completed", "validating", "tool_pending",
        "waiting_approval", "materializing", "completed", "failed", 
        "cancelled", "expired"
    }

    # Dict of allowed transitions
    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        "queued": {"planning", "failed", "cancelled"},
        "planning": {"awaiting_context", "running", "failed", "cancelled"},
        "awaiting_context": {"running", "failed", "cancelled"},
        "running": {"model_requested", "waiting_approval", "materializing", "failed", "cancelled"},
        "model_requested": {"model_completed", "failed", "cancelled"},
        "model_completed": {"validating", "failed", "cancelled"},
        "validating": {"tool_pending", "materializing", "failed", "cancelled"},
        "tool_pending": {"materializing", "waiting_approval", "failed", "cancelled"},
        "waiting_approval": {"running", "tool_pending", "cancelled", "failed", "completed"},
        "materializing": {"completed", "failed"},
        "failed": {"queued"},
        "cancelled": set(),
        "completed": set(),
        "expired": set()
    }

    @classmethod
    def validate_transition(cls, from_state: str, to_state: str):
        if from_state not in cls.STATES:
            raise InvalidStateTransitionException(from_state, to_state)
        if to_state not in cls.STATES:
            raise InvalidStateTransitionException(from_state, to_state)
            
        allowed = cls.ALLOWED_TRANSITIONS.get(from_state, set())
        if to_state not in allowed and from_state != to_state:
            raise InvalidStateTransitionException(from_state, to_state)

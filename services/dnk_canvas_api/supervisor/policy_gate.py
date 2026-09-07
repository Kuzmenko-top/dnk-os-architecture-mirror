# --- DNK-MRH-HEADER ---
# mrh_id: "supervisor/policy_gate.py"
# purpose: "Implement policy gate to enforce execution limits, approvals, and risk level controls."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any

class PolicyViolationException(Exception):
    def __init__(self, message: str):
        super().__init__(f"403 POLICY_VIOLATION: {message}")

class PolicyGate:
    @staticmethod
    def check_skill_risk(skill_id: str, risk_level: str, approved: bool = False):
        if risk_level in ["L2", "L3", "L4"] and not approved:
            raise PolicyViolationException(f"Skill '{skill_id}' has risk level '{risk_level}' and requires explicit approval.")

    @staticmethod
    def validate_action(action_type: str, action_data: Dict[str, Any], risk_level: str, approved: bool = False):
        # Prevent restricted actions for L1/L0
        restricted_actions = {
            "github_push", "github_create_issue", "change_production_ui", 
            "send_email", "financial_transaction", "delete_project_data"
        }
        
        if action_type in restricted_actions:
            if risk_level in ["L0", "L1"]:
                raise PolicyViolationException(f"Action '{action_type}' is prohibited for risk level '{risk_level}'.")
            elif not approved:
                raise PolicyViolationException(f"Action '{action_type}' has risk level '{risk_level}' and requires explicit approval.")

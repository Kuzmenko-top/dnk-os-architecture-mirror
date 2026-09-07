# --- DNK-MRH-HEADER ---
# mrh_id: "model_gateway/budgets.py"
# purpose: "Enforce cost tracking, rate limits, and token budgets per design run."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import logging

logger = logging.getLogger("gateway_budgets")

class BudgetExceededException(Exception):
    pass

class BudgetManager:
    # Strict limits per supervisor run session
    MAX_BUDGET_USD = 0.25

    @classmethod
    def check_and_track_budget(cls, current_spent_usd: float, expected_call_cost_usd: float):
        total = current_spent_usd + expected_call_cost_usd
        logger.info(f"Budget check: spent={current_spent_usd:.5f}$, expected_call={expected_call_cost_usd:.5f}$, total={total:.5f}$")
        if total > cls.MAX_BUDGET_USD:
            raise BudgetExceededException(
                f"Budget exceeded! Allowed: {cls.MAX_BUDGET_USD}$, Total spent + expected: {total:.5f}$"
            )

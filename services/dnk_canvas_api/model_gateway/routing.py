# --- DNK-MRH-HEADER ---
# mrh_id: "model_gateway/routing.py"
# purpose: "Implement provider routing, model allowlist, and fallback configurations."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import os
from typing import Tuple

class ModelRoutingManager:
    @staticmethod
    def resolve_provider_and_model() -> Tuple[str, str]:
        # Respect LLM_PROVIDER_MODE environment feature flag:
        # vertex, claude, shadow, fixture
        mode = os.getenv("LLM_PROVIDER_MODE", "fixture").lower()
        
        if mode == "vertex":
            return "vertex_gemini", "gemini-1.5-pro"
        elif mode == "claude":
            return "anthropic_claude", "claude-3-5-sonnet"
        elif mode == "shadow":
            return "vertex_gemini", "gemini-1.5-pro"
        else:
            return "vertex_gemini", "gemini-1.5-pro"

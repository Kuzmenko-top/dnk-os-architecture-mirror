# --- DNK-MRH-HEADER ---
# mrh_id: "core/model_proxy/tests/test_self_healing_router.py"
# purpose: "Unit tests verifying SelfHealingModelRouter fallback mechanism."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from core.model_proxy.self_healing_router import SelfHealingModelRouter


def test_self_healing_router_ok():
    router = SelfHealingModelRouter()
    gemini_model = os.getenv("GEMINI_MODEL_ID", "gemini-2.5-flash")
    res = router.resolve_model_with_fallback(gemini_model, error_code=0)
    assert res["status"] == "ok"
    assert res["active_model"] == gemini_model


def test_self_healing_router_fallback_404():
    router = SelfHealingModelRouter()
    res = router.resolve_model_with_fallback("invalid-3.5-flash", error_code=404)
    assert res["status"] == "healed"
    assert "codestral" in res["active_model"]
    assert res["active_provider"] == "nvidia_nim"

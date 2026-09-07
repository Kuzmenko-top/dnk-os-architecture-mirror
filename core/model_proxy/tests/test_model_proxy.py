# --- DNK-MRH-HEADER ---
# mrh_id: "core/model_proxy/tests/test_model_proxy.py"
# purpose: "Unit tests for UniversalModelProxy in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import pytest
from core.model_proxy.universal_model_proxy import UniversalModelProxy


def test_universal_model_proxy_payload():
    proxy = UniversalModelProxy()
    payload = proxy.format_prompt_payload("Hello DNK OS", "codestral-22b")
    assert payload["status"] == "ready"
    assert payload["model"] == "mistralai/codestral-22b-instruct-v0.1"
    assert payload["workspace_guard"] == "DNK OS/"


def test_list_available_models():
    proxy = UniversalModelProxy()
    models = proxy.list_available_models()
    assert "gemini-3.5-flash" in models
    assert "nemotron-120b" in models

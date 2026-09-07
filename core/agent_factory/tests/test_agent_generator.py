# --- DNK-MRH-HEADER ---
# mrh_id: "core/agent_factory/tests/test_agent_generator.py"
# purpose: "Unit tests for Agent Factory generator creating valid SOUL.md and MANIFEST.yaml files."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import tempfile
import pytest
from core.agent_factory.agent_generator import create_agent


def test_create_agent_factory():
    agent_dir = create_agent(
        agent_id="test_agent_morgan",
        name="Morgan",
        role="Analytics & Business Engineer",
        specialty="shopify ucp, metrics",
    )

    assert os.path.exists(agent_dir)
    assert os.path.exists(os.path.join(agent_dir, "SOUL.md"))
    assert os.path.exists(os.path.join(agent_dir, "MANIFEST.yaml"))
    assert os.path.exists(os.path.join(agent_dir, "skills"))
    assert os.path.exists(os.path.join(agent_dir, "memory"))

    with open(os.path.join(agent_dir, "SOUL.md"), "r", encoding="utf-8") as f:
        soul = f.read()

    assert "Morgan" in soul
    assert "Analytics & Business Engineer" in soul

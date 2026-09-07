# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_demo_e2e_flow.py"
# purpose: "Verification test suite for scripts/demo_e2e_flow.sh --scenario <name>"
# canonical_source: true
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import subprocess
import pytest

@pytest.mark.parametrize("scenario", ["shopify", "swarm-parallel", "patent-shield", "video-ai"])
def test_demo_e2e_flow_scenarios(scenario):
    cmd = ["bash", "scripts/demo_e2e_flow.sh", "--scenario", scenario]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Scenario {scenario} failed with code {result.returncode}:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    assert f"🎯 Сценарій: {scenario}" in result.stdout
    assert "Canvas DAG" in result.stdout
    assert "Adversarial Gate Passed" in result.stdout

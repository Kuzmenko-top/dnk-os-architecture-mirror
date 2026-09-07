# --- DNK-MRH-HEADER ---
# mrh_id: "tests/deployment/test_docker_configurations.py"
# purpose: "Unit and verification tests for production Dockerfiles (multi-stage, non-root security, healthchecks)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import os
import pytest

DOCKERFILES = ["Dockerfile.api", "Dockerfile.web", "Dockerfile.worker"]

@pytest.mark.parametrize("dockerfile", DOCKERFILES)
def test_dockerfile_exists(dockerfile):
    assert os.path.exists(dockerfile), f"Dockerfile {dockerfile} must exist in project root"

@pytest.mark.parametrize("dockerfile", DOCKERFILES)
def test_dockerfile_has_mrh_header(dockerfile):
    with open(dockerfile, "r", encoding="utf-8") as f:
        content = f.read()
    assert "# --- DNK-MRH-HEADER ---" in content
    assert f'mrh_id: "{dockerfile}"' in content
    assert "# --- END DNK-MRH-HEADER ---" in content

@pytest.mark.parametrize("dockerfile", DOCKERFILES)
def test_dockerfile_is_multistage(dockerfile):
    with open(dockerfile, "r", encoding="utf-8") as f:
        content = f.read()
    from_lines = [line for line in content.splitlines() if line.strip().startswith("FROM ")]
    assert len(from_lines) >= 2, f"{dockerfile} must have at least 2 stages (builder and runner)"

@pytest.mark.parametrize("dockerfile", DOCKERFILES)
def test_dockerfile_non_root_security(dockerfile):
    with open(dockerfile, "r", encoding="utf-8") as f:
        content = f.read()
    assert "USER 10001:10001" in content or "USER nextjs" in content or "USER appuser" in content, (
        f"{dockerfile} must declare non-root user execution"
    )

@pytest.mark.parametrize("dockerfile", DOCKERFILES)
def test_dockerfile_healthcheck_defined(dockerfile):
    with open(dockerfile, "r", encoding="utf-8") as f:
        content = f.read()
    assert "HEALTHCHECK" in content, f"{dockerfile} must define a HEALTHCHECK instruction"

# --- DNK-MRH-HEADER ---
# mrh_id: "tests_conftest"
# purpose: "Root pytest configuration and sys.path initialization for DNK OS MVP test suites"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import sys
import os
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent

for p in [str(ROOT_DIR), str(ROOT_DIR / "services")]:
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(autouse=True)
def clean_test_environment():
    """Autouse fixture ensuring strict state isolation across test suites."""
    # Pre-test cleanup
    yield
    # Post-test teardown
    if "FIXTURE_MODE" in os.environ:
        os.environ.pop("FIXTURE_MODE", None)

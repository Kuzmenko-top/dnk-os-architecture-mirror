# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_license_firewall.py"
# purpose: "Unit and Integration Tests for Two-Track License Firewall and Clean-Room Isolation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import json
import pytest
import tempfile
from pathlib import Path
from scripts.check_license_policy import (
    classify_license,
    normalize_license_key,
    generate_clean_room_spec,
    run_license_firewall,
    PERMISSIVE_LICENSES,
    RESTRICTIVE_LICENSES
)


def test_license_classification():
    """Verify standard licenses are correctly assigned to Track 1 or Track 2."""
    # Track 1 Permissive
    assert "Track 1" in classify_license("MIT")[0]
    assert "Track 1" in classify_license("Apache-2.0")[0]
    assert "Track 1" in classify_license("BSD-3-Clause")[0]
    assert "Track 1" in classify_license("ISC")[0]

    # Track 2 Copyleft / Restrictive
    assert "Track 2" in classify_license("GPL-3.0")[0]
    assert "Track 2" in classify_license("AGPL-3.0")[0]
    assert "Track 2" in classify_license("LGPL-2.1")[0]
    assert "Track 2" in classify_license("MPL-2.0")[0]

    # Unknown
    assert "Unknown" in classify_license("Custom-Proprietary-Unapproved")[0]


def test_clean_room_spec_generation():
    """Verify Clean-Room specification markdown file creation and content."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        spec_file = generate_clean_room_spec("remotion", "GPL-3.0", version="4.0.0", output_dir=tmp_dir)
        assert os.path.exists(spec_file)
        
        with open(spec_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        assert "# --- DNK-MRH-HEADER ---" in content
        assert "DNK-CLEANROOM-REMOTION" in content
        assert "Track 2: Copyleft / Restrictive" in content
        assert "Clean-Room Reverse Engineering" in content


def test_run_license_firewall_permissive_pass():
    """Verify that a manifest with only permissive licenses passes in strict mode."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        data = [
            {"Name": "fastapi", "License": "MIT", "Version": "0.110.0"},
            {"Name": "pydantic", "License": "MIT", "Version": "2.6.0"},
            {"Name": "pytest", "License": "MIT", "Version": "8.0.0"}
        ]
        json.dump(data, f)
        temp_path = f.name

    try:
        res = run_license_firewall(temp_path, strict=True)
        assert res["status"] == "PASSED"
        assert res["total_scanned"] == 3
        assert res["track1_approved_count"] == 3
        assert res["track2_copyleft_count"] == 0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_run_license_firewall_copyleft_blocked_in_strict():
    """Verify that copyleft dependencies trigger BLOCKED status in strict mode and generate specs."""
    with tempfile.TemporaryDirectory() as tmp_cleanroom:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            data = [
                {"Name": "mit-pkg", "License": "MIT", "Version": "1.0"},
                {"Name": "gpl-pkg", "License": "GPL-3.0", "Version": "2.0"},
                {"Name": "agpl-pkg", "License": "AGPL-3.0", "Version": "3.0"}
            ]
            json.dump(data, f)
            temp_path = f.name

        try:
            res = run_license_firewall(temp_path, strict=True, cleanroom_dir=tmp_cleanroom)
            assert res["status"] == "BLOCKED"
            assert res["total_scanned"] == 3
            assert res["track1_approved_count"] == 1
            assert res["track2_copyleft_count"] == 2
            
            # Check specs were generated
            generated_specs = os.listdir(tmp_cleanroom)
            assert len(generated_specs) == 2
            assert any("GPL_PKG" in s for s in generated_specs)
            assert any("AGPL_PKG" in s for s in generated_specs)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

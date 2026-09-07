"""
# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_marketing_assets_hygiene.py"
# purpose: "Verification test suite for Marketing Assets Catalog, Remotion Creative Templates, and Pitch Decks (Step 5)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK Swarm (gerych_auditor & dnk_marketing_cmo)"
# --- END DNK-MRH-HEADER ---
"""

import json
import re
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MARKETING_DIR = REPO_ROOT / "docs" / "notes" / "marketing"
ROOT_NOTES_DIR = REPO_ROOT / "docs" / "notes"


def test_marketing_assets_directory_and_core_files_exist():
    """Verify that docs/notes/marketing directory and all required assets exist."""
    assert MARKETING_DIR.exists() and MARKETING_DIR.is_dir(), f"Missing directory: {MARKETING_DIR}"
    
    expected_files = [
        "000_MARKETING_ASSETS_HUB.md",
        "001_remotion_creative_templates.md",
        "002_commercial_innovation_pitches.md",
    ]
    for filename in expected_files:
        file_path = MARKETING_DIR / filename
        assert file_path.exists(), f"Expected marketing asset missing: {file_path}"
        assert file_path.stat().st_size > 500, f"File too small or stub: {file_path}"

    root_note = ROOT_NOTES_DIR / "086_commercial_marketing_assets_hub.md"
    assert root_note.exists(), f"Expected root gateway note missing: {root_note}"


def test_marketing_notes_headers_and_frontmatter():
    """Verify YAML frontmatter and MRH headers across all marketing notes."""
    files_to_check = list(MARKETING_DIR.glob("*.md")) + [ROOT_NOTES_DIR / "086_commercial_marketing_assets_hub.md"]
    
    for md_file in files_to_check:
        content = md_file.read_text(encoding="utf-8")
        
        # Verify no hardcoded absolute user home paths
        assert "/Users/" not in content, f"Hardcoded absolute user path found in {md_file.name}"
        
        # Check YAML frontmatter
        assert content.startswith("---\n"), f"{md_file.name} must start with YAML frontmatter"
        parts = content.split("---\n", 2)
        assert len(parts) >= 3, f"Improper frontmatter block in {md_file.name}"
        
        frontmatter = yaml.safe_load(parts[1])
        assert isinstance(frontmatter, dict), f"YAML frontmatter invalid in {md_file.name}"
        assert "title" in frontmatter, f"'title' missing in frontmatter of {md_file.name}"
        assert "tags" in frontmatter, f"'tags' missing in frontmatter of {md_file.name}"
        assert "status" in frontmatter, f"'status' missing in frontmatter of {md_file.name}"
        
        # Check MRH header presence
        assert "DNK-MRH-HEADER" in content, f"MRH header missing in {md_file.name}"
        assert "END DNK-MRH-HEADER" in content, f"MRH closing tag missing in {md_file.name}"


def test_remotion_template_json_manifests_are_valid():
    """Extract and validate all Remotion JSON manifests embedded in 001_remotion_creative_templates.md."""
    template_file = MARKETING_DIR / "001_remotion_creative_templates.md"
    content = template_file.read_text(encoding="utf-8")
    
    json_blocks = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    assert len(json_blocks) >= 2, "Expected at least 2 Remotion JSON configuration examples"
    
    for idx, block in enumerate(json_blocks, 1):
        try:
            data = json.loads(block)
        except Exception as e:
            pytest.fail(f"Failed to parse JSON manifest #{idx} in {template_file.name}: {e}")
            continue
            
        assert "title" in data, f"Manifest #{idx} missing 'title'"
        assert "format_type" in data, f"Manifest #{idx} missing 'format_type'"
        assert data["format_type"] in ["story_9_16", "square_1_1", "landscape_16_9"], (
            f"Invalid format_type in manifest #{idx}: {data['format_type']}"
        )
        assert "duration_seconds" in data, f"Manifest #{idx} missing 'duration_seconds'"
        assert "props" in data and isinstance(data["props"], dict), f"Manifest #{idx} missing 'props' dict"


def test_commercial_pitches_coverage_of_core_innovations():
    """Verify that all 4 required innovations are thoroughly pitched in 002_commercial_innovation_pitches.md."""
    pitches_file = MARKETING_DIR / "002_commercial_innovation_pitches.md"
    content = pitches_file.read_text(encoding="utf-8")
    
    required_innovations = [
        "PersonaLive",
        "Diffusion Studio",
        "Lakehouse",
        "SCONES",
        "Swarm Control Plane",
    ]
    for innovation in required_innovations:
        assert innovation.lower() in content.lower(), f"Core innovation '{innovation}' missing from pitch document"

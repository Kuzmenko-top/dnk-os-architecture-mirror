# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_unified_memory_broker.py"
# purpose: "Unit tests for UnifiedMemoryBroker Tier 4 Obsidian Vault recursive rglob search and hygiene filters."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-06"
# author: "DNK Swarm (dnk_dev_fullstack + gerych_builder)"
# --- END DNK-MRH-HEADER ---

import pytest
from pathlib import Path
from core.memory.unified_memory_broker import UnifiedMemoryBroker, MemoryTier


def test_obsidian_vault_recursive_rglob_and_exclusions(tmp_path: Path):
    vault_dir = tmp_path / "notes"
    vault_dir.mkdir()

    # 1. Root level note
    root_note = vault_dir / "001_intro.md"
    root_note.write_text(
        "---\ntitle: \"Introduction Note\"\ntags: [core, dnk]\n---\n# Introduction\nThis is core architecture.",
        encoding="utf-8"
    )

    # 2. Subdirectory note (should be discovered by rglob)
    sub_dir = vault_dir / "subfolder"
    sub_dir.mkdir()
    sub_note = sub_dir / "002_sub_architecture.md"
    sub_note.write_text(
        "---\ntitle: \"Submodule Note\"\ntags: [deep, system]\n---\n# Submodule\nDeep architectural details.",
        encoding="utf-8"
    )

    # 3. Excluded .obsidian folder
    obsidian_dir = vault_dir / ".obsidian"
    obsidian_dir.mkdir()
    (obsidian_dir / "app.json").write_text("{}", encoding="utf-8")
    (obsidian_dir / "hidden.md").write_text("Should not appear", encoding="utf-8")

    # 4. Excluded archive folder
    archive_dir = vault_dir / "archive"
    archive_dir.mkdir()
    (archive_dir / "legacy_note.md").write_text("Old architecture notes", encoding="utf-8")

    # 5. Excluded temporary test file
    (vault_dir / "test-temp-fixture.md").write_text("Temporary test data architecture", encoding="utf-8")

    broker = UnifiedMemoryBroker(vault_path=vault_dir)
    recs, latency = broker._query_obsidian_vault("architecture", limit=10)

    # Must find root_note and sub_note, but NOT archive, .obsidian, or test-temp-fixture
    found_filenames = {r.metadata["filename"] for r in recs}
    assert "001_intro.md" in found_filenames
    assert "002_sub_architecture.md" in found_filenames
    assert "hidden.md" not in found_filenames
    assert "legacy_note.md" not in found_filenames
    assert "test-temp-fixture.md" not in found_filenames

    # Check relative_path format
    sub_rec = next(r for r in recs if r.metadata["filename"] == "002_sub_architecture.md")
    assert sub_rec.metadata["relative_path"] == "./docs/notes/subfolder/002_sub_architecture.md"
    assert sub_rec.tier == MemoryTier.OBSIDIAN_VAULT

    # Check tier stats vault_count accounts for recursive discovery excluding ignored paths
    stats = broker.get_tier_stats()
    assert stats["tier_4_obsidian_notes"] == 2

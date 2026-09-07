# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_obsidian_vault_sync.py"
# purpose: "Unit tests for ObsidianVaultSync engine verifying bidirectional sync, dry run, and isolation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import importlib.util
import sys
import tempfile
from pathlib import Path
import pytest

# Load obsidian_vault_sync module dynamically from scripts/system
script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "system" / "obsidian_vault_sync.py"
spec = importlib.util.spec_from_file_location("obsidian_vault_sync", script_path)
assert spec is not None and spec.loader is not None
obsidian_vault_sync = importlib.util.module_from_spec(spec)
sys.modules["obsidian_vault_sync"] = obsidian_vault_sync
spec.loader.exec_module(obsidian_vault_sync)
ObsidianVaultSync = obsidian_vault_sync.ObsidianVaultSync


@pytest.fixture
def sync_env():
    with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as vault_dir:
        repo_notes = Path(repo_dir) / "docs" / "notes"
        vault = Path(vault_dir) / "vault"
        repo_notes.mkdir(parents=True)
        vault.mkdir(parents=True)
        yield repo_notes, vault


def test_obsidian_vault_sync_copy_to_vault(sync_env):
    repo_notes, vault = sync_env
    test_note = repo_notes / "036 OCC Structural Graph Mutation Resolver.md"
    test_note.write_text("# ADR 036\nContent in repo.", encoding="utf-8")

    syncer = ObsidianVaultSync(repo_notes_dir=repo_notes, vault_dir=vault)
    stats = syncer.sync(direction="bidirectional")

    assert stats["copied_to_vault"] == 1
    assert stats["copied_to_repo"] == 0
    assert (vault / "036 OCC Structural Graph Mutation Resolver.md").exists()
    assert (vault / "036 OCC Structural Graph Mutation Resolver.md").read_text() == test_note.read_text()


def test_obsidian_vault_sync_copy_to_repo(sync_env):
    repo_notes, vault = sync_env
    test_note = vault / "037 New Feature Note.md"
    test_note.write_text("# Note 037\nCreated inside Obsidian.", encoding="utf-8")

    syncer = ObsidianVaultSync(repo_notes_dir=repo_notes, vault_dir=vault)
    stats = syncer.sync(direction="bidirectional")

    assert stats["copied_to_repo"] == 1
    assert stats["copied_to_vault"] == 0
    assert (repo_notes / "037 New Feature Note.md").exists()
    assert (repo_notes / "037 New Feature Note.md").read_text() == test_note.read_text()


def test_obsidian_vault_sync_dry_run(sync_env):
    repo_notes, vault = sync_env
    test_note = repo_notes / "draft.md"
    test_note.write_text("# Draft\nOnly in repo.", encoding="utf-8")

    syncer = ObsidianVaultSync(repo_notes_dir=repo_notes, vault_dir=vault, dry_run=True)
    stats = syncer.sync(direction="to-vault")

    assert stats["copied_to_vault"] == 1
    assert not (vault / "draft.md").exists()


def test_obsidian_vault_sync_skips_ignored(sync_env):
    repo_notes, vault = sync_env
    obsidian_internal = vault / ".obsidian"
    obsidian_internal.mkdir()
    (obsidian_internal / "app.json").write_text("{}", encoding="utf-8")

    ds_store = vault / ".DS_Store"
    ds_store.write_text("binary", encoding="utf-8")

    syncer = ObsidianVaultSync(repo_notes_dir=repo_notes, vault_dir=vault)
    stats = syncer.sync(direction="to-repo")

    assert stats["copied_to_repo"] == 0
    assert not (repo_notes / ".obsidian").exists()
    assert not (repo_notes / ".DS_Store").exists()

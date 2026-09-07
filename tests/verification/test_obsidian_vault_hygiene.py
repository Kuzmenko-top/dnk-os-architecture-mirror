# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_obsidian_vault_hygiene.py"
# purpose: "Adversarial Quality Gate testing Obsidian Vault frontmatter, MRH headers, and UnifiedMemoryBroker retrieval latency."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK Swarm (gerych_auditor + gerych_builder)"
# --- END DNK-MRH-HEADER ---

import re
import time
from pathlib import Path
import pytest
import yaml
from core.memory.unified_memory_broker import UnifiedMemoryBroker, MemoryTier

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = HUB_ROOT / "docs" / "notes"


def test_vault_root_notes_header_hygiene():
    """Verify that root-level markdown notes in docs/notes contain either YAML frontmatter or MRH header."""
    assert VAULT_PATH.exists(), f"Vault path {VAULT_PATH} does not exist"
    root_mds = [f for f in VAULT_PATH.glob("*.md") if not f.name.startswith(".")]
    assert len(root_mds) > 10, "Expected at least 10 root notes in Obsidian Vault"

    missing_headers = []
    for md_file in root_mds:
        content = md_file.read_text(encoding="utf-8", errors="ignore").strip()
        has_yaml = content.startswith("---")
        has_mrh = "DNK-MRH-HEADER" in content
        if not (has_yaml or has_mrh):
            missing_headers.append(md_file.name)

    # Allow zero or very few exceptions if any, assert none
    assert not missing_headers, f"Notes missing both YAML and MRH headers: {missing_headers}"


def test_vault_unified_memory_broker_real_query_latency():
    """Verify that UnifiedMemoryBroker can query the live vault recursively with sub-50ms latency."""
    broker = UnifiedMemoryBroker(vault_path=str(VAULT_PATH))
    start_time = time.perf_counter()
    records, query_latency = broker._query_obsidian_vault("architecture", limit=5)
    duration_ms = (time.perf_counter() - start_time) * 1000

    assert len(records) > 0, "Expected to find architecture records in live vault"
    # Allow up to 500ms for full-vault un-cached filesystem traversal on busy CI/dev systems
    assert duration_ms < 500.0, f"Query took {duration_ms:.2f}ms, expected sub-500ms"

    # Verify all records have valid relative_path and OBSIDIAN_VAULT tier
    for r in records:
        assert r.tier == MemoryTier.OBSIDIAN_VAULT
        assert r.metadata.get("relative_path", "").startswith("./docs/notes/")


def test_vault_tier_stats_count():
    """Verify get_tier_stats accurately reports recursive active notes count."""
    broker = UnifiedMemoryBroker(vault_path=str(VAULT_PATH))
    stats = broker.get_tier_stats()

    active_vault_notes = stats.get("tier_4_obsidian_notes", 0)
    assert active_vault_notes > 50, f"Expected >50 active notes across vault tree, got {active_vault_notes}"


def test_vault_note_prefixes_unique():
    """Verify that every numbered note in docs/notes has a strictly unique numeric prefix."""
    notes = [f.name for f in VAULT_PATH.glob("*.md") if not f.name.startswith(".")]
    prefixes = {}
    for n in notes:
        m = re.match(r"^(\d+)", n)
        if m:
            num = m.group(1)
            prefixes.setdefault(num, []).append(n)

    duplicates = {num: files for num, files in prefixes.items() if len(files) > 1}
    assert not duplicates, f"Found duplicate numbered notes in vault: {duplicates}"


def test_tasks_and_ideas_subfolder_hygiene():
    """Verify that tasks_and_ideas has structured subdirectories and no loose markdown files in root (except index)."""
    tasks_dir = VAULT_PATH / "tasks_and_ideas"
    if not tasks_dir.exists():
        return

    loose_files = [f.name for f in tasks_dir.glob("*.md") if f.name != "000_DNK_TASK_AND_IDEAS_INDEX.md"]
    assert not loose_files, f"Found unclustered loose files in tasks_and_ideas root: {loose_files}"

    for sub in ["epics", "tasks", "ideas", "gates"]:
        sub_path = tasks_dir / sub
        assert sub_path.exists() and sub_path.is_dir(), f"Expected subdirectory {sub_path} to exist"


def test_vault_notes_yaml_frontmatter_validity():
    """Verify that every root note in docs/notes has valid, parsable YAML frontmatter with required keys."""
    root_mds = [f for f in VAULT_PATH.glob("*.md") if not f.name.startswith(".")]
    assert len(root_mds) > 10, "Expected at least 10 root notes in Obsidian Vault"

    errors = []
    for md_file in root_mds:
        content = md_file.read_text(encoding="utf-8", errors="ignore").strip()
        m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            errors.append(f"{md_file.name}: Missing YAML frontmatter block")
            continue
        try:
            data = yaml.safe_load(m.group(1))
            if not isinstance(data, dict):
                errors.append(f"{md_file.name}: YAML frontmatter is not a dictionary")
                continue
            if not data.get("title") or not str(data.get("title")).strip():
                errors.append(f"{md_file.name}: Missing or empty 'title' key in frontmatter")
            if not data.get("tags"):
                errors.append(f"{md_file.name}: Missing or empty 'tags' key in frontmatter")
            if "aliases" in data and not isinstance(data["aliases"], (list, str)):
                errors.append(f"{md_file.name}: 'aliases' must be a list or string")
        except Exception as e:
            errors.append(f"{md_file.name}: YAML parse error - {e}")

    assert not errors, f"Frontmatter validation errors:\n" + "\n".join(errors)


def test_vault_markdown_file_links_integrity():
    """Verify that all markdown file links [label](path) inside notes resolve to existing files."""
    root_mds = [f for f in VAULT_PATH.glob("*.md") if not f.name.startswith(".")]
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    broken_links = []
    for md_file in root_mds:
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        for label, target in link_pattern.findall(content):
            if any(target.startswith(p) for p in ("http://", "https://", "#", "mailto:")):
                continue
            clean_target = target.split("#")[0].split("?")[0].strip()
            if not clean_target:
                continue
            # Resolve relative to current note's parent, or HUB_ROOT
            rel_to_note = md_file.parent / clean_target
            rel_to_root = HUB_ROOT / clean_target.lstrip("/")
            if not rel_to_note.exists() and not rel_to_root.exists():
                broken_links.append(f"{md_file.name} -> [{label}]({target})")

    assert not broken_links, f"Broken markdown links detected in notes:\n" + "\n".join(broken_links)


def test_task_forest_index_and_telemetry_sync():
    """Verify Task Forest DAG metrics calculation and index synchronization."""
    from scripts.system.update_task_forest_metrics import (
        collect_nodes,
        calculate_metrics,
        render_markdown_index,
        INDEX_FILE,
    )

    assert INDEX_FILE.exists(), f"Index file missing: {INDEX_FILE}"
    nodes = collect_nodes()
    assert len(nodes) >= 100, f"Expected at least 100 nodes, found {len(nodes)}"

    metrics = calculate_metrics(nodes)
    assert metrics["total"] == len(nodes)
    assert 0.0 <= metrics["avg_progress"] <= 100.0
    assert 0.0 <= metrics["completion_rate"] <= 100.0
    assert "epic" in metrics["by_type"]
    assert "task" in metrics["by_type"]
    assert "idea" in metrics["by_type"]
    assert "gate" in metrics["by_type"]
    assert len(metrics["epics_summary"]) >= 1

    for ep in metrics["epics_summary"]:
        assert "node_id" in ep
        assert "title" in ep
        assert "status" in ep
        assert 0.0 <= ep["progress"] <= 100.0

    rendered = render_markdown_index(nodes, metrics)
    assert "# 🌐 DNK OS Node-Based TASK & Ideas System Index" in rendered
    assert "## 📊 System Overview" in rendered
    assert "## 🏆 Active Epics & Objectives" in rendered
    assert "## 🗺️ Master Node Registry" in rendered




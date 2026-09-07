# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_swarm_ledger_and_mailbox.py"
# purpose: "Verify Swarm Shared Memory Ledger & Artifact Mailbox (ruflo meta-harness pattern)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

import os
import shutil
import tempfile
import time
from pathlib import Path
import pytest

from core.orchestrator.swarm_ledger import (
    ArtifactCategory,
    SwarmArtifact,
    SwarmLedger,
)
from core.orchestrator.swarm_coordinator import GerychSwarmCoordinator


@pytest.fixture
def temp_ledger_env():
    temp_dir = tempfile.mkdtemp(prefix="test_swarm_ledger_")
    hub_path = Path(temp_dir)
    storage_path = hub_path / "data" / "swarm_artifacts" / "swarm_ledger.json"
    yield hub_path, storage_path
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_swarm_artifact_hashing_and_ttl():
    content = {"user_id": 123, "endpoint": "/api/v1/checkout"}
    art = SwarmArtifact(
        artifact_id="art_test1",
        category=ArtifactCategory.API_CONTRACT,
        key="api:checkout",
        producer_agent="dnk_dev_fullstack",
        content=content,
        ttl_seconds=1,
    )
    assert art.content_hash != ""
    assert not art.is_expired()
    
    # Check deterministic hashing
    hash2 = SwarmArtifact.compute_hash(content)
    assert art.content_hash == hash2

    time.sleep(1.1)
    assert art.is_expired()


def test_swarm_ledger_crud_and_persistence(temp_ledger_env):
    hub_path, storage_path = temp_ledger_env
    ledger = SwarmLedger(hub_root=hub_path, storage_path=storage_path)

    # 1. Register artifact
    ts_interface = "export interface ShopifyTheme { id: string; name: string; }"
    art = ledger.register_artifact(
        key="types:shopify_theme",
        category=ArtifactCategory.TYPE_DEF,
        producer_agent="dnk_shopify",
        content=ts_interface,
        task_id="task_ecom_01",
        metadata={"compiler": "tsc", "strict": True},
    )
    assert art.artifact_id.startswith("art_")
    assert art.key == "types:shopify_theme"

    # 2. Get artifact by key and by id
    fetched_by_key = ledger.get_artifact("types:shopify_theme")
    assert fetched_by_key is not None
    assert fetched_by_key.content == ts_interface

    fetched_by_id = ledger.get_artifact(art.artifact_id)
    assert fetched_by_id is not None
    assert fetched_by_id.artifact_id == art.artifact_id

    # 3. Verify file persistence on disk
    assert storage_path.exists()
    
    # 4. Verify cold start recovery
    new_ledger = SwarmLedger(hub_root=hub_path, storage_path=storage_path)
    recovered = new_ledger.get_artifact("types:shopify_theme")
    assert recovered is not None
    assert recovered.producer_agent == "dnk_shopify"

    # 5. Query filtering
    results = new_ledger.find_artifacts(
        category=ArtifactCategory.TYPE_DEF,
        producer_agent="dnk_shopify",
    )
    assert len(results) == 1
    assert results[0].key == "types:shopify_theme"

    # 6. Deletion
    deleted = new_ledger.delete_artifact("types:shopify_theme")
    assert deleted is True
    assert new_ledger.get_artifact("types:shopify_theme") is None


def test_swarm_mailbox_dispatch_and_fetch(temp_ledger_env):
    hub_path, storage_path = temp_ledger_env
    ledger = SwarmLedger(hub_root=hub_path, storage_path=storage_path)

    # Dispatch artifact to gerych_builder mailbox
    pydantic_schema = {
        "title": "CheckoutPayload",
        "type": "object",
        "properties": {"amount": {"type": "number"}, "currency": {"type": "string"}},
    }
    art = ledger.register_artifact(
        key="schema:checkout",
        category=ArtifactCategory.SCHEMA,
        producer_agent="dnk_dev_fullstack",
        recipient_agent="gerych_builder",
        content=pydantic_schema,
        task_id="task_checkout_integration",
    )
    assert art.recipient_agent == "gerych_builder"

    # Fetch mailbox for gerych_builder (unread only)
    mailbox_messages = ledger.fetch_mailbox(
        recipient_agent="gerych_builder",
        unread_only=True,
        mark_read=True,
    )
    assert len(mailbox_messages) == 1
    assert mailbox_messages[0]["key"] == "schema:checkout"
    assert mailbox_messages[0]["producer_agent"] == "dnk_dev_fullstack"

    # Second fetch should return 0 unread messages
    mailbox_second = ledger.fetch_mailbox(
        recipient_agent="gerych_builder",
        unread_only=True,
    )
    assert len(mailbox_second) == 0

    # Fetch all (including read)
    mailbox_all = ledger.fetch_mailbox(
        recipient_agent="gerych_builder",
        unread_only=False,
    )
    assert len(mailbox_all) == 1
    assert mailbox_all[0]["is_read"] is True


def test_coordinator_ledger_helpers():
    coordinator = GerychSwarmCoordinator()
    
    # Test publishing through coordinator
    test_key = "test:api_contract:fastapi"
    art = coordinator.publish_artifact(
        key=test_key,
        category="api_contract",
        producer_agent="dnk_dev_fullstack",
        content={"endpoints": ["/api/v1/health", "/api/v1/canvas"]},
        recipient_agent="gerych_auditor",
    )
    assert art.key == test_key

    # Retrieve through coordinator
    retrieved = coordinator.get_artifact(test_key)
    assert retrieved is not None
    assert "/api/v1/health" in retrieved.content["endpoints"]

    # Check recipient mailbox
    msgs = coordinator.fetch_agent_mailbox("gerych_auditor", unread_only=False)
    assert any(m["key"] == test_key for m in msgs)

# --- DNK-MRH-HEADER ---
# mrh_id: "tests/stream/test_stream_router.py"
# purpose: "Integration tests for Stream Router: REST API, SSE streaming, Consumer Groups & DLQ replay (DNK-STREAM-001 Phase 4)"
# canonical_source: true
# alters_files: ["tests/stream/test_stream_router.py"]
# triggers_tasks: ["DNK-STREAM-001-PHASE4"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_topics_and_schemas_crud():
    # 1. Create Topic
    topic_resp = client.post(
        "/api/v1/stream/topics",
        json={
            "name": "orders.checkout.events",
            "workspace_id": "ws-alpha-001",
            "partitions_count": 4,
            "retention_ms": 86400000,
            "max_message_size_bytes": 1048576,
            "is_compacted": False,
        },
    )
    assert topic_resp.status_code == 201
    topic_data = topic_resp.json()
    assert topic_data["status"] == "success"
    assert topic_data["topic"]["name"] == "orders.checkout.events"
    assert topic_data["topic"]["partitions_count"] == 4

    # 2. List Topics
    list_resp = client.get("/api/v1/stream/topics", params={"workspace_id": "ws-alpha-001"})
    assert list_resp.status_code == 200
    topics = list_resp.json()["topics"]
    assert any(t["name"] == "orders.checkout.events" for t in topics)

    # 3. Register Schema
    schema_def = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
        },
        "required": ["order_id", "amount"],
    }
    schema_resp = client.post(
        "/api/v1/stream/schemas",
        json={
            "subject": "orders.checkout.events-value",
            "schema_type": "JSONSCHEMA",
            "definition": schema_def,
            "compatibility_mode": "BACKWARD",
            "workspace_id": "ws-alpha-001",
        },
    )
    assert schema_resp.status_code == 201
    schema_data = schema_resp.json()
    assert schema_data["status"] == "success"
    schema_id = schema_data["schema"]["id"]
    assert schema_id.startswith("sch_")

    # 4. Get Latest Schema
    get_schema_resp = client.get("/api/v1/stream/schemas/orders.checkout.events-value/latest")
    assert get_schema_resp.status_code == 200
    assert get_schema_resp.json()["schema"]["id"] == schema_id

    # 5. Get Non-Existent Schema -> 404
    missing_resp = client.get("/api/v1/stream/schemas/non_existent_subject/latest")
    assert missing_resp.status_code == 404


def test_publish_with_schema_validation_and_dlq_auto_routing():
    # 1. Register strict schema
    strict_schema = {
        "type": "object",
        "properties": {
            "transaction_id": {"type": "string"},
            "amount": {"type": "number"},
        },
        "required": ["transaction_id", "amount"],
    }
    schema_resp = client.post(
        "/api/v1/stream/schemas",
        json={
            "subject": "finance.transactions-value",
            "schema_type": "JSONSCHEMA",
            "definition": strict_schema,
            "compatibility_mode": "BACKWARD",
            "workspace_id": "ws-alpha-001",
        },
    )
    schema_id = schema_resp.json()["schema"]["id"]

    # 2. Publish Valid Event
    valid_pub = client.post(
        "/api/v1/stream/publish",
        json={
            "topic_name": "finance.transactions",
            "payload": {"transaction_id": "tx_999", "amount": 149.50},
            "key": "user_tx_999",
            "schema_id": schema_id,
            "workspace_id": "ws-alpha-001",
        },
    )
    assert valid_pub.status_code == 200
    valid_data = valid_pub.json()
    assert valid_data["status"] == "success"
    assert valid_data["is_duplicate"] is False
    assert valid_data["message"]["key"] == "user_tx_999"

    # 3. Publish Duplicate Event
    dup_pub = client.post(
        "/api/v1/stream/publish",
        json={
            "topic_name": "finance.transactions",
            "payload": {"transaction_id": "tx_999", "amount": 149.50},
            "key": "user_tx_999",
            "schema_id": schema_id,
            "workspace_id": "ws-alpha-001",
        },
    )
    assert dup_pub.status_code == 200
    assert dup_pub.json()["is_duplicate"] is True

    # 4. Publish Invalid Event (Missing required field) -> 422 & Auto-routed to DLQ
    invalid_pub = client.post(
        "/api/v1/stream/publish",
        json={
            "topic_name": "finance.transactions",
            "payload": {"transaction_id": "tx_broken"},  # Missing amount
            "key": "user_broken",
            "schema_id": schema_id,
            "workspace_id": "ws-alpha-001",
        },
    )
    assert invalid_pub.status_code == 422
    err_detail = invalid_pub.json()["detail"]
    assert err_detail["error"] == "SchemaValidationFailed"
    assert "dlq_event_id" in err_detail
    dlq_event_id = err_detail["dlq_event_id"]

    # Verify event landed in DLQ
    dlq_list = client.get("/api/v1/stream/dlq", params={"topic_name": "finance.transactions"})
    assert dlq_list.status_code == 200
    dlq_data = dlq_list.json()
    assert dlq_data["stats"]["total_dlq_events"] >= 1
    assert any(e["id"] == dlq_event_id for e in dlq_data["events"])


def test_consumer_groups_lifecycle_poll_and_commit():
    # 1. Create topic
    client.post(
        "/api/v1/stream/topics",
        json={"name": "notifications.email", "partitions_count": 2, "workspace_id": "ws-alpha-001"},
    )

    # 2. Join Consumer Group - Worker 1
    join_resp1 = client.post(
        "/api/v1/stream/consumer-groups/join",
        json={
            "group_id": "email-workers",
            "member_id": "worker_mailer_1",
            "topic_name": "notifications.email",
            "workspace_id": "ws-alpha-001",
        },
    )
    assert join_resp1.status_code == 200
    join_data1 = join_resp1.json()
    assert join_data1["group_id"] == "email-workers"
    assert set(join_data1["assigned_partitions"]) == {0, 1}

    # 3. Publish messages to topic
    client.post(
        "/api/v1/stream/publish",
        json={
            "topic_name": "notifications.email",
            "payload": {"to": "user1@example.com", "template": "welcome"},
            "key": "k1",
        },
    )
    client.post(
        "/api/v1/stream/publish",
        json={
            "topic_name": "notifications.email",
            "payload": {"to": "user2@example.com", "template": "receipt"},
            "key": "k2",
        },
    )

    # 4. Poll messages as worker_mailer_1
    poll_resp = client.post(
        "/api/v1/stream/consumer-groups/poll",
        json={
            "group_id": "email-workers",
            "member_id": "worker_mailer_1",
            "max_records": 10,
        },
    )
    assert poll_resp.status_code == 200
    polled = poll_resp.json()
    assert polled["count"] >= 1

    # 5. Check Lag before commit
    lag_resp = client.get("/api/v1/stream/consumer-groups/email-workers/lag")
    assert lag_resp.status_code == 200
    assert lag_resp.json()["total_lag"] >= 1

    # 6. Commit Offset
    for msg in polled["messages"]:
        commit_resp = client.post(
            "/api/v1/stream/consumer-groups/commit",
            json={
                "group_id": "email-workers",
                "partition": msg["partition"],
                "offset": msg["offset"],
            },
        )
        assert commit_resp.status_code == 200
        assert commit_resp.json()["committed_offset"] == msg["offset"]

    # 7. Check Lag after commit -> should be 0
    lag_resp_after = client.get("/api/v1/stream/consumer-groups/email-workers/lag")
    assert lag_resp_after.status_code == 200
    assert lag_resp_after.json()["total_lag"] == 0


def test_dlq_replay_endpoint():
    # 1. Directly trigger a poison event to DLQ via schema validation failure
    schema_def = {
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"],
    }
    s_resp = client.post(
        "/api/v1/stream/schemas",
        json={
            "subject": "dlq.test.subject-value",
            "schema_type": "JSONSCHEMA",
            "definition": schema_def,
        },
    )
    s_id = s_resp.json()["schema"]["id"]

    inv_resp = client.post(
        "/api/v1/stream/publish",
        json={
            "topic_name": "dlq.source.topic",
            "payload": {"wrong_field": 123},
            "schema_id": s_id,
        },
    )
    assert inv_resp.status_code == 422
    dlq_id = inv_resp.json()["detail"]["dlq_event_id"]

    # 2. Replay the DLQ event to another topic
    replay_resp = client.post(
        f"/api/v1/stream/dlq/{dlq_id}/replay",
        json={"target_topic": "dlq.replayed.destination"},
    )
    assert replay_resp.status_code == 200
    replay_data = replay_resp.json()
    assert replay_data["status"] == "success"
    assert replay_data["replayed_message"]["topic_name"] == "dlq.replayed.destination"

    # 3. Replay non-existent event -> 400
    bad_replay = client.post("/api/v1/stream/dlq/non_existent_dlq_id/replay", json={})
    assert bad_replay.status_code == 400


def test_health_probe_and_sse_stream():
    # 1. Run E2E Health Probe
    probe_resp = client.post("/api/v1/stream/probes/e2e", params={"topic_name": "health.synthetic.probe"})
    assert probe_resp.status_code == 200
    probe_data = probe_resp.json()
    assert probe_data["status"] == "HEALTHY"
    assert probe_data["success"] is True

    # 2. Cluster Health Check
    cluster_resp = client.get("/api/v1/stream/health")
    assert cluster_resp.status_code == 200
    assert cluster_resp.json()["status"] == "HEALTHY"

    # 3. SSE Real-Time Stream
    client.post(
        "/api/v1/stream/topics",
        json={"name": "sse.test.topic", "partitions_count": 1, "workspace_id": "ws-alpha-001"},
    )
    client.post(
        "/api/v1/stream/publish",
        json={
            "topic_name": "sse.test.topic",
            "payload": {"sse_event_key": "live_data_123"},
            "key": "k0",
        },
    )

    # Test SSE Stream output
    sse_resp = client.get("/api/v1/stream/events/sse?topic_name=sse.test.topic&partition=0&from_offset=0&max_events=1")
    assert sse_resp.status_code == 200
    assert "text/event-stream" in sse_resp.headers["content-type"]
    lines = [line.strip() for line in sse_resp.text.strip().split("\n") if line.strip()]
    assert len(lines) >= 1
    assert lines[0].startswith("data: ")
    event_payload = json.loads(lines[0][6:])
    assert event_payload["topic_name"] == "sse.test.topic"
    assert event_payload["payload"]["sse_event_key"] == "live_data_123"

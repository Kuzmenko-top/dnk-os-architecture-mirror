# --- DNK-MRH-HEADER ---
# mrh_id: "tests/stream/test_stream_models.py"
# purpose: "Unit tests for Stream ORM Models (DNK-STREAM-001 Phase 1)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.db.models.stream_topic import StreamTopic
from apps.api.db.models.stream_event_schema import StreamEventSchema
from apps.api.db.models.stream_message import StreamMessage
from apps.api.db.models.stream_consumer_group import StreamConsumerGroup
from apps.api.db.models.stream_dead_letter_event import StreamDeadLetterEvent
from apps.api.db.models.stream_ingestion_sink import StreamIngestionSink


def test_stream_topic_model():
    topic = StreamTopic(
        name="telemetry.events",
        partitions_count=6,
        retention_hours=72,
        cleanup_policy="DELETE",
        metadata_info={"owner": "sre-team"},
    )
    assert topic.id.startswith("top_")
    assert topic.name == "telemetry.events"
    assert topic.partitions_count == 6
    assert topic.retention_hours == 72
    assert topic.is_active is True
    d = topic.to_dict()
    assert d["name"] == "telemetry.events"
    assert d["partitions_count"] == 6


def test_stream_event_schema_model():
    schema = StreamEventSchema(
        subject="orders.created-value",
        version=1,
        schema_format="JSON_SCHEMA",
        schema_definition={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["order_id", "amount"],
        },
        compatibility_mode="BACKWARD",
    )
    assert schema.id.startswith("sch_")
    assert schema.subject == "orders.created-value"
    assert schema.version == 1
    assert "required" in schema.schema_definition
    d = schema.to_dict()
    assert d["subject"] == "orders.created-value"


def test_stream_message_model():
    msg = StreamMessage(
        topic_name="orders.created",
        partition=2,
        offset=1042,
        key="ord_99812",
        payload={"order_id": "ord_99812", "amount": 199.99},
        headers={"x-trace-id": "trc_123"},
        dedup_hash="hash_abc123",
    )
    assert msg.id.startswith("msg_")
    assert msg.topic_name == "orders.created"
    assert msg.partition == 2
    assert msg.offset == 1042
    assert msg.payload["amount"] == 199.99
    d = msg.to_dict()
    assert d["key"] == "ord_99812"
    assert d["offset"] == 1042


def test_stream_consumer_group_model():
    grp = StreamConsumerGroup(
        group_name="order-fulfillment-workers",
        topic_name="orders.created",
        state="STABLE",
        generation_id=2,
        members=[{"member_id": "c1", "client_id": "pod-1", "partitions": [0, 1]}],
        committed_offsets={"0": 100, "1": 150},
    )
    assert grp.id.startswith("grp_")
    assert grp.group_name == "order-fulfillment-workers"
    assert grp.generation_id == 2
    assert grp.committed_offsets["0"] == 100
    d = grp.to_dict()
    assert d["group_name"] == "order-fulfillment-workers"
    assert len(d["members"]) == 1


def test_stream_dead_letter_event_model():
    dlq = StreamDeadLetterEvent(
        original_topic="orders.created",
        consumer_group="order-fulfillment-workers",
        partition=1,
        offset=151,
        payload={"bad_key": 123},
        error_reason="JSONSchemaValidationError: missing required property 'amount'",
        error_stack="Traceback ...",
        status="QUARANTINED",
    )
    assert dlq.id.startswith("dlq_")
    assert dlq.original_topic == "orders.created"
    assert dlq.retry_count == 0
    assert dlq.status == "QUARANTINED"
    d = dlq.to_dict()
    assert "missing required property" in d["error_reason"]


def test_stream_ingestion_sink_model():
    sink = StreamIngestionSink(
        name="orders-clickhouse-sink",
        sink_type="CLICKHOUSE",
        source_topic="orders.created",
        target_table="analytics.orders_raw",
        batch_size=5000,
        flush_interval_ms=2000,
        sink_config={"cluster": "ch-prod-01", "format": "JSONEachRow"},
    )
    assert sink.id.startswith("snk_")
    assert sink.sink_type == "CLICKHOUSE"
    assert sink.batch_size == 5000
    d = sink.to_dict()
    assert d["target_table"] == "analytics.orders_raw"

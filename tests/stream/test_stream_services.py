# --- DNK-MRH-HEADER ---
# mrh_id: "tests/stream/test_stream_services.py"
# purpose: "Unit tests for Stream Bus, Schema Registry, and ClickHouse Buffer Services (DNK-STREAM-001 Phase 2)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.event_schema_registry import (
    EventSchemaRegistryService,
    SchemaCompatibilityError,
)
from apps.api.services.event_stream_bus import EventStreamBusService
from apps.api.services.clickhouse_ingestion_buffer import ClickHouseIngestionBufferService


def test_schema_registry_lifecycle_and_validation():
    registry = EventSchemaRegistryService()

    schema_def_v1 = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
            "amount": {"type": "number"},
        },
        "required": ["order_id", "amount"],
    }

    v1 = registry.register_schema(
        subject="orders.created-value",
        schema_definition=schema_def_v1,
        compatibility_mode="BACKWARD",
    )
    assert v1.version == 1
    latest = registry.get_latest_schema("orders.created-value")
    assert latest is not None
    assert latest.id == v1.id

    # Valid payload
    valid, err = registry.validate_payload(v1, {"order_id": "ord_101", "amount": 49.99})
    assert valid is True
    assert err is None

    # Invalid payload (missing required field)
    valid, err = registry.validate_payload(v1, {"order_id": "ord_101"})
    assert valid is False
    assert err is not None
    assert "Missing required field" in err

    # Invalid payload (wrong type)
    valid, err = registry.validate_payload(v1, {"order_id": "ord_101", "amount": "invalid_number"})
    assert valid is False
    assert err is not None
    assert "expected number" in err


def test_schema_compatibility_checks():
    registry = EventSchemaRegistryService()

    schema_def_v1 = {
        "type": "object",
        "properties": {"user_id": {"type": "string"}},
        "required": ["user_id"],
    }
    registry.register_schema(subject="user.events-value", schema_definition=schema_def_v1)

    # In BACKWARD mode, adding a new required field is illegal
    schema_def_v2_invalid = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "email": {"type": "string"},
        },
        "required": ["user_id", "email"],
    }
    with pytest.raises(SchemaCompatibilityError):
        registry.register_schema(subject="user.events-value", schema_definition=schema_def_v2_invalid)

    # Adding optional field is compatible
    schema_def_v2_valid = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string"},
            "email": {"type": "string"},
        },
        "required": ["user_id"],
    }
    v2 = registry.register_schema(subject="user.events-value", schema_definition=schema_def_v2_valid)
    assert v2.version == 2


def test_event_stream_bus_partitioning_and_dedup():
    bus = EventStreamBusService()
    topic = bus.create_topic(name="orders.stream", partitions_count=4)
    assert topic.partitions_count == 4

    # Publish messages with keys
    msg1, is_dup1 = bus.publish(
        topic_name="orders.stream",
        payload={"order_id": "ord_1", "total": 100},
        key="user_alpha",
    )
    assert is_dup1 is False
    assert msg1.partition in range(4)
    assert msg1.offset == 0

    # Publish duplicate message
    msg1_dup, is_dup2 = bus.publish(
        topic_name="orders.stream",
        payload={"order_id": "ord_1", "total": 100},
        key="user_alpha",
    )
    assert is_dup2 is True
    assert msg1_dup.id == msg1.id

    # Publish message with different key -> deterministic partitioning
    msg2, _ = bus.publish(
        topic_name="orders.stream",
        payload={"order_id": "ord_2", "total": 250},
        key="user_beta",
    )
    assert msg2.id != msg1.id

    # Fetch messages
    messages = bus.fetch_messages("orders.stream", partition=msg1.partition, offset=0)
    assert len(messages) >= 1
    assert messages[0].key == "user_alpha"


def test_clickhouse_ingestion_buffer():
    bus = EventStreamBusService()
    ch_buffer = ClickHouseIngestionBufferService()

    sink = ch_buffer.register_sink(
        name="telemetry-ch-sink",
        source_topic="telemetry.stream",
        target_table="analytics.telemetry_raw",
        batch_size=3,
    )
    assert sink.batch_size == 3

    # Produce messages and ingest
    msg1, _ = bus.publish("telemetry.stream", {"cpu": 45.2})
    msg2, _ = bus.publish("telemetry.stream", {"cpu": 55.8})

    res1 = ch_buffer.ingest_message(sink.id, msg1)
    assert res1["buffered_count"] == 1
    assert res1["flushed"] is False

    res2 = ch_buffer.ingest_message(sink.id, msg2)
    assert res2["buffered_count"] == 2
    assert res2["flushed"] is False

    # 3rd message triggers batch threshold flush
    msg3, _ = bus.publish("telemetry.stream", {"cpu": 72.1})
    res3 = ch_buffer.ingest_message(sink.id, msg3)
    assert res3["buffered_count"] == 0
    assert res3["flushed"] is True

    batches = ch_buffer.get_flushed_batches(sink.id)
    assert len(batches) == 1
    assert len(batches[0]) == 3

    # Manual flush on empty buffer returns 0
    flush_res = ch_buffer.flush(sink.id)
    assert flush_res["flushed_count"] == 0

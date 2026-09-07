# --- DNK-MRH-HEADER ---
# mrh_id: "tests/stream/test_stream_consumer_and_dlq.py"
# purpose: "Unit tests for Stream Consumer Coordinator, DLQ, and Health Probes (DNK-STREAM-001 Phase 3)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest

from apps.api.services.event_stream_bus import EventStreamBusService
from apps.api.services.stream_consumer_coordinator import StreamConsumerCoordinator
from apps.api.services.stream_dead_letter_queue_service import StreamDeadLetterQueueService
from apps.api.services.stream_health_probe_service import StreamHealthProbeService


@pytest.fixture
def stream_env():
    bus = EventStreamBusService()
    coordinator = StreamConsumerCoordinator(bus)
    dlq = StreamDeadLetterQueueService(bus, max_retries=3)
    health = StreamHealthProbeService(bus, coordinator)
    return {
        "bus": bus,
        "coordinator": coordinator,
        "dlq": dlq,
        "health": health,
    }


def test_consumer_group_registration_and_rebalance(stream_env):
    bus: EventStreamBusService = stream_env["bus"]
    coordinator: StreamConsumerCoordinator = stream_env["coordinator"]

    topic = bus.create_topic("orders.stream", partitions_count=4)
    assert topic.partitions_count == 4

    group = coordinator.register_consumer_group(
        group_id="order-processors",
        topic_name="orders.stream",
    )
    assert group.id == "order-processors"
    assert group.topic_name == "orders.stream"

    # Member 1 joins -> gets all 4 partitions [0, 1, 2, 3]
    res1 = coordinator.join_group("order-processors", "worker_1")
    assert res1["generation"] == 2
    assert sorted(res1["assigned_partitions"]) == [0, 1, 2, 3]

    # Member 2 joins -> rebalances to 2 partitions each
    res2 = coordinator.join_group("order-processors", "worker_2")
    assert res2["generation"] == 3
    # worker_1 and worker_2 each have 2 partitions
    worker1_parts = coordinator._partition_assignments["order-processors"]["worker_1"]
    worker2_parts = coordinator._partition_assignments["order-processors"]["worker_2"]
    assert len(worker1_parts) == 2
    assert len(worker2_parts) == 2
    assert sorted(worker1_parts + worker2_parts) == [0, 1, 2, 3]

    # Member 2 leaves -> worker_1 gets all 4 partitions back
    left = coordinator.leave_group("order-processors", "worker_2")
    assert left is True
    assert sorted(coordinator._partition_assignments["order-processors"]["worker_1"]) == [0, 1, 2, 3]


def test_consumer_poll_and_offset_commit(stream_env):
    bus: EventStreamBusService = stream_env["bus"]
    coordinator: StreamConsumerCoordinator = stream_env["coordinator"]

    bus.create_topic("payments.stream", partitions_count=2)
    coordinator.register_consumer_group("payment-group", "payments.stream")
    join_res = coordinator.join_group("payment-group", "payment_worker_1")
    assert sorted(join_res["assigned_partitions"]) == [0, 1]

    # Publish messages
    msg1, _ = bus.publish("payments.stream", {"payment_id": "p1"}, key="key-1")
    msg2, _ = bus.publish("payments.stream", {"payment_id": "p2"}, key="key-1")
    msg3, _ = bus.publish("payments.stream", {"payment_id": "p3"}, key="key-2")

    # Poll messages
    polled = coordinator.poll("payment-group", "payment_worker_1", max_records=10)
    assert len(polled) >= 1

    # Check lag before commit
    lag_info = coordinator.get_group_lag("payment-group")
    assert lag_info["total_lag"] == 3

    # Commit offset for the partitions
    for msg in [msg1, msg2, msg3]:
        coordinator.commit_offset("payment-group", partition=msg.partition, offset=msg.offset)

    lag_after = coordinator.get_group_lag("payment-group")
    assert lag_after["total_lag"] == 0


def test_dead_letter_queue_routing_and_replay(stream_env):
    bus: EventStreamBusService = stream_env["bus"]
    dlq: StreamDeadLetterQueueService = stream_env["dlq"]

    bus.create_topic("inventory.events", partitions_count=2)

    # Route bad event to DLQ
    poison_payload = {"sku": "INVALID_SKU", "qty": -500}
    dlq_event = dlq.route_to_dlq(
        original_topic="inventory.events",
        payload=poison_payload,
        error_reason="NegativeInventoryQuantityError",
        original_partition=1,
        original_offset=42,
    )

    assert dlq_event.status == "PENDING"
    assert dlq_event.retry_count == 0
    assert dlq_event.max_retries == 3

    # Verify DLQ stats
    stats = dlq.get_dlq_stats()
    assert stats["total_dlq_events"] == 1
    assert stats["pending"] == 1

    # Replay event back to topic
    success, replayed_msg, message = dlq.replay_event(dlq_event.id)
    assert success is True
    assert replayed_msg is not None
    assert replayed_msg.topic_name == "inventory.events"
    assert replayed_msg.headers.get("x-dlq-replayed-from") == dlq_event.id

    updated_event = dlq.get_event(dlq_event.id)
    assert updated_event is not None
    assert updated_event.status == "RESOLVED"
    assert updated_event.retry_count == 1


def test_stream_health_probe_e2e(stream_env):
    health: StreamHealthProbeService = stream_env["health"]

    probe_res = health.run_e2e_probe()
    assert probe_res["status"] == "HEALTHY"
    assert probe_res["success"] is True
    assert probe_res["round_trip_latency_ms"] >= 0

    cluster_health = health.get_cluster_health()
    assert cluster_health["status"] == "HEALTHY"
    assert cluster_health["topics_count"] >= 1
    assert cluster_health["total_partitions"] >= 2

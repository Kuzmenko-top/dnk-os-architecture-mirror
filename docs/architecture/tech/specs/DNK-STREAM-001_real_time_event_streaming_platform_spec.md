<!-- --- DNK-MRH-HEADER ---
mrh_id: "DOC-SPEC-DNK-STREAM-001"
purpose: "TaskDNA Specification for Real-Time Event Streaming Platform (DNK-STREAM-001)"
canonical_source: true
alters_files: [
  "apps/api/db/models/stream_topic.py",
  "apps/api/db/models/stream_event_schema.py",
  "apps/api/db/models/stream_message.py",
  "apps/api/db/models/stream_consumer_group.py",
  "apps/api/db/models/stream_dead_letter_event.py",
  "apps/api/db/models/stream_ingestion_sink.py",
  "apps/api/services/stream_schema_registry_service.py",
  "apps/api/services/stream_event_bus_service.py",
  "apps/api/services/stream_consumer_manager_service.py",
  "apps/api/services/stream_clickhouse_sink_service.py",
  "apps/api/routers/stream_router.py"
]
triggers_tasks: ["DNK-STREAM-001-PHASE1", "DNK-STREAM-001-PHASE2", "DNK-STREAM-001-PHASE3", "DNK-STREAM-001-PHASE4"]
status: "Active"
version: "1.0.0"
updated_at: "2026-08-29"
author: "DNK-e.com Maksym & Gerych Prime"
--- END DNK-MRH-HEADER --->

# 🌊 DNK-STREAM-001: Real-Time Event Streaming Platform

## 1. Overview & Architectural Objectives
DNK-STREAM-001 introduces a high-throughput, fault-tolerant Real-Time Event Streaming Platform for the DNK OS ecosystem. It provides distributed pub/sub pub-broker primitives, strict JSONSchema/Avro/Protobuf schema evolution & validation via Schema Registry, resilient Consumer Groups with offset tracking and partition rebalancing, Dead-Letter Queue (DLQ) automated replay, and micro-batched high-volume analytical sinks (ClickHouse / OLAP).

## 2. Core Architectural Pillars
1. **Stream Topics & Event Schema Registry**:
   - Declarative topic lifecycle with partition count, retention policies (time/size), and compaction strategies.
   - Strict schema validation, version evolution (`BACKWARD`, `FORWARD`, `FULL`), and compatibility verification.
2. **Event Streaming Bus & High-Throughput Ingestion**:
   - In-memory lock-free partitioned event ring buffer with persistence hooks.
   - Message ordering guarantees per partition key with SHA-256 deduplication hashing.
3. **Consumer Groups, Offsets & Dead-Letter Queue (DLQ)**:
   - Consumer group coordination, heartbeat management, and commit offset tracking.
   - Automatic quarantine of unparseable or poison-pill events into Dead-Letter Queue with manual and automated replay capabilities.
4. **ClickHouse OLAP Ingestion Sink & REST / SSE Gateway**:
   - High-performance asynchronous micro-batch buffer for high-cardinality analytical tables.
   - FastAPI REST endpoints for publishing, topic administration, schema registration, consumer management, and SSE stream tailing.

## 3. Data Models (Phase 1)
- `StreamTopic`: Topic metadata, partition configuration, replication factor, retention hours, and status.
- `StreamEventSchema`: Registered schemas with version, format (`JSON_SCHEMA`, `AVRO`, `PROTOBUF`), and compatibility rules.
- `StreamMessage`: Envelope containing topic, partition, offset, payload, headers, trace_id, and timestamp.
- `StreamConsumerGroup`: Consumer group metadata, active members, rebalance generation, and committed offsets.
- `StreamDeadLetterEvent`: Quarantined failed messages with error details, retry count, and replay status.
- `StreamIngestionSink`: Analytical sink configurations (ClickHouse, BigQuery, S3) with flush thresholds and buffer statistics.

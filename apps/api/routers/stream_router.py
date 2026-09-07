# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/stream_router.py"
# purpose: "FastAPI REST and SSE Router for Real-Time Event Streaming Platform (DNK-STREAM-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from apps.api.services.clickhouse_ingestion_buffer import ClickHouseIngestionBufferService
from apps.api.services.event_schema_registry import EventSchemaRegistryService
from apps.api.services.event_stream_bus import EventStreamBusService
from apps.api.services.stream_consumer_coordinator import StreamConsumerCoordinator
from apps.api.services.stream_dead_letter_queue_service import StreamDeadLetterQueueService
from apps.api.services.stream_health_probe_service import StreamHealthProbeService

router = APIRouter(prefix="/api/v1/stream", tags=["Event Streaming"])

# Global Service Singletons (In-Memory / Shared Engine)
stream_bus_service = EventStreamBusService()
schema_registry_service = EventSchemaRegistryService()
clickhouse_buffer_service = ClickHouseIngestionBufferService()
consumer_coordinator_service = StreamConsumerCoordinator(stream_bus_service)
dlq_service = StreamDeadLetterQueueService(stream_bus_service)
health_probe_service = StreamHealthProbeService(stream_bus_service, consumer_coordinator_service)


# ---------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------

class CreateTopicRequest(BaseModel):
    name: str = Field(..., description="Topic name (e.g. orders.stream)")
    workspace_id: str = Field("ws-alpha-001", description="Workspace ID")
    partitions_count: int = Field(4, description="Number of partitions")
    retention_ms: int = Field(86400000, description="Retention time in ms")
    max_message_size_bytes: int = Field(1048576, description="Max message size in bytes")
    is_compacted: bool = Field(False, description="Log compaction flag")
    schema_id: Optional[str] = Field(None, description="Optional linked schema ID")


class RegisterSchemaRequest(BaseModel):
    subject: str = Field(..., description="Schema subject name")
    schema_type: str = Field("JSONSCHEMA", description="Schema type: JSONSCHEMA, AVRO, PROTOBUF")
    definition: Dict[str, Any] = Field(..., description="Schema definition JSON")
    compatibility_mode: str = Field("BACKWARD", description="Compatibility mode: BACKWARD, FORWARD, FULL, NONE")
    workspace_id: str = Field("ws-alpha-001", description="Workspace ID")


class PublishEventRequest(BaseModel):
    topic_name: str = Field(..., description="Target topic name")
    payload: Dict[str, Any] = Field(..., description="Event payload dictionary")
    key: Optional[str] = Field(None, description="Partition routing key")
    headers: Optional[Dict[str, Any]] = Field(None, description="Message metadata headers")
    schema_id: Optional[str] = Field(None, description="Schema ID to validate against")
    idempotency_key: Optional[str] = Field(None, description="Client idempotency key")
    workspace_id: str = Field("ws-alpha-001", description="Workspace ID")


class JoinConsumerGroupRequest(BaseModel):
    group_id: str = Field(..., description="Consumer group identifier")
    member_id: str = Field(..., description="Consumer worker/client identifier")
    topic_name: str = Field(..., description="Subscribed topic name")
    workspace_id: str = Field("ws-alpha-001", description="Workspace ID")


class PollConsumerGroupRequest(BaseModel):
    group_id: str = Field(..., description="Consumer group identifier")
    member_id: str = Field(..., description="Consumer worker/client identifier")
    max_records: int = Field(100, description="Maximum number of records to fetch")


class CommitOffsetRequest(BaseModel):
    group_id: str = Field(..., description="Consumer group identifier")
    partition: int = Field(..., description="Partition ID")
    offset: int = Field(..., description="Offset to commit")


class ReplayDLQRequest(BaseModel):
    target_topic: Optional[str] = Field(None, description="Optional destination topic override")


# ---------------------------------------------------------
# Topics & Schemas Endpoints
# ---------------------------------------------------------

@router.post("/topics", status_code=status.HTTP_201_CREATED)
def create_topic(req: CreateTopicRequest):
    topic = stream_bus_service.create_topic(
        name=req.name,
        workspace_id=req.workspace_id,
        partitions_count=req.partitions_count,
    )
    if req.schema_id:
        topic.schema_id = req.schema_id
    return {"status": "success", "topic": topic.to_dict()}


@router.get("/topics")
def list_topics(workspace_id: str = Query("ws-alpha-001")):
    topics = stream_bus_service.list_topics(workspace_id=workspace_id)
    return {"topics": [t.to_dict() for t in topics]}


@router.post("/schemas", status_code=status.HTTP_201_CREATED)
def register_schema(req: RegisterSchemaRequest):
    schema = schema_registry_service.register_schema(
        subject=req.subject,
        schema_definition=req.definition,
        schema_format=req.schema_type,
        compatibility_mode=req.compatibility_mode,
        workspace_id=req.workspace_id,
    )
    return {"status": "success", "schema": schema.to_dict()}


@router.get("/schemas/{subject}/latest")
def get_latest_schema(subject: str):
    schema = schema_registry_service.get_latest_schema(subject)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema subject '{subject}' not found.")
    return {"schema": schema.to_dict()}


# ---------------------------------------------------------
# Publishing & Ingestion Endpoints
# ---------------------------------------------------------

@router.post("/publish")
def publish_event(req: PublishEventRequest):
    # If schema validation requested
    if req.schema_id:
        schema = schema_registry_service.get_schema_by_id(req.schema_id)
        if schema:
            valid, err = schema_registry_service.validate_payload(schema, req.payload)
            if not valid:
                # Route to DLQ automatically
                dlq_event = dlq_service.route_to_dlq(
                    original_topic=req.topic_name,
                    payload=req.payload,
                    error_reason=f"SchemaValidationFailed: {err}",
                    workspace_id=req.workspace_id,
                    headers=req.headers,
                )
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "SchemaValidationFailed",
                        "message": err,
                        "dlq_event_id": dlq_event.id,
                    },
                )

    msg, is_dup = stream_bus_service.publish(
        topic_name=req.topic_name,
        payload=req.payload,
        key=req.key,
        headers=req.headers,
        schema_id=req.schema_id,
        idempotency_key=req.idempotency_key,
        workspace_id=req.workspace_id,
    )

    return {
        "status": "success",
        "is_duplicate": is_dup,
        "message": msg.to_dict(),
    }


# ---------------------------------------------------------
# Consumer Groups & Offset Management
# ---------------------------------------------------------

@router.post("/consumer-groups/join")
def join_consumer_group(req: JoinConsumerGroupRequest):
    # Ensure consumer group registered
    group = consumer_coordinator_service.get_group(req.group_id)
    if not group:
        group = consumer_coordinator_service.register_consumer_group(
            group_id=req.group_id,
            topic_name=req.topic_name,
            workspace_id=req.workspace_id,
        )

    join_info = consumer_coordinator_service.join_group(
        group_id=req.group_id,
        member_id=req.member_id,
    )
    return {
        "group_id": req.group_id,
        "member_id": req.member_id,
        "generation": join_info["generation"],
        "assigned_partitions": join_info["assigned_partitions"],
    }


@router.post("/consumer-groups/poll")
def poll_consumer_group(req: PollConsumerGroupRequest):
    messages = consumer_coordinator_service.poll(
        group_id=req.group_id,
        member_id=req.member_id,
        max_records=req.max_records,
    )
    return {
        "group_id": req.group_id,
        "member_id": req.member_id,
        "count": len(messages),
        "messages": [m.to_dict() for m in messages],
    }


@router.post("/consumer-groups/commit")
def commit_offset(req: CommitOffsetRequest):
    res = consumer_coordinator_service.commit_offset(
        group_id=req.group_id,
        partition=req.partition,
        offset=req.offset,
    )
    return res


@router.get("/consumer-groups/{group_id}/lag")
def get_consumer_group_lag(group_id: str):
    lag_info = consumer_coordinator_service.get_group_lag(group_id)
    return lag_info


# ---------------------------------------------------------
# Dead-Letter Queue (DLQ) Endpoints
# ---------------------------------------------------------

@router.get("/dlq")
def list_dlq_events(
    topic_name: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    workspace_id: Optional[str] = Query(None),
):
    events = dlq_service.list_events(
        topic_name=topic_name,
        status=status_filter,
        workspace_id=workspace_id,
    )
    stats = dlq_service.get_dlq_stats(workspace_id=workspace_id)
    return {
        "stats": stats,
        "events": [e.to_dict() for e in events],
    }


@router.post("/dlq/{event_id}/replay")
def replay_dlq_event(event_id: str, req: Optional[ReplayDLQRequest] = None):
    target_topic = req.target_topic if req else None
    success, replayed_msg, message = dlq_service.replay_event(
        event_id=event_id,
        target_topic=target_topic,
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {
        "status": "success",
        "message": message,
        "replayed_message": replayed_msg.to_dict() if replayed_msg else None,
    }


# ---------------------------------------------------------
# Probes, Health & SSE Stream
# ---------------------------------------------------------

@router.post("/probes/e2e")
def run_e2e_probe(
    topic_name: str = Query("health.synthetic.probe"),
    workspace_id: str = Query("ws-alpha-001"),
):
    probe = health_probe_service.run_e2e_probe(
        topic_name=topic_name,
        workspace_id=workspace_id,
    )
    return probe


@router.get("/health")
def get_stream_cluster_health(workspace_id: str = Query("ws-alpha-001")):
    return health_probe_service.get_cluster_health(workspace_id=workspace_id)


@router.get("/events/sse")
async def sse_event_stream(
    topic_name: str = Query(..., description="Topic name to stream from"),
    partition: int = Query(0, description="Partition index"),
    from_offset: int = Query(0, description="Starting offset"),
    max_events: Optional[int] = Query(None, description="Max events to stream before closing"),
):
    """Streams real-time messages over Server-Sent Events (SSE)."""

    async def event_generator():
        current_offset = from_offset
        yielded_count = 0
        while True:
            messages = stream_bus_service.consume(
                topic_name=topic_name,
                partition=partition,
                from_offset=current_offset,
                limit=50,
            )
            for msg in messages:
                current_offset = msg.offset + 1
                yield f"data: {json.dumps(msg.to_dict())}\n\n"
                yielded_count += 1
                if max_events is not None and yielded_count >= max_events:
                    return
            if max_events is not None and yielded_count >= max_events:
                return
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_timeline"
# purpose: "Read-only Live Timeline REST API router for unified system, swarm, adapter, and CI/CD events stream."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


class TimelineEvent(BaseModel):
    id: str
    timestamp: str
    source: str
    category: str
    level: str
    title: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimelineEnvelope(BaseModel):
    data: List[TimelineEvent]
    data_source: str = "fixture"
    total_count: int
    fetched_at: str


TIMELINE_FIXTURES: List[Dict[str, Any]] = [
    {
        "id": "evt-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "github",
        "category": "governance",
        "level": "INFO",
        "title": "PR #30 Verified by Quality Gate",
        "message": "PR #30 checks succeeded: 100% green on all regression tests.",
        "metadata": {"pr_number": 30, "status": "GREEN"}
    },
    {
        "id": "evt-002",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "shopify",
        "category": "adapter",
        "level": "INFO",
        "title": "Shopify Storefront Sync Snapshot",
        "message": "Liquid theme AST tree parsed cleanly without errors.",
        "metadata": {"theme_id": "dawn-main", "assets_count": 42}
    },
    {
        "id": "evt-003",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "swarm",
        "category": "orchestrator",
        "level": "INFO",
        "title": "TaskDNA Execution Step Completed",
        "message": "Agent gerych_builder finalized Working Cabinet UX Polish.",
        "metadata": {"agent": "gerych_builder", "task": "DNK-UX-002"}
    },
    {
        "id": "evt-004",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "system",
        "category": "quality_gate",
        "level": "SUCCESS",
        "title": "Zero-Waste High-Velocity Protocol Active",
        "message": "FastAPI backend and Next.js frontend health checks green.",
        "metadata": {"protocol": "v4.3.0"}
    }
]


@router.get("/events", response_model=TimelineEnvelope)
async def get_timeline_events(
    source: Optional[str] = Query(None, description="Filter by event source: github, shopify, system, swarm"),
    category: Optional[str] = Query(None, description="Filter by category: adapter, governance, quality_gate, orchestrator"),
    level: Optional[str] = Query(None, description="Filter by log level: INFO, WARNING, ERROR, SUCCESS"),
    limit: int = Query(50, ge=1, le=200, description="Max number of events to return")
):
    """Retrieve filtered timeline event stream for Working Cabinet Live Timeline."""
    events = TIMELINE_FIXTURES

    if source:
        events = [e for e in events if e.get("source") == source]
    if category:
        events = [e for e in events if e.get("category") == category]
    if level:
        events = [e for e in events if e.get("level") == level]

    events = events[:limit]

    return TimelineEnvelope(
        data=[TimelineEvent(**e) for e in events],
        data_source="fixture",
        total_count=len(events),
        fetched_at=datetime.now(timezone.utc).isoformat()
    )


@router.get("/v1/events", response_model=TimelineEnvelope)
async def get_timeline_events_v1(
    source: Optional[str] = Query(None, description="Filter by event source: github, shopify, system, swarm"),
    category: Optional[str] = Query(None, description="Filter by category: adapter, governance, quality_gate, orchestrator"),
    level: Optional[str] = Query(None, description="Filter by log level: INFO, WARNING, ERROR, SUCCESS"),
    limit: int = Query(50, ge=1, le=200, description="Max number of events to return")
):
    """Alias for timeline events under /v1."""
    return await get_timeline_events(source=source, category=category, level=level, limit=limit)

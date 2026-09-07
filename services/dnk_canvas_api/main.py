import base64
# --- DNK-MRH-HEADER ---
# mrh_id: "main.py"
# purpose: "Production FastAPI backend service for Canvas Engine persistence, snaps, and design runs with PostgreSQL and Redis."
# canonical_source: true
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import os
import pathlib
import time
import json
import logging
import hashlib
import asyncio
from typing import Optional, List, Dict, Any, Set
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import redis
from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks, WebSocket, WebSocketDisconnect, Header, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey, BigInteger, UniqueConstraint, DateTime, JSON, Float

from sqlalchemy.types import TypeDecorator, CHAR
import uuid

class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID as pg_UUID
            return dialect.type_descriptor(pg_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return str(value)

UUID = lambda as_uuid=False: GUID()

from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import IntegrityError

try:
    from services.dnk_canvas_api.ai_models import (
        CanvasCutoutRequest, CanvasCutoutResponse,
        CanvasRelightRequest, CanvasRelightResponse,
        CanvasGenerateLayerRequest, CanvasGenerateLayerResponse,
        birefnet_client, iclight_client, flux_layerdiffuse_client,
        BiRefNetClient, ICLightClient, FluxLayerDiffuseClient
    )
except ImportError:
    from ai_models import (
        CanvasCutoutRequest, CanvasCutoutResponse,
        CanvasRelightRequest, CanvasRelightResponse,
        CanvasGenerateLayerRequest, CanvasGenerateLayerResponse,
        birefnet_client, iclight_client, flux_layerdiffuse_client,
        BiRefNetClient, ICLightClient, FluxLayerDiffuseClient
    )


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dnk_canvas_api")

# DB & Redis connection strings from env
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/dnk_hub")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Declarative models
Base = declarative_base()

# --- Legacy Models ---
class Canvas(Base):
    __tablename__ = "canvases"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time() * 1000))
    updated_at = Column(BigInteger, nullable=False, default=lambda: int(time.time() * 1000))

class CanvasSnapshot(Base):
    __tablename__ = "canvas_snapshots"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    canvas_id = Column(String(36), ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    elements_json = Column(Text, nullable=False)
    app_state_json = Column(Text, nullable=False)
    files_json = Column(Text, nullable=False)
    client_request_id = Column(String(100), nullable=False)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time() * 1000))

class DesignRun(Base):
    __tablename__ = "design_runs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    canvas_id = Column(String(36), ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False)  # queued, running, completed, failed
    command = Column(String(255), nullable=False)
    payload_json = Column(Text, nullable=False)
    artifact_id = Column(String(36), nullable=True)
    idempotency_key = Column(String(255), nullable=True, unique=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time() * 1000))
    updated_at = Column(BigInteger, nullable=False, default=lambda: int(time.time() * 1000))

class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    canvas_id = Column(String(36), ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    content_json = Column(Text, nullable=False)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time() * 1000))
    status = Column(String(50), nullable=True, default="shadow_persisted")
    version = Column(Integer, nullable=True, default=1)
    expires_at = Column(BigInteger, nullable=True)
    validation_status = Column(String(50), nullable=True, default="valid")
    idempotency_key = Column(String(255), nullable=True, unique=True)

class ActivityEvent(Base):
    __tablename__ = "activity_events"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id = Column(String(36), nullable=False)
    canvas_id = Column(String(36), nullable=False)
    event_type = Column(String(100), nullable=False)
    from_state = Column(String(50), nullable=True)
    to_state = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(BigInteger, nullable=False, default=lambda: int(time.time() * 1000))

# --- New Models under hub_memory schema (DNK_CANVAS_DATA_MODEL.md) ---
class CanvasDocument(Base):
    __tablename__ = "canvas_documents"
    __table_args__ = {"schema": "hub_memory"}

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(UUID(as_uuid=False), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String(64), nullable=False, default="excalidraw")
    current_revision_id = Column(UUID(as_uuid=False), nullable=True)
    created_by = Column(String(255), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    status = Column(String(32), nullable=False, default="active")
    canvas_metadata = Column("metadata", JSON, nullable=False, default=dict)

class CanvasRevision(Base):
    __tablename__ = "canvas_revisions"
    __table_args__ = (
        UniqueConstraint("document_id", "revision_number", name="uq_document_revision"),
        {"schema": "hub_memory"}
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_documents.id", ondelete="CASCADE"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    scene_json = Column(JSON, nullable=False)
    scene_checksum = Column(String(64), nullable=False)
    created_by = Column(String(255), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    change_summary = Column(Text, nullable=True)
    parent_revision_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_revisions.id", ondelete="SET NULL"), nullable=True)

class CanvasAsset(Base):
    __tablename__ = "canvas_assets"
    __table_args__ = (
        UniqueConstraint("workspace_id", "sha256", name="uq_workspace_sha256"),
        {"schema": "hub_memory"}
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(UUID(as_uuid=False), nullable=False)
    storage_key = Column(String(512), nullable=False, unique=True)
    sha256 = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="pending_upload") # pending_upload, uploaded, verifying, verified, rejected, deleted
    mime_type = Column(String(128), nullable=False)
    byte_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

from sqlalchemy import Index, text

class CanvasAssetLink(Base):
    __tablename__ = "canvas_asset_links"
    __table_args__ = (
        Index("uq_canvas_asset_element_link", "document_id", "element_id", "asset_id", unique=True, sqlite_where=text("element_id IS NOT NULL"), postgresql_where=text("element_id IS NOT NULL")),
        Index("uq_canvas_asset_document_link", "document_id", "asset_id", unique=True, sqlite_where=text("element_id IS NULL"), postgresql_where=text("element_id IS NULL")),
        {"schema": "hub_memory"}
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    asset_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_assets.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_documents.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(String(255), nullable=True)
    relation_type = Column(String(64), nullable=False, default="references")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class CanvasLink(Base):
    __tablename__ = "canvas_links"
    __table_args__ = (
        Index("uq_canvas_element_link", "document_id", "element_id", "entity_type", "entity_id", "relation_type", unique=True, sqlite_where=text("element_id IS NOT NULL"), postgresql_where=text("element_id IS NOT NULL")),
        Index("uq_canvas_document_link", "document_id", "entity_type", "entity_id", "relation_type", unique=True, sqlite_where=text("element_id IS NULL"), postgresql_where=text("element_id IS NULL")),
        {"schema": "hub_memory"}
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_documents.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(String(255), nullable=True)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(255), nullable=False)
    relation_type = Column(String(64), nullable=False, default="references")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class CanvasAuditEvent(Base):
    __tablename__ = "canvas_audit_events"
    __table_args__ = {"schema": "hub_memory"}

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    document_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_documents.id", ondelete="CASCADE"), nullable=True)
    actor_type = Column(String(64), nullable=False)
    actor_id = Column(String(255), nullable=False)
    event_type = Column(String(128), nullable=False)
    revision_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_revisions.id", ondelete="SET NULL"), nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class CanvasCompetitor(Base):
    __tablename__ = "canvas_competitors"
    __table_args__ = {"schema": "hub_memory"}

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    website_url = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="active")
    competitor_metadata = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class CanvasEvidence(Base):
    __tablename__ = "canvas_evidences"
    __table_args__ = (
        UniqueConstraint("workspace_id", "sha256", name="uq_workspace_evidence_sha256"),
        {"schema": "hub_memory"}
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    competitor_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_competitors.id", ondelete="SET NULL"), nullable=True)
    asset_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_assets.id", ondelete="SET NULL"), nullable=True)
    source_url = Column(String(512), nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    sha256 = Column(String(64), nullable=False)
    evidence_status = Column(String(32), nullable=False, default="captured")
    storage_key = Column(String(512), nullable=False)
    storage_mode = Column(String(32), nullable=False, default="fixture")
    evidence_metadata = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class CanvasInsight(Base):
    __tablename__ = "canvas_insights"
    __table_args__ = {"schema": "hub_memory"}

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_documents.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(String(255), nullable=False, index=True)
    evidence_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_evidences.id", ondelete="SET NULL"), nullable=True)
    competitor_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_competitors.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(32), nullable=False, default="proposed")
    source_references = Column(JSON, nullable=False, default=dict)
    created_by = Column(String(255), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class FlowerDraft(Base):
    __tablename__ = "flower_drafts"
    __table_args__ = {"schema": "hub_memory"}

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    workspace_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_documents.id", ondelete="CASCADE"), nullable=False)
    element_id = Column(String(255), nullable=False, index=True)
    insight_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.canvas_insights.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="draft")
    flower_type = Column(String(64), nullable=False, default="task_flower")
    content = Column(JSON, nullable=False, default=dict)
    source_references = Column(JSON, nullable=False, default=dict)
    created_by = Column(String(255), nullable=False, default="user")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))



class DesignSkill(Base):
    __tablename__ = "design_skills"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    risk_level = Column(String(32), nullable=False, default="L1")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class DesignSkillVersion(Base):
    __tablename__ = "design_skill_versions"
    __table_args__ = (
        UniqueConstraint("skill_id", "version", name="uq_skill_version"),
        {"schema": "hub_memory"}
    )
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    skill_id = Column(String(64), ForeignKey("hub_memory.design_skills.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(32), nullable=False)
    input_schema = Column(JSON, nullable=False)
    output_artifacts = Column(JSON, nullable=False)
    approval_required = Column(Integer, nullable=False, default=0) # 0=False, 1=True
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class SupervisorRun(Base):
    __tablename__ = "supervisor_runs"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    design_run_id = Column(UUID(as_uuid=False), nullable=False)
    workflow_id = Column(String(64), nullable=False)
    status = Column(String(50), nullable=False, default="queued")
    current_step = Column(Integer, nullable=False, default=0)
    supervisor_version = Column(String(32), nullable=False, default="1.0.0")
    model_policy = Column(String(64), nullable=False, default="gemma-4")
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failure_code = Column(String(64), nullable=True)

class AgentStep(Base):
    __tablename__ = "agent_steps"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    supervisor_run_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.supervisor_runs.id", ondelete="CASCADE"), nullable=False)
    step_number = Column(Integer, nullable=False)
    agent_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    input_context = Column(JSON, nullable=True)
    output_summary = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

class ToolCall(Base):
    __tablename__ = "tool_calls"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    agent_step_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.agent_steps.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    arguments_json = Column(JSON, nullable=False)
    result_json = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    duration_ms = Column(Integer, nullable=True)
    error_code = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    supervisor_run_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.supervisor_runs.id", ondelete="CASCADE"), nullable=False)
    step_id = Column(UUID(as_uuid=False), nullable=True)
    approval_type = Column(String(100), nullable=False)
    risk_level = Column(String(32), nullable=False)
    proposed_action_json = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    requested_by = Column(String(255), nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

class DesignContext(Base):
    __tablename__ = "design_contexts"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    supervisor_run_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.supervisor_runs.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=False), nullable=False)
    canvas_id = Column(UUID(as_uuid=False), nullable=False)
    prompt = Column(Text, nullable=False)
    design_system_id = Column(String(100), nullable=False)
    last_snapshot_id = Column(UUID(as_uuid=False), nullable=True)
    collected_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class ArtifactReview(Base):
    __tablename__ = "artifact_reviews"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    supervisor_run_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.supervisor_runs.id", ondelete="CASCADE"), nullable=False)
    artifact_id = Column(UUID(as_uuid=False), nullable=False)
    reviewer_agent = Column(String(100), nullable=False)
    critique_text = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class LlmRequest(Base):
    __tablename__ = "llm_requests"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    supervisor_run_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.supervisor_runs.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    request_id = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    input_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class LlmOutput(Base):
    __tablename__ = "llm_outputs"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    llm_request_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.llm_requests.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False, default="success")
    output_hash = Column(String(64), nullable=False)
    output_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class ProviderUsage(Base):
    __tablename__ = "provider_usage"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    llm_request_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.llm_requests.id", ondelete="CASCADE"), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Integer, nullable=False, default=0)
    cost_estimate = Column(Float, nullable=False, default=0.0)
    error_code = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class ModelToolCall(Base):
    __tablename__ = "model_tool_calls"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    llm_request_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.llm_requests.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    arguments_json = Column(JSON, nullable=False)
    result_json = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class DesignValidationResult(Base):
    __tablename__ = "design_validation_results"
    __table_args__ = {"schema": "hub_memory"}
    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    supervisor_run_id = Column(UUID(as_uuid=False), ForeignKey("hub_memory.supervisor_runs.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False) # passed, failed
    errors_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

# Initialize engine and Session
AUTO_CREATE_SCHEMA = os.getenv("AUTO_CREATE_SCHEMA", "false").lower() == "true"

try:
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
    # Ping database connection
    with engine.connect() as conn:
        pass
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Successfully connected to PostgreSQL database.")

    if AUTO_CREATE_SCHEMA:
        with engine.begin() as conn:
            from sqlalchemy import text
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS hub_memory"))
        Base.metadata.create_all(bind=engine)
        logger.info("Auto-created database tables (AUTO_CREATE_SCHEMA=true).")
    else:
        # Check migrations are at head in production/normal start
        try:
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            from alembic.runtime.migration import MigrationContext

            base_dir = os.path.dirname(os.path.abspath(__file__))
            ini_path = os.path.join(base_dir, "alembic.ini")
            alembic_cfg = Config(ini_path)
            script_location = alembic_cfg.get_main_option("script_location")
            if script_location and not os.path.isabs(script_location):
                alembic_cfg.set_main_option("script_location", os.path.join(base_dir, script_location))
            script = ScriptDirectory.from_config(alembic_cfg)
            head_revision = script.get_current_head()

            with engine.connect() as connection:
                context = MigrationContext.configure(connection)
                current_revision = context.get_current_revision()

            logger.info(f"Database migration check: current={current_revision}, head={head_revision}")
            import sys
            is_alembic = any("alembic" in arg for arg in sys.argv) if sys.argv else False
            if current_revision != head_revision and not is_alembic:
                raise RuntimeError(f"Database schema is not up-to-date! Current revision: {current_revision}, head: {head_revision}")
        except Exception as migration_error:
            logger.error(f"Migration verification failed: {migration_error}")
            raise migration_error

except Exception as e:
    is_prod = (os.getenv("ENV") == "production" or os.getenv("NODE_ENV") == "production") and os.getenv("ENV") != "test" and os.getenv("APP_ENV") != "test"
    if is_prod:
        logger.critical(f"FATAL: Database connection failed in production! SQLite fallback is prohibited: {e}")
        raise RuntimeError(f"Database connection failed in production: {e}")
    logger.warning(f"Failed to initialize PostgreSQL or verify migrations. Using SQLite fallback: {e}")
    DATABASE_URL = os.getenv("SQLITE_FALLBACK_URL", "sqlite:////tmp/canvas_production_fallback.db")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        execution_options={"schema_translate_map": {"hub_memory": None}}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis client
try:
    r_client = redis.from_url(REDIS_URL)
    r_client.ping()
    logger.info("Successfully connected to Redis.")
except Exception as e:
    logger.warning(f"Redis not available. Using local simulated pub/sub. Error: {e}")
    r_client = None

# FastAPI App
test_router = APIRouter()


def is_production_env() -> bool:
    return any(
        os.getenv(name, "").lower() in {"production", "prod"}
        for name in ("APP_ENV", "ENV", "NODE_ENV")
    )

app = FastAPI(title="DNK Canvas Engine Production API", version="1.1.0")

# Include test-only router if in test environment (P0 Physical Absence Isolation)
if (
    os.getenv("APP_ENV") == "test"
    and os.getenv("ENV") == "test"
    and os.getenv("NODE_ENV") != "production"
):
    app.include_router(test_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from apps.api.routers.product_launch import router as product_launch_router
    app.include_router(product_launch_router)
except Exception as exc:
    logger.warning("Could not mount product_launch router: %s", exc)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def home():
    return {"message": "DNK Canvas Engine API"}


import uuid

def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError, AttributeError):
        return False

def to_valid_uuid(val: Any) -> str:
    if not val:
        return str(uuid.uuid4())
    s = str(val).strip()
    try:
        return str(uuid.UUID(s))
    except (ValueError, TypeError, AttributeError):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))

# Pydantic schemas
class CanvasCreate(BaseModel):
    workspace_id: Optional[str] = None
    title: Optional[str] = None
    name: Optional[str] = None  # fallback for legacy client
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SnapshotCreate(BaseModel):
    version: int
    elements: List[Dict[str, Any]]
    app_state: Optional[Dict[str, Any]] = None
    files: Optional[Dict[str, Any]] = None
    client_request_id: str

class SceneSave(BaseModel):
    expected_revision: int
    scene_json: Dict[str, Any]
    scene_checksum: str
    change_summary: Optional[str] = None

class ForceCommit(BaseModel):
    override_reason: str
    parent_revision_number: int
    scene_json: Dict[str, Any]
    scene_checksum: str
    approval_id: Optional[str] = None

class RevisionMilestone(BaseModel):
    change_summary: str


class CanvasDeltaSyncRequest(BaseModel):
    upsert_nodes: Optional[List[Dict[str, Any]]] = None
    delete_node_ids: Optional[List[str]] = None
    upsert_edges: Optional[List[Dict[str, Any]]] = None
    delete_edge_ids: Optional[List[str]] = None
    sketches: Optional[List[Dict[str, Any]]] = None
    viewport: Optional[Dict[str, Any]] = None
    client_revision: Optional[int] = None
    change_summary: Optional[str] = "Delta sync update"
    actor_id: Optional[str] = "system"
    workspace_id: Optional[str] = "ws-alpha-001"


class PresignAssetRequest(BaseModel):
    sha256: str
    mime_type: str
    byte_size: int
    filename: Optional[str] = None
    element_id: Optional[str] = None

class CommitAssetRequest(BaseModel):
    uploaded_byte_size: Optional[int] = None
    element_id: Optional[str] = None

class LinkCreate(BaseModel):
    element_id: Optional[str] = None
    entity_type: str
    entity_id: str
    relation_type: Optional[str] = "references"

class ApprovalPayload(BaseModel):
    expected_artifact_version: int
    expected_canvas_revision: int
    approval_note: str
    idempotency_key: str

class DesignRunCreate(BaseModel):
    canvas_id: str
    command: str
    payload: Dict[str, Any]
    idempotency_key: Optional[str] = None


# Helper functions
def publish_event(topic: str, payload: dict):
    payload_str = json.dumps(payload)
    if r_client:
        try:
            r_client.publish(topic, payload_str)
            logger.info(f"Published to Redis channel '{topic}': {payload_str}")
        except Exception as e:
            logger.warning(f"Failed to publish to Redis: {e}")

def audit_event(db, run_id: str, canvas_id: str, event_type: str, from_state: Optional[str], to_state: str, details: str):
    evt = ActivityEvent(
        id=str(uuid4()),
        run_id=run_id,
        canvas_id=canvas_id,
        event_type=event_type,
        from_state=from_state,
        to_state=to_state,
        details=details,
        created_at=int(time.time() * 1000)
    )
    db.add(evt)
    db.commit()
    publish_event("canvas.audit", {
        "id": evt.id,
        "runId": run_id,
        "canvasId": canvas_id,
        "eventType": event_type,
        "fromState": from_state,
        "toState": to_state,
        "timestamp": evt.created_at
    })

def transition_run(db, run: DesignRun, to_state: str, error_msg: Optional[str] = None, artifact_id: Optional[str] = None):
    from_state = run.status
    if from_state == to_state:
        return

    run.status = to_state
    run.error_message = error_msg
    run.artifact_id = artifact_id or run.artifact_id
    run.updated_at = int(time.time() * 1000)
    db.commit()

    logger.info(f"[FastAPI State Machine] Run {run.id} transitioned: {from_state} ➔ {to_state}")

    # Audit log
    audit_event(db, run.id, run.canvas_id, "state_transition", from_state, to_state, error_msg or f"Transition to {to_state}")

    # Publish Redis status event
    publish_event("canvas.run_status", {
        "runId": run.id,
        "canvasId": run.canvas_id,
        "fromState": from_state,
        "toState": to_state,
        "artifactId": run.artifact_id,
        "errorMsg": error_msg,
        "timestamp": run.updated_at
    })

# Background fixture task worker
def run_fixture_worker(run_id: str):
    time.sleep(1.0)
    db = SessionLocal()
    try:
        run = db.query(DesignRun).filter(DesignRun.id == run_id).first()
        if not run or run.status != "queued":
            return

        # queued ➔ running
        transition_run(db, run, "running")

        time.sleep(2.0)
        # Re-fetch in case of cancellation
        db.refresh(run)
        if run.status != "running":
            return

        artifact_id = str(uuid4())
        # Workspace design elements fixture
        artifact_content = {
            "elements": [
                {
                  "id": "rect_gen_1",
                  "type": "rectangle",
                  "x": 350,
                  "y": 180,
                  "width": 250,
                  "height": 140,
                  "backgroundColor": "#0f172a",
                  "strokeColor": "#6366f1",
                },
                {
                  "id": "text_gen_1",
                  "type": "text",
                  "x": 380,
                  "y": 220,
                  "text": "Orchestrated Workspace Sketch",
                  "fontSize": 14,
                  "color": "#ffffff",
                }
            ],
            "app_state": {},
            "files": {}
        }

        # Create artifact
        art = Artifact(
            id=artifact_id,
            canvas_id=run.canvas_id,
            name="Generated Canvas Artifact",
            type="excalidraw_scene",
            content_json=json.dumps(artifact_content),
            created_at=int(time.time() * 1000)
        )
        db.add(art)

        # Update Canvas snapshot
        canvas = db.query(Canvas).filter(Canvas.id == run.canvas_id).first()
        if canvas:
            next_version = canvas.version + 1
            snap = CanvasSnapshot(
                id=str(uuid4()),
                canvas_id=canvas.id,
                version=next_version,
                elements_json=json.dumps(artifact_content["elements"]),
                app_state_json="{}",
                files_json="{}",
                client_request_id=str(uuid4()),
                created_at=int(time.time() * 1000)
            )
            db.add(snap)
            canvas.version = next_version
            canvas.updated_at = int(time.time() * 1000)

        # Update new CanvasDocument revision
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == run.canvas_id).first()
        if doc:
            scene_json = {
                "type": "excalidraw",
                "elements": artifact_content["elements"],
                "app_state": {},
                "files": {}
            }
            scene_str = json.dumps(scene_json, sort_keys=True)
            checksum = hashlib.sha256(scene_str.encode('utf-8')).hexdigest()

            new_rev = CanvasRevision(
                id=str(uuid4()),
                document_id=doc.id,
                revision_number=canvas.version if canvas else 1,
                scene_json=scene_json,
                scene_checksum=checksum,
                created_by="agent",
                change_summary="Orchestrated Workspace Sketch generated by run_fixture_worker",
                parent_revision_id=doc.current_revision_id
            )
            db.add(new_rev)
            db.flush()
            doc.current_revision_id = new_rev.id
            doc.updated_at = datetime.now(timezone.utc)

        transition_run(db, run, "completed", artifact_id=artifact_id)
    except Exception as e:
        logger.error(f"[FastAPI Worker Error]: {e}")
        db.rollback()
    finally:
        db.close()



# Secure workspace authorization dependency
def get_current_workspace_id(
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-Id"),
    authorization: Optional[str] = Header(None)
) -> str:
    raw_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if ":" in token:
            user, workspace = token.split(":", 1)
            raw_id = workspace
        elif len(token) > 10:
            raw_id = token
    elif x_workspace_id:
        raw_id = x_workspace_id

    if not raw_id:
        raise HTTPException(status_code=401, detail="Workspace identity context missing. Set X-Workspace-Id or Authorization header.")
    return to_valid_uuid(raw_id)

# --- API Routes ---

@app.post("/api/v1/canvases", status_code=201)
def create_canvas(payload: CanvasCreate, workspace_id: str = Depends(get_current_workspace_id)):
    db = SessionLocal()
    try:
        canvas_id = str(uuid4())
        title = payload.title or payload.name or "Untitled Canvas"
        w_id = to_valid_uuid(payload.workspace_id) if payload.workspace_id else workspace_id

        # Create in hub_memory schema
        doc = CanvasDocument(
            id=canvas_id,
            workspace_id=w_id,
            title=title,
            description=payload.description,
            created_by="user-uuid-1234",
            canvas_metadata=payload.metadata or {}
        )
        db.add(doc)

        # Create in legacy public schema for backward compatibility
        legacy_canvas = Canvas(
            id=canvas_id,
            name=title,
            version=0,
            status="active"
        )
        db.add(legacy_canvas)

        db.commit()

        return {
            "id": doc.id,
            "workspace_id": doc.workspace_id,
            "title": doc.title,
            "description": doc.description,
            "document_type": doc.document_type,
            "current_revision_id": doc.current_revision_id,
            "created_by": doc.created_by,
            "created_at": doc.created_at.isoformat() if hasattr(doc.created_at, "isoformat") else str(doc.created_at),
            "updated_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else str(doc.updated_at),
            "status": doc.status,
            "metadata": doc.canvas_metadata,
            "version": 0
        }
    finally:
        db.close()

@app.get("/api/v1/canvases")
def list_canvases(limit: int = 20, offset: int = 0, workspace_id: str = Depends(get_current_workspace_id)):
    db = SessionLocal()
    try:
        query = db.query(CanvasDocument).filter(CanvasDocument.workspace_id == workspace_id)
        total = query.count()
        items = query.offset(offset).limit(limit).all()

        result_items = []
        for doc in items:
            result_items.append({
                "id": doc.id,
                "title": doc.title,
                "status": doc.status,
                "created_at": doc.created_at.isoformat() if hasattr(doc.created_at, "isoformat") else str(doc.created_at)
            })

        return {
            "total": total,
            "items": result_items
        }
    finally:
        db.close()

@app.get("/api/v1/canvases/{canvas_id}")
def get_canvas(canvas_id: str, workspace_id: str = Depends(get_current_workspace_id)):
    c_uuid = to_valid_uuid(canvas_id)
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == c_uuid).first()
        if not doc:
            if canvas_id in ("default-canvas", "default-canvas-id"):
                doc = CanvasDocument(
                    id=c_uuid,
                    workspace_id=workspace_id,
                    title="Default Workspace Canvas",
                    description="Auto-provisioned default canvas",
                    document_type="excalidraw",
                    created_by="system",
                    canvas_metadata={"source": "auto_default"}
                )
                db.add(doc)
                legacy_canvas = Canvas(
                    id=c_uuid,
                    name="Default Workspace Canvas",
                    version=0,
                    status="active"
                )
                db.add(legacy_canvas)
                db.commit()
                db.refresh(doc)
            else:
                raise HTTPException(status_code=404, detail="Canvas not found")
        if doc.workspace_id != workspace_id and canvas_id not in ("default-canvas", "default-canvas-id"):
            raise HTTPException(status_code=403, detail="Not authorized to access this canvas")

        # Fetch current revision elements if current_revision_id exists
        scene_json = None
        current_revision_number = 0
        if doc.current_revision_id:
            rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()
            if rev:
                scene_json = rev.scene_json
                current_revision_number = rev.revision_number

        if scene_json is None:
            # default empty scene
            scene_json = { "type": "excalidraw", "elements": [] }

        return {
            "id": doc.id,
            "workspace_id": doc.workspace_id,
            "title": doc.title,
            "description": doc.description,
            "document_type": doc.document_type,
            "current_revision_id": doc.current_revision_id,
            "current_revision_number": current_revision_number,
            "version": current_revision_number,
            "status": doc.status,
            "updated_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else str(doc.updated_at),
            "scene_json": scene_json,
            "metadata": doc.canvas_metadata
        }
    finally:
        db.close()

@app.post("/api/v1/canvases/{canvas_id}/snapshots")
def save_snapshot(canvas_id: str, payload: SnapshotCreate):
    c_uuid = to_valid_uuid(canvas_id)
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == c_uuid).with_for_update().first()
        if not doc:
            if canvas_id in ("default-canvas", "default-canvas-id"):
                doc = CanvasDocument(
                    id=c_uuid,
                    workspace_id=to_valid_uuid("ws-alpha-001"),
                    title="Default Workspace Canvas",
                    description="Auto-provisioned default canvas",
                    document_type="excalidraw",
                    created_by="system",
                    canvas_metadata={"source": "auto_default"}
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
            else:
                raise HTTPException(status_code=404, detail="Canvas not found")

        # Concurrency check
        current_version = 0
        if doc.current_revision_id:
            rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()
            if rev:
                current_version = rev.revision_number

        expected_version = current_version + 1
        if payload.version != expected_version:
            raise HTTPException(status_code=409, detail=f"CONFLICT: Expected version {expected_version}, got {payload.version}")

        # Check idempotency via client_request_id
        dup = db.query(CanvasRevision).filter(
            CanvasRevision.document_id == canvas_id,
            CanvasRevision.change_summary == f"client_request_id:{payload.client_request_id}"
        ).first()
        if dup:
            return {"success": True, "version": current_version, "idempotency_hit": True}

        # Build unified scene_json
        scene_json = {
            "type": "excalidraw",
            "elements": payload.elements,
            "app_state": payload.app_state or {},
            "files": payload.files or {}
        }

        # Serialize and hash scene_json
        scene_str = json.dumps(scene_json, sort_keys=True)
        checksum = hashlib.sha256(scene_str.encode('utf-8')).hexdigest()

        # Save as a CanvasRevision in hub_memory
        new_rev = CanvasRevision(
            id=str(uuid4()),
            document_id=canvas_id,
            revision_number=payload.version,
            scene_json=scene_json,
            scene_checksum=checksum,
            created_by="user-uuid-1234",
            change_summary=f"client_request_id:{payload.client_request_id}",
            parent_revision_id=doc.current_revision_id
        )
        db.add(new_rev)
        db.flush()

        # Update document current revision
        doc.current_revision_id = new_rev.id
        doc.updated_at = datetime.now(timezone.utc)

        # Also sync to legacy public.canvases table for any legacy dependency
        legacy_canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
        if legacy_canvas:
            legacy_canvas.version = payload.version
            legacy_canvas.updated_at = int(time.time() * 1000)

            # Sync to public.canvas_snapshots as well
            snap = CanvasSnapshot(
                id=str(uuid4()),
                canvas_id=canvas_id,
                version=payload.version,
                elements_json=json.dumps(payload.elements),
                app_state_json=json.dumps(payload.app_state or {}),
                files_json=json.dumps(payload.files or {}),
                client_request_id=payload.client_request_id,
                created_at=int(time.time() * 1000)
            )
            db.add(snap)

        db.commit()
        return {"success": True, "version": payload.version}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "error": "REVISION_CONFLICT",
                "message": "The canvas has been modified by another actor. Stale revision provided.",
                "client_revision": payload.version,
                "server_revision": current_version + 1,
                "modified_by": "another actor",
                "modified_at": str(datetime.now(timezone.utc))
            }
        )
    finally:
        db.close()

@app.get("/api/v1/canvases/{canvas_id}/snapshots/latest")
def get_latest_snapshot(canvas_id: str):
    c_uuid = to_valid_uuid(canvas_id)
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == c_uuid).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas not found")

        if not doc.current_revision_id:
            raise HTTPException(status_code=404, detail="No snapshots found")

        rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()
        if not rev:
            raise HTTPException(status_code=404, detail="No snapshots found")

        scene = rev.scene_json
        elements = scene.get("elements", [])
        app_state = scene.get("app_state", {})
        files = scene.get("files", {})

        client_request_id = "req-1"
        if rev.change_summary and rev.change_summary.startswith("client_request_id:"):
            client_request_id = rev.change_summary.split(":", 1)[1]

        return {
            "version": rev.revision_number,
            "elements": elements,
            "app_state": app_state,
            "files": files,
            "client_request_id": client_request_id
        }
    finally:
        db.close()

@app.put("/api/v1/canvases/{canvas_id}/scene")
def save_scene(canvas_id: str, payload: SceneSave, workspace_id: str = Depends(get_current_workspace_id)):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).with_for_update().first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas not found")
        if doc.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this canvas")

        current_version = 0
        if doc.current_revision_id:
            rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()
            if rev:
                current_version = rev.revision_number

        if payload.expected_revision != current_version:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "REVISION_CONFLICT",
                    "message": f"The canvas has been modified by another actor. Stale revision provided. Expected {current_version}, got {payload.expected_revision}",
                    "client_revision": payload.expected_revision,
                    "server_revision": current_version,
                    "modified_by": doc.created_by,
                    "modified_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else str(doc.updated_at)
                }
            )

        # Server-side validation of SHA-256 checksum with stable canonical sorting
        
        # Base64 inspection to prevent large image embeddings in scene JSON
        elements_str = json.dumps(payload.scene_json.get("elements", []))
        if "data:image/" in elements_str and ";base64," in elements_str:
            raise HTTPException(
                status_code=400,
                detail="Base64 embedded images are not allowed inside scene JSON. Use S3 asset upload API instead."
            )

        scene_str = json.dumps(payload.scene_json, sort_keys=True, separators=(',', ':'))
        computed_checksum = hashlib.sha256(scene_str.encode('utf-8')).hexdigest()

        if computed_checksum != payload.scene_checksum:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "CHECKSUM_MISMATCH",
                    "message": f"Integrity check failed. Computed checksum {computed_checksum} does not match provided checksum {payload.scene_checksum}."
                }
            )

        new_rev = CanvasRevision(
            id=str(uuid4()),
            document_id=canvas_id,
            revision_number=current_version + 1,
            scene_json=payload.scene_json,
            scene_checksum=payload.scene_checksum,
            created_by="user-uuid-1234",
            change_summary=payload.change_summary or "Updated scene",
            parent_revision_id=doc.current_revision_id
        )
        db.add(new_rev)
        db.flush()

        doc.current_revision_id = new_rev.id
        doc.updated_at = datetime.now(timezone.utc)

        # Also sync to legacy public schema
        legacy_canvas = db.query(Canvas).filter(Canvas.id == canvas_id).first()
        if legacy_canvas:
            legacy_canvas.version = current_version + 1
            legacy_canvas.updated_at = int(time.time() * 1000)

            elements = payload.scene_json.get("elements", [])
            app_state = payload.scene_json.get("app_state", {})
            files = payload.scene_json.get("files", {})

            snap = CanvasSnapshot(
                id=str(uuid4()),
                canvas_id=canvas_id,
                version=current_version + 1,
                elements_json=json.dumps(elements),
                app_state_json=json.dumps(app_state),
                files_json=json.dumps(files),
                client_request_id=str(uuid4()),
                created_at=int(time.time() * 1000)
              )
            db.add(snap)

        db.commit()

        return {
            "status": "success",
            "new_revision_id": new_rev.id,
            "new_revision_number": new_rev.revision_number,
            "updated_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else str(doc.updated_at)
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "error": "REVISION_CONFLICT",
                "message": "The canvas has been modified by another actor. Stale revision provided.",
                "client_revision": payload.expected_revision,
                "server_revision": current_version + 1,
                "modified_by": "another actor",
                "modified_at": str(datetime.now(timezone.utc))
            }
        )
    finally:
        db.close()

def compute_canonical_payload_hash(data: dict) -> str:
    # Recursively sort keys for canonical JSON serialization
    def canonicalize(obj: Any) -> Any:
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, list):
            return [canonicalize(item) for item in obj]
        if isinstance(obj, dict):
            return {k: canonicalize(obj[k]) for k in sorted(obj.keys())}
        return obj

    canonical_data = canonicalize(data)
    payload_str = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()


@app.post("/api/v1/canvases/{canvas_id}/force-commit")
def force_commit_scene(canvas_id: str, payload: ForceCommit, response: Response, workspace_id: str = Depends(get_current_workspace_id)):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).with_for_update().first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas not found")
        if doc.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this canvas")

        # Server-side validation of SHA-256 checksum with stable canonical sorting
        
        # Base64 inspection to prevent large image embeddings in scene JSON
        elements_str = json.dumps(payload.scene_json.get("elements", []))
        if "data:image/" in elements_str and ";base64," in elements_str:
            raise HTTPException(
                status_code=400,
                detail="Base64 embedded images are not allowed inside scene JSON. Use S3 asset upload API instead."
            )

        scene_str = json.dumps(payload.scene_json, sort_keys=True, separators=(',', ':'))
        computed_checksum = hashlib.sha256(scene_str.encode('utf-8')).hexdigest()

        if computed_checksum != payload.scene_checksum:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "CHECKSUM_MISMATCH",
                    "message": f"Integrity check failed. Computed checksum {computed_checksum} does not match provided checksum {payload.scene_checksum}."
                }
            )

        # Force-Commit Gate Enforcement
        if not payload.approval_id:
            # Create pending approval request with FULL secure binding!
            app_id = str(uuid4())
            sv_run_id = str(uuid4())

            # Insert SupervisorRun for foreign key constraint safety
            sv_run = SupervisorRun(
                id=sv_run_id,
                design_run_id=str(uuid4()),
                workflow_id="force_commit_flow",
                status="pending"
            )
            db.add(sv_run)
            db.flush()

            # Secure parameters arguments_hash binding of the canonical payload
            args_hash = compute_canonical_payload_hash({
                "action_name": "canvas.force_commit",
                "canvas_id": canvas_id,
                "workspace_id": workspace_id,
                "actor_id": "Supervisor-Maksym",
                "override_reason": payload.override_reason,
                "parent_revision_number": payload.parent_revision_number,
                "scene_json": payload.scene_json,
            })

            proposed_action = {
                "canvas_id": canvas_id,
                "workspace_id": workspace_id,
                "action_name": "canvas.force_commit",
                "actor_id": "Supervisor-Maksym",
                "arguments_hash": args_hash,
                "scene_checksum": payload.scene_checksum,
                "parent_revision_number": payload.parent_revision_number,
                "override_reason": payload.override_reason,
                "scene_json": payload.scene_json
            }

            app_req = ApprovalRequest(
                id=app_id,
                supervisor_run_id=sv_run_id,
                approval_type="canvas.force_commit",
                risk_level="L2",
                proposed_action_json=proposed_action,
                status="pending"
            )
            db.add(app_req)
            db.commit()

            response.status_code = 202
            return {
                "status": "pending_approval",
                "message": "Force-commit requires Supervisor Gate approval. Approval request registered.",
                "approval_id": app_id
            }

        # Verify approval_id with row-level transaction locking
        app_req = db.query(ApprovalRequest).filter(ApprovalRequest.id == payload.approval_id).with_for_update().first()
        if not app_req:
            raise HTTPException(status_code=403, detail="Supervisor Gate has not registered any approval request with this ID")

        # Approval consumption check
        if app_req.status == "consumed":
            raise HTTPException(status_code=403, detail="APPROVAL_ALREADY_CONSUMED")

        if app_req.status != "approved":
            raise HTTPException(status_code=403, detail=f"Supervisor Gate has not approved this request yet. Current status: {app_req.status}")

        # Re-verify full binding parameters to prevent replay attacks, arguments tampering, or cross-canvas reutilization!
        saved_action = app_req.proposed_action_json

        if saved_action.get("canvas_id") != canvas_id:
            raise HTTPException(status_code=403, detail="Approval binding violation: canvas_id mismatch.")

        if saved_action.get("workspace_id") != workspace_id:
            raise HTTPException(status_code=403, detail="Approval binding violation: workspace_id mismatch.")

        if saved_action.get("action_name") != "canvas.force_commit":
            raise HTTPException(status_code=403, detail="Approval binding violation: action_name mismatch.")

        if saved_action.get("scene_checksum") != payload.scene_checksum:
            raise HTTPException(status_code=403, detail="Approval binding violation: scene_checksum mismatch.")

        if saved_action.get("parent_revision_number") != payload.parent_revision_number:
            raise HTTPException(status_code=403, detail="Approval binding violation: parent_revision_number mismatch.")

        # Re-verify full canonical arguments_hash
        computed_args_hash = compute_canonical_payload_hash({
            "action_name": "canvas.force_commit",
            "canvas_id": canvas_id,
            "workspace_id": workspace_id,
            "actor_id": "Supervisor-Maksym",
            "override_reason": payload.override_reason,
            "parent_revision_number": payload.parent_revision_number,
            "scene_json": payload.scene_json,
        })
        if saved_action.get("arguments_hash") != computed_args_hash:
            raise HTTPException(status_code=403, detail="Approval binding violation: arguments_hash mismatch.")

        # Gate approved! Execute force commit
        new_rev = CanvasRevision(
            id=str(uuid4()),
            document_id=canvas_id,
            revision_number=payload.parent_revision_number + 1,
            scene_json=payload.scene_json,
            scene_checksum=payload.scene_checksum,
            created_by="Supervisor-Maksym",
            change_summary=f"FORCE_COMMIT: {payload.override_reason}",
            parent_revision_id=doc.current_revision_id
        )
        db.add(new_rev)
        db.flush()

        doc.current_revision_id = new_rev.id
        doc.updated_at = datetime.now(timezone.utc)

        # Audit event
        audit = CanvasAuditEvent(
            id=str(uuid4()),
            document_id=canvas_id,
            actor_type="agent",
            actor_id="Supervisor-Maksym",
            event_type="force_commit",
            revision_id=new_rev.id,
            payload={"override_reason": payload.override_reason, "approval_id": payload.approval_id}
        )
        db.add(audit)
        db.flush()

        # One-time approval consumption inside the atomic row locking transaction
        app_req.status = "consumed"
        db.flush()

        db.commit()

        return {
            "status": "success",
            "new_revision_id": new_rev.id,
            "new_revision_number": new_rev.revision_number,
            "updated_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else str(doc.updated_at)
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=403, detail="APPROVAL_ALREADY_CONSUMED")
    finally:
        db.close()

@app.get("/api/v1/canvases/{canvas_id}/revisions")
def list_revisions(canvas_id: str):
    db = SessionLocal()
    try:
        revs = db.query(CanvasRevision).filter(CanvasRevision.document_id == canvas_id).order_by(CanvasRevision.revision_number.desc()).all()
        items = []
        for r in revs:
            items.append({
                "id": r.id,
                "revision_number": r.revision_number,
                "change_summary": r.change_summary,
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at)
            })
        return {"revisions": items}
    finally:
        db.close()

@app.get("/api/v1/canvases/{canvas_id}/revisions/{revision_id}")
def get_revision_details(canvas_id: str, revision_id: str):
    db = SessionLocal()
    try:
        r = db.query(CanvasRevision).filter(CanvasRevision.id == revision_id, CanvasRevision.document_id == canvas_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Revision not found")
        return {
            "id": r.id,
            "revision_number": r.revision_number,
            "scene_json": r.scene_json,
            "scene_checksum": r.scene_checksum,
            "change_summary": r.change_summary,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at)
        }
    finally:
        db.close()

@app.post("/api/v1/canvases/{canvas_id}/revisions")
def create_revision_milestone(canvas_id: str, payload: RevisionMilestone):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas not found")

        if not doc.current_revision_id:
            raise HTTPException(status_code=400, detail="Cannot create milestone for canvas with no scene")

        current_rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()
        if not current_rev:
            raise HTTPException(status_code=400, detail="Current revision not found")

        new_rev = CanvasRevision(
            id=str(uuid4()),
            document_id=canvas_id,
            revision_number=current_rev.revision_number + 1,
            scene_json=current_rev.scene_json,
            scene_checksum=current_rev.scene_checksum,
            created_by="user-uuid-1234",
            change_summary=f"Milestone: {payload.change_summary}",
            parent_revision_id=current_rev.id
        )
        db.add(new_rev)
        db.flush()

        doc.current_revision_id = new_rev.id
        doc.updated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "revision_id": new_rev.id,
            "revision_number": new_rev.revision_number,
            "change_summary": new_rev.change_summary,
            "created_at": doc.updated_at.isoformat() if hasattr(doc.updated_at, "isoformat") else str(doc.updated_at)
        }
    finally:
        db.close()


class CanvasCollabManager:
    """Manages multi-user real-time WebSocket collaboration per canvas."""
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, canvas_id: str, websocket: WebSocket):
        await websocket.accept()
        if canvas_id not in self.active_connections:
            self.active_connections[canvas_id] = set()
        self.active_connections[canvas_id].add(websocket)

    def disconnect(self, canvas_id: str, websocket: WebSocket):
        if canvas_id in self.active_connections:
            self.active_connections[canvas_id].discard(websocket)
            if not self.active_connections[canvas_id]:
                del self.active_connections[canvas_id]

    async def broadcast(self, canvas_id: str, message: Dict[str, Any], sender: Optional[WebSocket] = None):
        if canvas_id not in self.active_connections:
            return
        dead = []
        for ws in list(self.active_connections[canvas_id]):
            if ws != sender:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.append(ws)
        for d in dead:
            self.disconnect(canvas_id, d)


canvas_collab_manager = CanvasCollabManager()


@app.post("/api/v1/canvases/{canvas_id}/delta")
@app.post("/api/v1/canvases/{canvas_id}/sync")
async def sync_canvas_delta(
    canvas_id: str,
    payload: CanvasDeltaSyncRequest,
    background_tasks: BackgroundTasks
):
    """
    Delta sync endpoint: applies incremental nodes/edges/sketches mutations
    to PostgreSQL 16 (hub_memory schema) and broadcasts to active collaborators.
    """
    db = SessionLocal()
    try:
        from services.dnk_canvas_api.crud import apply_delta_sync
        result = apply_delta_sync(
            db,
            canvas_id=canvas_id,
            delta=payload.dict(exclude_unset=True),
            actor_id=payload.actor_id or "system",
            workspace_id=payload.workspace_id or "ws-alpha-001"
        )
    finally:
        db.close()

    # Broadcast delta to connected WebSocket clients in background
    background_tasks.add_task(
        canvas_collab_manager.broadcast,
        canvas_id,
        {
            "type": "canvas_delta",
            "delta": result,
            "actor_id": payload.actor_id or "system"
        }
    )
    return result


@app.post("/api/v1/canvases/{canvas_id}/revisions/{revision_id}/restore")
def restore_canvas_revision_endpoint(
    canvas_id: str,
    revision_id: str,
    actor_id: Optional[str] = Header("system", alias="X-Actor-Id"),
    workspace_id: str = Depends(get_current_workspace_id)
):
    """
    Restore a past revision in PostgreSQL hub_memory. Enables undo beyond session.
    """
    db = SessionLocal()
    try:
        from services.dnk_canvas_api.crud import restore_revision
        result = restore_revision(
            db,
            canvas_id=canvas_id,
            revision_id=revision_id,
            actor_id=actor_id or "system",
            workspace_id=workspace_id or "ws-alpha-001"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    finally:
        db.close()


@app.websocket("/api/v1/ws/canvas/{canvas_id}")
async def websocket_canvas(websocket: WebSocket, canvas_id: str):
    """
    Real-time collaboration WebSocket endpoint for Canvas.
    Supports presence, cursor tracking, and live delta synchronization.
    """
    await canvas_collab_manager.connect(canvas_id, websocket)
    try:
        await websocket.send_json({
            "type": "connection_ack",
            "canvas_id": canvas_id,
            "status": "connected"
        })
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "unknown")
            if msg_type == "delta_sync":
                delta_payload = data.get("delta", {})
                actor_id = data.get("actor_id", "websocket_client")
                db = SessionLocal()
                try:
                    from services.dnk_canvas_api.crud import apply_delta_sync
                    result = apply_delta_sync(
                        db,
                        canvas_id=canvas_id,
                        delta=delta_payload,
                        actor_id=actor_id
                    )
                finally:
                    db.close()
                await canvas_collab_manager.broadcast(canvas_id, {
                    "type": "canvas_delta",
                    "delta": result,
                    "actor_id": actor_id
                }, sender=websocket)
                await websocket.send_json({
                    "type": "delta_ack",
                    "revision_number": result.get("revision_number"),
                    "revision_id": result.get("revision_id")
                })
            elif msg_type == "cursor_move":
                await canvas_collab_manager.broadcast(canvas_id, {
                    "type": "cursor_update",
                    "actor_id": data.get("actor_id", "unknown"),
                    "cursor": data.get("cursor", {}),
                    "user_name": data.get("user_name", "Anonymous")
                }, sender=websocket)
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        canvas_collab_manager.disconnect(canvas_id, websocket)
    except Exception:
        canvas_collab_manager.disconnect(canvas_id, websocket)


@app.post("/api/v1/canvases/{canvas_id}/links")
def create_canvas_link(
    canvas_id: str,
    payload: LinkCreate,
    workspace_id: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header("human", alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header("user-1", alias="X-Actor-Id")
):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
        if not doc:
            legacy_c = db.query(Canvas).filter(Canvas.id == canvas_id).first()
            if not legacy_c:
                raise HTTPException(status_code=404, detail="Canvas not found")
        elif doc.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this canvas")

        rel_type = payload.relation_type or "references"
        existing = db.query(CanvasLink).filter(
            CanvasLink.document_id == canvas_id,
            CanvasLink.element_id == payload.element_id,
            CanvasLink.entity_type == payload.entity_type,
            CanvasLink.entity_id == payload.entity_id,
            CanvasLink.relation_type == rel_type
        ).first()

        if existing:
            return {
                "link_id": existing.id,
                "canvas_id": canvas_id,
                "element_id": existing.element_id,
                "entity_type": existing.entity_type,
                "entity_id": existing.entity_id,
                "relation_type": existing.relation_type,
                "created_at": existing.created_at.isoformat() if hasattr(existing.created_at, "isoformat") else str(existing.created_at),
                "already_exists": True
            }

        link = CanvasLink(
            id=str(uuid4()),
            document_id=canvas_id,
            element_id=payload.element_id,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            relation_type=rel_type
        )
        db.add(link)

        evt = CanvasAuditEvent(
            id=str(uuid4()),
            document_id=canvas_id,
            actor_type=x_actor_type or "human",
            actor_id=x_actor_id or "user-1",
            event_type="link_created",
            payload={
                "link_id": link.id,
                "element_id": payload.element_id,
                "entity_type": payload.entity_type,
                "entity_id": payload.entity_id,
                "relation_type": rel_type
            }
        )
        db.add(evt)
        db.commit()
        db.refresh(link)

        return {
            "link_id": link.id,
            "canvas_id": canvas_id,
            "element_id": link.element_id,
            "entity_type": link.entity_type,
            "entity_id": link.entity_id,
            "relation_type": link.relation_type,
            "created_at": link.created_at.isoformat() if hasattr(link.created_at, "isoformat") else str(link.created_at)
        }
    finally:
        db.close()

@app.delete("/api/v1/canvases/{canvas_id}/links/{link_id}")
def remove_canvas_link(
    canvas_id: str,
    link_id: str,
    workspace_id: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header("human", alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header("user-1", alias="X-Actor-Id"),
    x_approval_id: Optional[str] = Header(None, alias="X-Approval-Id")
):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
        if doc and doc.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this canvas")

        link = db.query(CanvasLink).filter(CanvasLink.id == link_id, CanvasLink.document_id == canvas_id).first()
        if not link:
            return {
                "status": "deleted",
                "link_id": link_id,
                "message": "Entity link removed successfully (idempotent)."
            }

        actor_type = (x_actor_type or "human").lower()
        if actor_type == "agent":
            if x_approval_id:
                app_req = db.query(ApprovalRequest).filter(ApprovalRequest.id == x_approval_id).first()
                if app_req and app_req.status == "approved":
                    db.delete(link)
                    evt = CanvasAuditEvent(
                        id=str(uuid4()),
                        document_id=canvas_id,
                        actor_type="agent",
                        actor_id=x_actor_id or "agent-gerych",
                        event_type="link_deleted_approved",
                        payload={"link_id": link_id, "approval_id": x_approval_id}
                    )
                    db.add(evt)
                    db.commit()
                    return {
                        "status": "deleted",
                        "link_id": link_id,
                        "message": "Entity link removed after supervisor approval."
                    }
                elif app_req and app_req.status in ["rejected", "timeout_rejected"]:
                    raise HTTPException(status_code=403, detail="Agent deletion request was rejected by supervisor")
                elif app_req and app_req.status == "pending":
                    return Response(
                        status_code=202,
                        content=json.dumps({
                            "status": "pending_approval",
                            "approval_id": x_approval_id,
                            "binding": {
                                "canvas_id": canvas_id,
                                "link_id": link_id,
                                "workspace_id": workspace_id,
                                "actor_id": x_actor_id or "agent-gerych"
                            }
                        }),
                        media_type="application/json"
                    )

            app_id = str(uuid4())
            s_run_id = str(uuid4())
            s_run = SupervisorRun(
                id=s_run_id,
                design_run_id=str(uuid4()),
                workflow_id="agent_delete_workflow",
                status="pending_approval",
                supervisor_version="1.0.0",
                model_policy="gemma-4"
            )
            db.add(s_run)
            db.flush()

            new_approval = ApprovalRequest(
                id=app_id,
                supervisor_run_id=s_run_id,
                approval_type="agent_delete_link",
                risk_level="L2",
                proposed_action_json={
                    "canvas_id": canvas_id,
                    "link_id": link_id,
                    "workspace_id": workspace_id,
                    "actor_id": x_actor_id or "agent-gerych"
                },
                status="pending",
                requested_by=x_actor_id or "agent-gerych",
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=600)
            )
            db.add(new_approval)
            db.commit()

            return Response(
                status_code=202,
                content=json.dumps({
                    "status": "pending_approval",
                    "approval_id": app_id,
                    "binding": {
                        "canvas_id": canvas_id,
                        "link_id": link_id,
                        "workspace_id": workspace_id,
                        "actor_id": x_actor_id or "agent-gerych"
                    }
                }),
                media_type="application/json"
            )

        db.delete(link)
        evt = CanvasAuditEvent(
            id=str(uuid4()),
            document_id=canvas_id,
            actor_type="human",
            actor_id=x_actor_id or "user-1",
            event_type="link_deleted",
            payload={"link_id": link_id}
        )
        db.add(evt)
        db.commit()
        return {
            "status": "deleted",
            "link_id": link_id,
            "message": "Entity link removed successfully."
        }
    finally:
        db.close()

@app.post("/api/v1/canvases/{canvas_id}/assets/presign")
def presign_asset_upload(
    canvas_id: str,
    payload: PresignAssetRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header("human", alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header("user-1", alias="X-Actor-Id")
):
    allowed_mimes = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif", "image/svg+xml"}
    if payload.mime_type.lower() not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid MIME type '{payload.mime_type}'. Only valid image formats (PNG, JPEG, WebP, GIF, SVG) are permitted."
        )

    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas not found")
        if doc.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this canvas")

        existing_asset = db.query(CanvasAsset).filter(
            CanvasAsset.workspace_id == doc.workspace_id,
            CanvasAsset.sha256 == payload.sha256
        ).first()

        if existing_asset and existing_asset.status == "verified":
            if payload.element_id:
                link = db.query(CanvasAssetLink).filter(
                    CanvasAssetLink.document_id == canvas_id,
                    CanvasAssetLink.element_id == payload.element_id,
                    CanvasAssetLink.asset_id == existing_asset.id
                ).first()
                if not link:
                    new_link = CanvasAssetLink(
                        id=str(uuid4()),
                        asset_id=existing_asset.id,
                        document_id=canvas_id,
                        element_id=payload.element_id,
                        relation_type="screenshot"
                    )
                    db.add(new_link)

            evt = CanvasAuditEvent(
                id=str(uuid4()),
                document_id=canvas_id,
                actor_type=x_actor_type or "human",
                actor_id=x_actor_id or "user-1",
                event_type="asset_deduplicated",
                payload={"asset_id": existing_asset.id, "sha256": payload.sha256}
            )
            db.add(evt)
            db.commit()

            return {
                "asset_id": existing_asset.id,
                "status": "verified",
                "deduplicated": True,
                "storage_key": existing_asset.storage_key,
                "presigned_url": None
            }

        storage_key = f"workspaces/{doc.workspace_id}/assets/{payload.sha256}.bin"
        if existing_asset:
            existing_asset.status = "pending_upload"
            existing_asset.byte_size = payload.byte_size
            existing_asset.mime_type = payload.mime_type
            existing_asset.storage_key = storage_key
            asset = existing_asset
        else:
            asset = CanvasAsset(
                id=str(uuid4()),
                workspace_id=doc.workspace_id,
                storage_key=storage_key,
                sha256=payload.sha256,
                status="pending_upload",
                mime_type=payload.mime_type,
                byte_size=payload.byte_size
            )
            db.add(asset)

        db.commit()
        db.refresh(asset)

        presigned_url = f"https://storage.local/upload/{asset.id}?key={storage_key}"

        return {
            "asset_id": asset.id,
            "presigned_url": presigned_url,
            "status": "pending_upload",
            "deduplicated": False,
            "storage_key": storage_key
        }
    finally:
        db.close()

@app.post("/api/v1/canvases/{canvas_id}/assets/{asset_id}/commit")
def commit_asset_upload(
    canvas_id: str,
    asset_id: str,
    payload: CommitAssetRequest,
    workspace_id: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header("human", alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header("user-1", alias="X-Actor-Id")
):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas not found")
        if doc.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this canvas")

        asset = db.query(CanvasAsset).filter(CanvasAsset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

        if str(asset.workspace_id) != str(doc.workspace_id) or str(asset.workspace_id) != str(workspace_id):
            raise HTTPException(status_code=403, detail="Workspace mismatch for asset commit")

        if asset.status == "verified":
            return {
                "asset_id": asset.id,
                "status": "verified",
                "storage_key": asset.storage_key,
                "already_verified": True
            }

        if payload.uploaded_byte_size is not None and payload.uploaded_byte_size != asset.byte_size:
            asset.status = "rejected"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Byte size mismatch! Expected {asset.byte_size}, received {payload.uploaded_byte_size}."
            )

        asset.status = "verified"
        
        if payload.element_id:
            existing_link = db.query(CanvasAssetLink).filter(
                CanvasAssetLink.document_id == canvas_id,
                CanvasAssetLink.element_id == payload.element_id,
                CanvasAssetLink.asset_id == asset.id
            ).first()
            if not existing_link:
                link = CanvasAssetLink(
                    id=str(uuid4()),
                    asset_id=asset.id,
                    document_id=canvas_id,
                    element_id=payload.element_id,
                    relation_type="screenshot"
                )
                db.add(link)

        evt = CanvasAuditEvent(
            id=str(uuid4()),
            document_id=canvas_id,
            actor_type=x_actor_type or "human",
            actor_id=x_actor_id or "user-1",
            event_type="asset_committed",
            payload={"asset_id": asset.id, "storage_key": asset.storage_key}
        )
        db.add(evt)
        db.commit()

        return {
            "asset_id": asset.id,
            "status": "verified",
            "storage_key": asset.storage_key
        }
    finally:
        db.close()

# --- Design Run routes ---# --- Design Run routes ---

@app.post("/api/v1/design-runs", status_code=201)
def create_design_run(payload: DesignRunCreate, bg_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        if payload.idempotency_key:
            existing = db.query(DesignRun).filter(DesignRun.idempotency_key == payload.idempotency_key).first()
            if existing:
                return existing

        run = DesignRun(
            id=str(uuid4()),
            canvas_id=payload.canvas_id,
            status="queued",
            command=payload.command,
            payload_json=json.dumps(payload.payload),
            idempotency_key=payload.idempotency_key
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # Log audit event
        audit_event(db, run.id, run.canvas_id, "run_created", None, "queued", "Run created in production FastAPI")

        # Determine if we run standard fixture or Supervisor
        is_supervised = (payload.command == "generate_workspace" or payload.payload.get("mode") == "supervised")
        if is_supervised:
            from supervisor.supervisor import DNKSupervisor
            sv = DNKSupervisor(r_client)
            sv_run = sv.create_supervisor_run(db, run.id, payload.canvas_id, payload.payload)
            bg_tasks.add_task(sv.execute_run_workflow, db, sv_run.id)
        else:
            bg_tasks.add_task(run_fixture_worker, run.id)

        return run
    finally:
        db.close()

@app.get("/api/v1/design-runs/{run_id}")
def get_design_run(run_id: str):
    db = SessionLocal()
    try:
        run = db.query(DesignRun).filter(DesignRun.id == run_id).first()
        if not run:
            sv_run = db.query(SupervisorRun).filter(SupervisorRun.id == run_id).first()
            if sv_run:
                run = db.query(DesignRun).filter(DesignRun.id == sv_run.design_run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Design run not found")
        return run
    finally:
        db.close()

@app.get("/api/v1/design-runs/{run_id}/steps")
def get_design_run_steps(run_id: str):
    db = SessionLocal()
    try:
        sv_run = db.query(SupervisorRun).filter(
            (SupervisorRun.design_run_id == run_id) | (SupervisorRun.id == run_id)
        ).first()
        if not sv_run:
            return []
        steps = db.query(AgentStep).filter(AgentStep.supervisor_run_id == sv_run.id).order_by(AgentStep.step_number).all()
        return steps
    finally:
        db.close()

@app.get("/api/v1/design-runs/{run_id}/events")
def get_design_run_events(run_id: str):
    db = SessionLocal()
    try:
        evs = db.query(ActivityEvent).filter(
            (ActivityEvent.run_id == run_id)
        ).order_by(ActivityEvent.created_at).all()
        if not evs:
            sv_run = db.query(SupervisorRun).filter(
                (SupervisorRun.design_run_id == run_id) | (SupervisorRun.id == run_id)
            ).first()
            if sv_run:
                evs = db.query(ActivityEvent).filter(
                    (ActivityEvent.run_id == sv_run.id) | (ActivityEvent.run_id == sv_run.design_run_id)
                ).order_by(ActivityEvent.created_at).all()
        return evs
    finally:
        db.close()

@app.get("/api/v1/design-runs/{run_id}/audit")
def get_design_run_audit(run_id: str):
    return get_design_run_events(run_id)

@app.post("/api/v1/design-runs/{run_id}/cancel")
def cancel_design_run(run_id: str):
    db = SessionLocal()
    try:
        run = db.query(DesignRun).filter(DesignRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Design run not found")
        if run.status in ["completed", "failed"]:
            raise HTTPException(status_code=400, detail="Cannot cancel an already finished run")

        transition_run(db, run, "failed", error_msg="Cancelled by user")

        sv_run = db.query(SupervisorRun).filter(SupervisorRun.design_run_id == run.id).first()
        if sv_run and sv_run.status not in ["completed", "failed"]:
            sv_run.status = "failed"
            sv_run.failure_code = "Cancelled by user"
            sv_run.completed_at = datetime.now(timezone.utc)
            db.commit()

        return {"success": True, "message": "Run cancelled successfully."}
    finally:
        db.close()

@app.post("/api/v1/design-runs/{run_id}/retry")
def retry_design_run(run_id: str, bg_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        run = db.query(DesignRun).filter(DesignRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Design run not found")
        if run.status != "failed":
            raise HTTPException(status_code=400, detail="Can only retry failed runs")

        transition_run(db, run, "queued", error_msg=None)

        sv_run = db.query(SupervisorRun).filter(SupervisorRun.design_run_id == run.id).first()
        if sv_run:
            sv_run.status = "queued"
            sv_run.failure_code = None
            sv_run.completed_at = None
            db.commit()

            from supervisor.supervisor import DNKSupervisor
            sv = DNKSupervisor(r_client)
            bg_tasks.add_task(sv.execute_run_workflow, db, sv_run.id)
        else:
            bg_tasks.add_task(run_fixture_worker, run.id)

        return {"success": True, "message": "Run retry initiated."}
    finally:
        db.close()


@test_router.post("/api/v1/test/approve/{approval_id}")
def test_approve_request(approval_id: str):
    # Strict environment isolation gate (P0)
    is_test = os.getenv("APP_ENV") == "test" and os.getenv("ENV") == "test" and os.getenv("NODE_ENV") != "production"
    if not is_test:
        raise HTTPException(status_code=404, detail="Not Found")

    db = SessionLocal()
    try:
        app_req = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
        if not app_req:
            raise HTTPException(status_code=404, detail="Approval request not found")

        # Verify the saved payload hash during approval/confirmation:
        saved_action = app_req.proposed_action_json
        if saved_action:
            computed_hash = compute_canonical_payload_hash({
                "action_name": saved_action.get("action_name", "canvas.force_commit"),
                "canvas_id": saved_action.get("canvas_id"),
                "workspace_id": saved_action.get("workspace_id"),
                "actor_id": saved_action.get("actor_id", "Supervisor-Maksym"),
                "override_reason": saved_action.get("override_reason"),
                "parent_revision_number": saved_action.get("parent_revision_number"),
                "scene_json": saved_action.get("scene_json"),
            })
            if saved_action.get("arguments_hash") != computed_hash:
                raise HTTPException(status_code=403, detail="Approval binding violation inside test approval: arguments_hash mismatch.")

        app_req.status = "approved"
        db.commit()
        return {"status": "approved", "approval_id": approval_id}
    finally:
        db.close()

@app.get("/api/v1/artifacts/{artifact_id}")
def get_artifact(artifact_id: str):
    db = SessionLocal()
    try:
        art = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        if not art:
            raise HTTPException(status_code=404, detail="Artifact not found")
        return {
            "id": art.id,
            "canvas_id": art.canvas_id,
            "name": art.name,
            "type": art.type,
            "content": json.loads(art.content_json)
        }
    finally:
        db.close()

@app.post("/api/v1/artifacts/{artifact_id}/approve")
def approve_artifact(
    artifact_id: str,
    payload: ApprovalPayload,
    workspace_id: str = Depends(get_current_workspace_id)
):
    db = SessionLocal()
    try:
        # Start transaction with Row Locking
        # 1. Lock artifact and fetch it
        art = db.query(Artifact).filter(Artifact.id == artifact_id).with_for_update().first()
        if not art:
            raise HTTPException(status_code=404, detail="Artifact not found")

        # 2. Lock canvas_document and fetch it
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == art.canvas_id).with_for_update().first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas Document not found")

        # 3. Check Workspace Permission
        if doc.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Forbidden: You do not own workspace access")

        # 4. Idempotency check:
        if art.idempotency_key == payload.idempotency_key:
            if art.status in ["approved", "materializing", "materialized"]:
                current_rev_num = 0
                if doc.current_revision_id:
                    rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()
                    if rev:
                        current_rev_num = rev.revision_number
                return {
                    "status": art.status,
                    "artifact_id": art.id,
                    "canvas_revision": current_rev_num,
                    "idempotency_hit": True
                }

        # Check if the idempotency_key is used by another artifact
        existing_key = db.query(Artifact).filter(
            Artifact.idempotency_key == payload.idempotency_key,
            Artifact.id != art.id
        ).first()
        if existing_key:
            raise HTTPException(status_code=409, detail="Idempotency key already used")

        # 5. Check Artifact state
        if art.status != "shadow_persisted":
            raise HTTPException(status_code=409, detail=f"Artifact is in '{art.status}' state, cannot approve.")

        # 6. Check validation status
        if art.validation_status != "valid":
            raise HTTPException(status_code=422, detail="Artifact validation status is not valid")

        # 7. Check expiration
        now_ms = int(time.time() * 1000)
        if art.expires_at and now_ms > art.expires_at:
            art.status = "expired"
            db.commit()
            raise HTTPException(status_code=400, detail="Artifact has expired")

        # 8. Check Expected Artifact Version Matches
        if art.version != payload.expected_artifact_version:
            raise HTTPException(status_code=409, detail="ARTIFACT_VERSION_CONFLICT")

        # 9. Check Expected Canvas Revision
        current_canvas_rev = 0
        if doc.current_revision_id:
            rev = db.query(CanvasRevision).filter(CanvasRevision.id == doc.current_revision_id).first()
            if rev:
                current_canvas_rev = rev.revision_number

        if current_canvas_rev != payload.expected_canvas_revision:
            raise HTTPException(status_code=409, detail="CANVAS_REVISION_CONFLICT")

        # Transition state
        art.status = "approved"
        art.idempotency_key = payload.idempotency_key
        db.flush()

        # 10. Compile DesignIntent!
        art.status = "materializing"
        db.flush()

        # Parse artifact content
        try:
            artifact_content = json.loads(art.content_json)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to parse artifact JSON: {str(e)}")

        from .compiler.compiler_types import DesignIntent
        from .compiler.design_intent_compiler import DesignIntentCompiler

        try:
            layout_strategy = artifact_content.get("layout", {}).get("strategy", "absolute")

            regions_raw = artifact_content.get("layout", {}).get("regions", [])
            regions = []
            for r in regions_raw:
                regions.append({
                    "id": r.get("id"),
                    "width": r.get("width", 0),
                    "height": r.get("height", 0),
                    "x": r.get("x", 0),
                    "y": r.get("y", 0)
                })

            components_raw = artifact_content.get("components", [])
            components = []
            for c in components_raw:
                components.append({
                    "id": c.get("id"),
                    "type": c.get("type"),
                    "region_id": c.get("region_id"),
                    "title": c.get("title", ""),
                    "properties": c.get("properties", {})
                })

            interactions_raw = artifact_content.get("interactions", [])
            interactions = []
            for i in interactions_raw:
                interactions.append({
                    "id": i.get("id"),
                    "type": i.get("type"),
                    "source_component_id": i.get("source_component_id"),
                    "target_component_id": i.get("target_component_id"),
                    "properties": i.get("properties", {})
                })

            intent = DesignIntent(
                title=artifact_content.get("title", "DNK Canvas"),
                layout_strategy=layout_strategy,
                regions=regions,
                components=components,
                interactions=interactions,
                accessibility_notes=artifact_content.get("accessibility_notes", [])
            )

            compiled = DesignIntentCompiler.compile(intent, art.id)

        except Exception as compile_err:
            art.status = "shadow_persisted"
            db.commit()

            audit_fail = CanvasAuditEvent(
                id=str(uuid4()),
                document_id=art.canvas_id,
                actor_type="agent",
                actor_id="Gerych-Compiler",
                event_type="materialization_failed",
                payload={"error": str(compile_err)}
            )
            db.add(audit_fail)
            db.commit()

            raise HTTPException(
                status_code=422,
                detail=f"Compilation Failed: {str(compile_err)}"
            )

        # 11. Create CanvasRevision and update document
        scene_json = {
            "elements": compiled.elements,
            "appState": compiled.app_state,
            "files": compiled.files
        }

        scene_str = json.dumps(scene_json, sort_keys=True, separators=(',', ':'))
        computed_checksum = hashlib.sha256(scene_str.encode('utf-8')).hexdigest()

        new_rev = CanvasRevision(
            id=str(uuid4()),
            document_id=art.canvas_id,
            revision_number=current_canvas_rev + 1,
            scene_json=scene_json,
            scene_checksum=computed_checksum,
            created_by="Gerych-Compiler",
            change_summary=payload.approval_note or f"Materialized from artifact {art.id}",
            parent_revision_id=doc.current_revision_id
        )
        db.add(new_rev)
        db.flush()

        doc.current_revision_id = new_rev.id
        doc.updated_at = datetime.now(timezone.utc)

        # Mark artifact = materialized
        art.status = "materialized"

        # Record success audit event
        audit_success = CanvasAuditEvent(
            id=str(uuid4()),
            document_id=art.canvas_id,
            actor_type="user",
            actor_id="Maksym",
            event_type="materialization_success",
            revision_id=new_rev.id,
            payload={
                "artifact_id": art.id,
                "compiler_version": compiled.compiler_version,
                "input_hash": compiled.source_hash,
                "output_hash": computed_checksum
            }
        )
        db.add(audit_success)

        # Activity event
        evt = ActivityEvent(
            id=str(uuid4()),
            run_id=str(uuid4()),
            canvas_id=art.canvas_id,
            event_type="materialize",
            from_state="shadow_persisted",
            to_state="materialized",
            details=f"Successfully materialized artifact {art.id}",
            created_at=int(time.time() * 1000)
        )
        db.add(evt)

        db.commit()

        # Publish canvas.revision.created (only after successful commit)
        publish_event("canvas.revision.created", {
            "document_id": art.canvas_id,
            "revision_id": new_rev.id,
            "revision_number": new_rev.revision_number,
            "artifact_id": art.id
        })

        return {
            "status": "materialized",
            "artifact_id": art.id,
            "canvas_revision": new_rev.revision_number,
            "revision_id": new_rev.id
        }

    finally:
        db.close()


@app.post("/api/v1/artifacts/{artifact_id}/reject")
def reject_artifact(
    artifact_id: str,
    workspace_id: str = Depends(get_current_workspace_id)
):
    db = SessionLocal()
    try:
        # Lock artifact and fetch it
        art = db.query(Artifact).filter(Artifact.id == artifact_id).with_for_update().first()
        if not art:
            raise HTTPException(status_code=404, detail="Artifact not found")

        # Fetch CanvasDocument
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == art.canvas_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas Document not found")

        # Check workspace ownership
        if doc.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Forbidden: You do not own workspace access")

        if art.status != "shadow_persisted":
            raise HTTPException(status_code=409, detail=f"Artifact is in '{art.status}' state, cannot reject.")

        art.status = "rejected"
        db.commit()

        return {
            "status": "rejected",
            "artifact_id": art.id
        }
    finally:
        db.close()


@app.get("/api/v1/artifacts/{artifact_id}/validation")
def get_artifact_validation(
    artifact_id: str,
    workspace_id: str = Depends(get_current_workspace_id)
):
    db = SessionLocal()
    try:
        art = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        if not art:
            raise HTTPException(status_code=404, detail="Artifact not found")

        # Check canvas workspace permission
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == art.canvas_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas Document not found")

        if doc.workspace_id != workspace_id:
            raise HTTPException(status_code=403, detail="Forbidden: You do not own workspace access")

        return {
            "status": art.validation_status,
            "errors": [] if art.validation_status == "valid" else ["Validation failed"]
        }
    finally:
        db.close()


# --- CANVAS RUNTIME TRANSPORT & EVENT CLIENT ENDPOINTS (Flower 20) ---

@app.websocket("/api/v1/ws/executions/{execution_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    execution_id: str,
    tenant_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    canvas_id: Optional[str] = None,
    last_event_id: Optional[int] = None
):
    # Fail-closed authentication check
    if not tenant_id or not workspace_id or not canvas_id or not execution_id:
        await websocket.close(code=4003)
        return

    await websocket.accept()

    from core.runtime_events import RuntimeEventBus
    bus = RuntimeEventBus.get_instance()

    try:
        queue = bus.subscribe(
            execution_id=execution_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            last_event_id=last_event_id
        )
    except PermissionError:
        await websocket.close(code=4003)
        return

    async def send_events():
        while True:
            event = await queue.get()
            if isinstance(event, dict) and event.get("event_type") == "snapshot_fallback":
                await websocket.send_json({
                    "type": "snapshot_fallback",
                    "payload": event.get("payload", {})
                })
            else:
                await websocket.send_json({
                    "type": "event",
                    "event": event.model_dump() if hasattr(event, "model_dump") else event
                })
            queue.task_done()

    async def receive_controls():
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            logger.info("WS Control Action Received: %s for execution %s", action, execution_id)
            if action in ["resume", "cancel", "interrupt"]:
                await websocket.send_json({
                    "type": "control_ack",
                    "action": action,
                    "status": "processed"
                })

    try:
        await asyncio.gather(send_events(), receive_controls())
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for execution_id %s", execution_id)
    finally:
        bus.unsubscribe(execution_id, queue)

class ExecutionControlPayload(BaseModel):
    tenant_id: str
    workspace_id: str
    canvas_id: str
    resume_updates: Dict[str, Any] = Field(default_factory=dict)

@app.post("/api/v1/executions/{execution_id}/resume")
def resume_execution(execution_id: str, payload: ExecutionControlPayload):
    if not payload.tenant_id or not payload.workspace_id or not payload.canvas_id:
        raise HTTPException(status_code=403, detail="Fail-Closed: Unauthorized tenant or workspace.")

    from core.runtime_events import RuntimeEventBus, RuntimeEvent
    event = RuntimeEvent(
        tenant_id=payload.tenant_id,
        workspace_id=payload.workspace_id,
        canvas_id=payload.canvas_id,
        graph_id=f"graph_{execution_id}",
        thread_id=execution_id,
        execution_id=execution_id,
        event_type="graph.resumed",
        sequence_number=999,
        payload=payload.resume_updates
    )
    RuntimeEventBus.get_instance().publish(event)
    return {"success": True, "message": "Execution resume requested."}

@app.post("/api/v1/executions/{execution_id}/cancel")
def cancel_execution(execution_id: str, payload: ExecutionControlPayload):
    if not payload.tenant_id or not payload.workspace_id or not payload.canvas_id:
        raise HTTPException(status_code=403, detail="Fail-Closed: Unauthorized tenant or workspace.")

    from core.runtime_events import RuntimeEventBus, RuntimeEvent
    event = RuntimeEvent(
        tenant_id=payload.tenant_id,
        workspace_id=payload.workspace_id,
        canvas_id=payload.canvas_id,
        graph_id=f"graph_{execution_id}",
        thread_id=execution_id,
        execution_id=execution_id,
        event_type="graph.cancelled",
        sequence_number=1000,
        payload={}
    )
    RuntimeEventBus.get_instance().publish(event)
    return {"success": True, "message": "Execution cancel requested."}


# --- DNK-CANVAS-003 Research Workflow Schemas & Endpoints ---

class AssetPresignRequest(BaseModel):
    filename: Optional[str] = "asset.png"
    mime_type: Optional[str] = "image/png"

class AssetCommitRequest(BaseModel):
    client_sha256: Optional[str] = None
    client_byte_size: Optional[int] = None
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    byte_size: Optional[int] = None


@app.post("/api/v1/workspaces/{workspace_id}/assets/presign", status_code=201)
def presign_asset_upload(
    workspace_id: str,
    payload: AssetPresignRequest,
    current_workspace: str = Depends(get_current_workspace_id)
):
    if current_workspace != workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

    asset_id = str(uuid4())
    filename = payload.filename or "asset.png"
    storage_key = f"assets/{workspace_id}/{asset_id}/{filename}"
    db = SessionLocal()
    try:
        asset = CanvasAsset(
            id=asset_id,
            workspace_id=workspace_id,
            storage_key=storage_key,
            sha256=f"pending_{asset_id}",
            status="pending_upload",
            mime_type=payload.mime_type or "image/png",
            byte_size=0
        )
        db.add(asset)
        db.commit()
        return {
            "asset_id": asset_id,
            "upload_url": f"/api/v1/workspaces/{workspace_id}/assets/{asset_id}/upload",
            "storage_key": storage_key,
            "status": "pending_upload"
        }
    finally:
        db.close()


MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


@app.put("/api/v1/workspaces/{workspace_id}/assets/{asset_id}/upload")
async def upload_asset_binary(
    workspace_id: str,
    asset_id: str,
    request: Request,
    current_workspace: str = Depends(get_current_workspace_id)
):
    if current_workspace != workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

    db = SessionLocal()
    try:
        asset = db.query(CanvasAsset).filter(
            CanvasAsset.id == asset_id,
            CanvasAsset.workspace_id == workspace_id
        ).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found.")

        if asset.status in ("verified", "rejected"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot upload binary for asset in terminal status '{asset.status}'."
            )

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                cl_val = int(content_length)
                if cl_val > MAX_UPLOAD_SIZE_BYTES:
                    asset.status = "rejected"
                    db.commit()
                    raise HTTPException(
                        status_code=413,
                        detail=f"Payload Too Large: Content-Length ({cl_val} bytes) exceeds 10MB limit."
                    )
            except ValueError:
                pass

        file_path = pathlib.Path("/tmp/dnk_canvas_assets") / asset.storage_key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        total_bytes = 0
        try:
            with open(file_path, "wb") as f:
                async for chunk in request.stream():
                    if chunk:
                        total_bytes += len(chunk)
                        if total_bytes > MAX_UPLOAD_SIZE_BYTES:
                            f.close()
                            if file_path.exists():
                                file_path.unlink()
                            asset.status = "rejected"
                            db.commit()
                            raise HTTPException(
                                status_code=413,
                                detail="Payload Too Large: File size exceeds 10MB limit."
                            )
                        f.write(chunk)
        except HTTPException:
            raise
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            asset.status = "rejected"
            db.commit()
            raise HTTPException(status_code=500, detail=f"Failed to process upload stream: {str(e)}")

        if total_bytes == 0:
            if file_path.exists():
                file_path.unlink()
            asset.status = "rejected"
            db.commit()
            raise HTTPException(status_code=400, detail="Empty upload body.")

        asset.status = "uploaded"
        asset.byte_size = total_bytes
        db.commit()
        db.refresh(asset)
        return {
            "asset_id": asset.id,
            "status": asset.status,
            "byte_size": asset.byte_size,
            "storage_key": asset.storage_key
        }
    finally:
        db.close()


@app.post("/api/v1/workspaces/{workspace_id}/assets/{asset_id}/commit")
def commit_asset_upload(
    workspace_id: str,
    asset_id: str,
    payload: Optional[AssetCommitRequest] = None,
    current_workspace: str = Depends(get_current_workspace_id)
):
    if current_workspace != workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

    db = SessionLocal()
    try:
        asset = db.query(CanvasAsset).filter(
            CanvasAsset.id == asset_id,
            CanvasAsset.workspace_id == workspace_id
        ).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found.")

        if asset.status in ("verified", "rejected"):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot commit asset in terminal status '{asset.status}'."
            )

        asset.status = "verifying"
        db.commit()

        file_path = pathlib.Path("/tmp/dnk_canvas_assets") / asset.storage_key
        if not file_path.exists() or not file_path.is_file():
            asset.status = "rejected"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Missing storage object: binary upload file does not exist in physical storage."
            )

        actual_bytes = file_path.read_bytes()
        actual_sha256 = hashlib.sha256(actual_bytes).hexdigest()
        actual_byte_size = len(actual_bytes)

        if actual_byte_size > MAX_UPLOAD_SIZE_BYTES:
            asset.status = "rejected"
            db.commit()
            raise HTTPException(
                status_code=413,
                detail="Payload Too Large: File size in storage exceeds 10MB limit."
            )

        detected_mime = "application/octet-stream"
        if actual_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            detected_mime = "image/png"
        elif actual_bytes.startswith(b"\xff\xd8\xff"):
            detected_mime = "image/jpeg"
        elif actual_bytes.startswith(b"GIF8"):
            detected_mime = "image/gif"
        elif actual_bytes.startswith(b"%PDF"):
            detected_mime = "application/pdf"

        if detected_mime == "application/octet-stream":
            asset.status = "rejected"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="MIME mismatch: physical bytes format is unknown or magic bytes not recognized."
            )

        p_sha = (payload.client_sha256 or payload.sha256) if payload else None
        p_size = (payload.client_byte_size if payload and payload.client_byte_size is not None else payload.byte_size) if payload else None
        p_mime = (payload.mime_type or asset.mime_type) if payload else asset.mime_type

        if p_mime and p_mime != detected_mime:
            asset.status = "rejected"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"MIME mismatch: expected declared '{p_mime}', detected '{detected_mime}'."
            )

        if p_sha and p_sha.lower() != actual_sha256.lower():
            asset.status = "rejected"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="SHA256 mismatch: physical bytes SHA256 does not match client claimed SHA256."
            )

        if p_size is not None and p_size != actual_byte_size:
            asset.status = "rejected"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Byte size mismatch: physical bytes size does not match client claimed byte_size."
            )

        asset.sha256 = actual_sha256
        asset.byte_size = actual_byte_size
        asset.mime_type = detected_mime
        asset.status = "verified"
        db.commit()
        db.refresh(asset)
        return {
            "asset_id": asset.id,
            "status": asset.status,
            "sha256": asset.sha256,
            "byte_size": asset.byte_size,
            "storage_key": asset.storage_key
        }
    finally:
        db.close()


class CompetitorCreate(BaseModel):
    name: str
    website_url: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CanonicalEvidenceCreate(BaseModel):
    asset_id: str
    source_url: str
    captured_at: Optional[datetime] = None
    competitor_id: Optional[str] = None
    evidence_status: Optional[str] = "captured"
    metadata: Optional[Dict[str, Any]] = None

class FixtureEvidenceCreate(BaseModel):
    source_url: str
    image_bytes_base64: str
    captured_at: Optional[datetime] = None
    competitor_id: Optional[str] = None
    evidence_status: Optional[str] = "captured"
    metadata: Optional[Dict[str, Any]] = None

class ElementEvidenceLinkCreate(BaseModel):
    evidence_id: str
    relation_type: Optional[str] = "references"

class InsightCreate(BaseModel):
    title: str
    summary: str
    evidence_id: Optional[str] = None
    competitor_id: Optional[str] = None
    source_references: Optional[Dict[str, Any]] = None

class FlowerDraftCreate(BaseModel):
    insight_id: str
    title: Optional[str] = None
    flower_type: Optional[str] = "task_flower"
    content: Optional[Dict[str, Any]] = None

class ApprovalActionPayload(BaseModel):
    actor_type: Optional[str] = "user"
    actor_id: Optional[str] = "user-1234"
    comments: Optional[str] = None


def record_canvas_audit_event(
    db,
    event_type: str,
    actor_type: str = "user",
    actor_id: str = "user-1234",
    document_id: Optional[str] = None,
    revision_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None
) -> CanvasAuditEvent:
    event = CanvasAuditEvent(
        id=str(uuid4()),
        document_id=document_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event_type,
        revision_id=revision_id,
        payload=payload or {}
    )
    db.add(event)
    return event


@app.post("/api/v1/workspaces/{workspace_id}/competitors", status_code=201)
def create_competitor(
    workspace_id: str,
    payload: CompetitorCreate,
    current_workspace: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id")
):
    if current_workspace != workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

    db = SessionLocal()
    try:
        competitor = CanvasCompetitor(
            id=str(uuid4()),
            workspace_id=workspace_id,
            name=payload.name,
            website_url=payload.website_url,
            description=payload.description,
            status="active",
            competitor_metadata=payload.metadata or {}
        )
        db.add(competitor)

        record_canvas_audit_event(
            db=db,
            event_type="competitor_created",
            actor_type=x_actor_type or "user",
            actor_id=x_actor_id or "user-1234",
            document_id=None,
            payload={
                "workspace_id": workspace_id,
                "competitor_id": competitor.id,
                "name": competitor.name,
                "website_url": competitor.website_url
            }
        )
        db.commit()
        db.refresh(competitor)
        return {
            "id": competitor.id,
            "workspace_id": competitor.workspace_id,
            "name": competitor.name,
            "website_url": competitor.website_url,
            "description": competitor.description,
            "status": competitor.status,
            "metadata": competitor.competitor_metadata,
            "created_at": competitor.created_at.isoformat() if competitor.created_at else None
        }
    finally:
        db.close()


@app.get("/api/v1/workspaces/{workspace_id}/competitors")
def list_competitors(
    workspace_id: str,
    current_workspace: str = Depends(get_current_workspace_id)
):
    if current_workspace != workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

    db = SessionLocal()
    try:
        competitors = db.query(CanvasCompetitor).filter(CanvasCompetitor.workspace_id == workspace_id).all()
        return [
            {
                "id": c.id,
                "workspace_id": c.workspace_id,
                "name": c.name,
                "website_url": c.website_url,
                "description": c.description,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }
            for c in competitors
        ]
    finally:
        db.close()


@app.get("/api/v1/workspaces/{workspace_id}/competitors/{competitor_id}")
def get_competitor(
    workspace_id: str,
    competitor_id: str,
    current_workspace: str = Depends(get_current_workspace_id)
):
    if current_workspace != workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

    db = SessionLocal()
    try:
        competitor = db.query(CanvasCompetitor).filter(
            CanvasCompetitor.id == competitor_id,
            CanvasCompetitor.workspace_id == workspace_id
        ).first()
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found.")
        return {
            "id": competitor.id,
            "workspace_id": competitor.workspace_id,
            "name": competitor.name,
            "website_url": competitor.website_url,
            "description": competitor.description,
            "status": competitor.status,
            "created_at": competitor.created_at.isoformat() if competitor.created_at else None
        }
    finally:
        db.close()


@app.post("/api/v1/workspaces/{workspace_id}/evidence", status_code=201)
def add_canonical_evidence(
    workspace_id: str,
    payload: CanonicalEvidenceCreate,
    current_workspace: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id")
):
    if current_workspace != workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

    db = SessionLocal()
    try:
        asset = db.query(CanvasAsset).filter(
            CanvasAsset.id == payload.asset_id,
            CanvasAsset.workspace_id == workspace_id
        ).first()
        if not asset or asset.status not in ("verified", "committed"):
            raise HTTPException(status_code=400, detail="Provided asset_id is invalid, unverified, or belongs to another workspace.")

        sha256_hash = asset.sha256
        storage_key = asset.storage_key
        storage_mode = "s3"

        existing = db.query(CanvasEvidence).filter(
            CanvasEvidence.workspace_id == workspace_id,
            CanvasEvidence.sha256 == sha256_hash
        ).first()
        if existing:
            return {
                "id": existing.id,
                "workspace_id": existing.workspace_id,
                "competitor_id": existing.competitor_id,
                "asset_id": existing.asset_id,
                "source_url": existing.source_url,
                "captured_at": existing.captured_at.isoformat() if existing.captured_at else None,
                "sha256": existing.sha256,
                "evidence_status": existing.evidence_status,
                "storage_key": existing.storage_key,
                "storage_mode": existing.storage_mode,
                "runtime_scope": "local_fixture_storage",
                "production_s3_verified": False,
                "metadata": existing.evidence_metadata,
                "idempotent": True
            }

        captured_dt = payload.captured_at or datetime.now(timezone.utc)
        meta = payload.metadata or {}
        meta.setdefault("runtime_scope", "local_fixture_storage")
        meta["production_s3_verified"] = False

        evidence = CanvasEvidence(
            id=str(uuid4()),
            workspace_id=workspace_id,
            competitor_id=payload.competitor_id,
            asset_id=asset.id,
            source_url=payload.source_url,
            captured_at=captured_dt,
            sha256=sha256_hash,
            evidence_status=payload.evidence_status or "captured",
            storage_key=storage_key,
            storage_mode=storage_mode,
            evidence_metadata=meta
        )
        db.add(evidence)

        record_canvas_audit_event(
            db=db,
            event_type="evidence_added",
            actor_type=x_actor_type or "user",
            actor_id=x_actor_id or "user-1234",
            document_id=None,
            payload={
                "workspace_id": workspace_id,
                "evidence_id": evidence.id,
                "asset_id": asset.id,
                "source_url": evidence.source_url,
                "sha256": sha256_hash,
                "storage_mode": storage_mode
            }
        )
        db.commit()
        db.refresh(evidence)
        return {
            "id": evidence.id,
            "workspace_id": evidence.workspace_id,
            "competitor_id": evidence.competitor_id,
            "asset_id": evidence.asset_id,
            "source_url": evidence.source_url,
            "captured_at": evidence.captured_at.isoformat() if evidence.captured_at else None,
            "sha256": evidence.sha256,
            "evidence_status": evidence.evidence_status,
            "storage_key": evidence.storage_key,
            "storage_mode": evidence.storage_mode,
            "runtime_scope": "local_fixture_storage",
            "production_s3_verified": False,
            "metadata": evidence.evidence_metadata,
            "idempotent": False
        }
    finally:
        db.close()


@app.post("/api/v1/workspaces/{workspace_id}/evidence/fixture", status_code=201)
def add_fixture_evidence(
    workspace_id: str,
    payload: FixtureEvidenceCreate,
    current_workspace: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id")
):
    if current_workspace != workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

    if is_production_env():
        raise HTTPException(status_code=404, detail="Fixture endpoint disabled in production environment.")

    db = SessionLocal()
    try:
        b64_str = payload.image_bytes_base64
        if "," in b64_str:
            b64_str = b64_str.split(",", 1)[1]
        try:
            raw_bytes = base64.b64decode(b64_str)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid Base64 encoding: {str(e)}")

        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
        byte_size = len(raw_bytes)
        storage_key = f"evidence/{workspace_id}/fixture_{sha256_hash}.png"

        file_path = pathlib.Path("/tmp/dnk_canvas_assets") / storage_key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(raw_bytes)

        existing_asset = db.query(CanvasAsset).filter(
            CanvasAsset.workspace_id == workspace_id,
            CanvasAsset.sha256 == sha256_hash
        ).first()

        if not existing_asset:
            asset = CanvasAsset(
                id=str(uuid4()),
                workspace_id=workspace_id,
                storage_key=storage_key,
                sha256=sha256_hash,
                status="verified",
                mime_type="image/png",
                byte_size=byte_size
            )
            db.add(asset)
            db.flush()
            asset_id = asset.id
        else:
            asset_id = existing_asset.id

        existing = db.query(CanvasEvidence).filter(
            CanvasEvidence.workspace_id == workspace_id,
            CanvasEvidence.sha256 == sha256_hash
        ).first()
        if existing:
            return {
                "id": existing.id,
                "workspace_id": existing.workspace_id,
                "competitor_id": existing.competitor_id,
                "asset_id": existing.asset_id,
                "source_url": existing.source_url,
                "captured_at": existing.captured_at.isoformat() if existing.captured_at else None,
                "sha256": existing.sha256,
                "evidence_status": existing.evidence_status,
                "storage_key": existing.storage_key,
                "storage_mode": "fixture",
                "idempotent": True
            }

        captured_dt = payload.captured_at or datetime.now(timezone.utc)
        evidence = CanvasEvidence(
            id=str(uuid4()),
            workspace_id=workspace_id,
            competitor_id=payload.competitor_id,
            asset_id=asset_id,
            source_url=payload.source_url,
            captured_at=captured_dt,
            sha256=sha256_hash,
            evidence_status=payload.evidence_status or "captured",
            storage_key=storage_key,
            storage_mode="fixture",
            evidence_metadata=payload.metadata or {}
        )
        db.add(evidence)

        record_canvas_audit_event(
            db=db,
            event_type="fixture_evidence_captured",
            actor_type=x_actor_type or "user",
            actor_id=x_actor_id or "user-1234",
            document_id=None,
            payload={
                "workspace_id": workspace_id,
                "evidence_id": evidence.id,
                "asset_id": asset_id,
                "source_url": evidence.source_url,
                "sha256": sha256_hash,
                "storage_mode": "fixture"
            }
        )
        db.commit()
        db.refresh(evidence)
        return {
            "id": evidence.id,
            "workspace_id": evidence.workspace_id,
            "competitor_id": evidence.competitor_id,
            "asset_id": evidence.asset_id,
            "source_url": evidence.source_url,
            "captured_at": evidence.captured_at.isoformat() if evidence.captured_at else None,
            "sha256": evidence.sha256,
            "evidence_status": evidence.evidence_status,
            "storage_key": evidence.storage_key,
            "storage_mode": evidence.storage_mode,
            "runtime_scope": "local_fixture_storage",
            "production_s3_verified": False,
            "metadata": evidence.evidence_metadata,
            "idempotent": False
        }
    finally:
        db.close()


@app.get("/api/v1/workspaces/{workspace_id}/evidence")
def list_evidence(
    workspace_id: str,
    current_workspace: str = Depends(get_current_workspace_id)
):
    if current_workspace != workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

    db = SessionLocal()
    try:
        evidences = db.query(CanvasEvidence).filter(CanvasEvidence.workspace_id == workspace_id).all()
        return [
            {
                "id": ev.id,
                "workspace_id": ev.workspace_id,
                "competitor_id": ev.competitor_id,
                "asset_id": ev.asset_id,
                "source_url": ev.source_url,
                "captured_at": ev.captured_at.isoformat() if ev.captured_at else None,
                "sha256": ev.sha256,
                "evidence_status": ev.evidence_status,
                "storage_key": ev.storage_key,
                "storage_mode": ev.storage_mode
            }
            for ev in evidences
        ]
    finally:
        db.close()


@app.post("/api/v1/canvases/{canvas_id}/elements/{element_id}/evidence", status_code=201)
def link_evidence_to_element(
    canvas_id: str,
    element_id: str,
    payload: ElementEvidenceLinkCreate,
    current_workspace: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id")
):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas document not found.")

        if current_workspace != doc.workspace_id:
            raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

        evidence = db.query(CanvasEvidence).filter(CanvasEvidence.id == payload.evidence_id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found.")

        if evidence.workspace_id != doc.workspace_id:
            raise HTTPException(status_code=403, detail="Cross-workspace evidence linking forbidden.")

        # Link asset via CanvasAssetLink if asset_id is present
        if evidence.asset_id:
            existing_asset_link = db.query(CanvasAssetLink).filter(
                CanvasAssetLink.document_id == canvas_id,
                CanvasAssetLink.element_id == element_id,
                CanvasAssetLink.asset_id == evidence.asset_id
            ).first()
            if not existing_asset_link:
                asset_link = CanvasAssetLink(
                    id=str(uuid4()),
                    asset_id=evidence.asset_id,
                    document_id=canvas_id,
                    element_id=element_id,
                    relation_type=payload.relation_type or "references"
                )
                db.add(asset_link)

        # Link entity via CanvasLink
        existing_link = db.query(CanvasLink).filter(
            CanvasLink.document_id == canvas_id,
            CanvasLink.element_id == element_id,
            CanvasLink.entity_type == "evidence",
            CanvasLink.entity_id == evidence.id
        ).first()

        if not existing_link:
            link = CanvasLink(
                id=str(uuid4()),
                document_id=canvas_id,
                element_id=element_id,
                entity_type="evidence",
                entity_id=evidence.id,
                relation_type=payload.relation_type or "references"
            )
            db.add(link)

        record_canvas_audit_event(
            db=db,
            event_type="asset_linked",
            actor_type=x_actor_type or "user",
            actor_id=x_actor_id or "user-1234",
            document_id=canvas_id,
            payload={
                "document_id": canvas_id,
                "element_id": element_id,
                "evidence_id": evidence.id,
                "asset_id": evidence.asset_id,
                "sha256": evidence.sha256,
                "source_url": evidence.source_url
            }
        )
        db.commit()
        return {
            "document_id": canvas_id,
            "element_id": element_id,
            "evidence_id": evidence.id,
            "asset_id": evidence.asset_id,
            "status": "linked"
        }
    finally:
        db.close()


@app.post("/api/v1/canvases/{canvas_id}/elements/{element_id}/insights", status_code=201)
def create_element_insight(
    canvas_id: str,
    element_id: str,
    payload: InsightCreate,
    current_workspace: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id")
):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas document not found.")

        if current_workspace != doc.workspace_id:
            raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

        # Prepare source references
        source_refs = dict(payload.source_references or {})
        source_refs["document_id"] = canvas_id
        source_refs["element_id"] = element_id

        if payload.evidence_id:
            evidence = db.query(CanvasEvidence).filter(CanvasEvidence.id == payload.evidence_id).first()
            if not evidence:
                raise HTTPException(status_code=404, detail="Evidence not found.")
            if evidence.workspace_id != doc.workspace_id:
                raise HTTPException(status_code=403, detail="Cross-workspace evidence reference forbidden.")
            source_refs["evidence_source_url"] = evidence.source_url
            source_refs["evidence_sha256"] = evidence.sha256
            if not payload.competitor_id and evidence.competitor_id:
                payload.competitor_id = evidence.competitor_id

        if payload.competitor_id:
            competitor = db.query(CanvasCompetitor).filter(CanvasCompetitor.id == payload.competitor_id).first()
            if competitor:
                if competitor.workspace_id != doc.workspace_id:
                    raise HTTPException(status_code=403, detail="Cross-workspace competitor reference forbidden.")
                source_refs["competitor_name"] = competitor.name
                source_refs["competitor_url"] = competitor.website_url

        insight = CanvasInsight(
            id=str(uuid4()),
            workspace_id=doc.workspace_id,
            document_id=canvas_id,
            element_id=element_id,
            evidence_id=payload.evidence_id,
            competitor_id=payload.competitor_id,
            title=payload.title,
            summary=payload.summary,
            status="proposed",  # Insight is created in proposed status
            source_references=source_refs,
            created_by=x_actor_id or "user-1234"
        )
        db.add(insight)

        # Link entity via CanvasLink
        link = CanvasLink(
            id=str(uuid4()),
            document_id=canvas_id,
            element_id=element_id,
            entity_type="insight",
            entity_id=insight.id,
            relation_type="produces"
        )
        db.add(link)

        record_canvas_audit_event(
            db=db,
            event_type="insight_created",
            actor_type=x_actor_type or "user",
            actor_id=x_actor_id or "user-1234",
            document_id=canvas_id,
            payload={
                "document_id": canvas_id,
                "element_id": element_id,
                "insight_id": insight.id,
                "title": insight.title,
                "status": "proposed"
            }
        )
        db.commit()
        db.refresh(insight)
        return {
            "id": insight.id,
            "workspace_id": insight.workspace_id,
            "document_id": insight.document_id,
            "element_id": insight.element_id,
            "evidence_id": insight.evidence_id,
            "competitor_id": insight.competitor_id,
            "title": insight.title,
            "summary": insight.summary,
            "status": insight.status,
            "source_references": insight.source_references,
            "created_at": insight.created_at.isoformat() if insight.created_at else None
        }
    finally:
        db.close()


@app.post("/api/v1/canvases/{canvas_id}/elements/{element_id}/flowers", status_code=201)
def create_flower_draft_from_insight(
    canvas_id: str,
    element_id: str,
    payload: FlowerDraftCreate,
    current_workspace: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id")
):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas document not found.")

        if current_workspace != doc.workspace_id:
            raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

        # Validate insight exists and belongs to workspace
        insight = db.query(CanvasInsight).filter(CanvasInsight.id == payload.insight_id).first()
        if not insight:
            raise HTTPException(status_code=400, detail="Valid Insight is required before creating a Flower draft.")

        if insight.workspace_id != doc.workspace_id:
            raise HTTPException(status_code=403, detail="Cross-workspace insight referencing forbidden.")

        source_refs = {
            "document_id": canvas_id,
            "element_id": element_id,
            "insight_id": insight.id,
            "insight_title": insight.title,
            "insight_source_references": insight.source_references
        }

        title = payload.title or f"Flower: {insight.title}"
        content = payload.content or {
            "description": insight.summary,
            "plant_scale": "flower",
            "mrh_id": f"Flower_{insight.id[:8]}",
            "derived_from_insight": insight.id
        }

        flower = FlowerDraft(
            id=str(uuid4()),
            workspace_id=doc.workspace_id,
            document_id=canvas_id,
            element_id=element_id,
            insight_id=insight.id,
            title=title,
            status="draft",  # Flower draft created in draft status
            flower_type=payload.flower_type or "task_flower",
            content=content,
            source_references=source_refs,
            created_by=x_actor_id or "user-1234"
        )
        db.add(flower)

        link = CanvasLink(
            id=str(uuid4()),
            document_id=canvas_id,
            element_id=element_id,
            entity_type="flower",
            entity_id=flower.id,
            relation_type="derives"
        )
        db.add(link)

        record_canvas_audit_event(
            db=db,
            event_type="flower_drafted",
            actor_type=x_actor_type or "user",
            actor_id=x_actor_id or "user-1234",
            document_id=canvas_id,
            payload={
                "document_id": canvas_id,
                "element_id": element_id,
                "flower_id": flower.id,
                "insight_id": insight.id,
                "title": flower.title,
                "status": "draft"
            }
        )
        db.commit()
        db.refresh(flower)
        return {
            "id": flower.id,
            "workspace_id": flower.workspace_id,
            "document_id": flower.document_id,
            "element_id": flower.element_id,
            "insight_id": flower.insight_id,
            "title": flower.title,
            "status": flower.status,
            "flower_type": flower.flower_type,
            "content": flower.content,
            "source_references": flower.source_references,
            "created_at": flower.created_at.isoformat() if flower.created_at else None
        }
    finally:
        db.close()


@app.get("/api/v1/canvases/{canvas_id}/elements/{element_id}/research")
def get_element_research(
    canvas_id: str,
    element_id: str,
    current_workspace: str = Depends(get_current_workspace_id)
):
    db = SessionLocal()
    try:
        doc = db.query(CanvasDocument).filter(CanvasDocument.id == canvas_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Canvas document not found.")

        if current_workspace != doc.workspace_id:
            raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

        # Query linked evidence
        links = db.query(CanvasLink).filter(
            CanvasLink.document_id == canvas_id,
            CanvasLink.element_id == element_id
        ).all()

        evidence_ids = [l.entity_id for l in links if l.entity_type == "evidence"]
        evidences = db.query(CanvasEvidence).filter(CanvasEvidence.id.in_(evidence_ids)).all() if evidence_ids else []

        insights = db.query(CanvasInsight).filter(
            CanvasInsight.document_id == canvas_id,
            CanvasInsight.element_id == element_id
        ).all()

        flowers = db.query(FlowerDraft).filter(
            FlowerDraft.document_id == canvas_id,
            FlowerDraft.element_id == element_id
        ).all()

        audit_events = db.query(CanvasAuditEvent).filter(
            CanvasAuditEvent.document_id == canvas_id
        ).order_by(CanvasAuditEvent.created_at.desc()).all()

        element_audit = [
            {
                "id": a.id,
                "event_type": a.event_type,
                "actor_type": a.actor_type,
                "actor_id": a.actor_id,
                "payload": a.payload,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in audit_events
            if a.payload.get("element_id") == element_id or not a.payload.get("element_id")
        ]

        return {
            "document_id": canvas_id,
            "element_id": element_id,
            "evidences": [
                {
                    "id": ev.id,
                    "source_url": ev.source_url,
                    "captured_at": ev.captured_at.isoformat() if ev.captured_at else None,
                    "sha256": ev.sha256,
                    "evidence_status": ev.evidence_status,
                    "storage_key": ev.storage_key,
                    "storage_mode": ev.storage_mode
                }
                for ev in evidences
            ],
            "insights": [
                {
                    "id": ins.id,
                    "title": ins.title,
                    "summary": ins.summary,
                    "status": ins.status,
                    "source_references": ins.source_references,
                    "created_at": ins.created_at.isoformat() if ins.created_at else None
                }
                for ins in insights
            ],
            "flowers": [
                {
                    "id": fl.id,
                    "insight_id": fl.insight_id,
                    "title": fl.title,
                    "status": fl.status,
                    "flower_type": fl.flower_type,
                    "content": fl.content,
                    "source_references": fl.source_references,
                    "created_at": fl.created_at.isoformat() if fl.created_at else None
                }
                for fl in flowers
            ],
            "audit_trail": element_audit
        }
    finally:
        db.close()


@app.post("/api/v1/insights/{insight_id}/approve")
def approve_insight(
    insight_id: str,
    payload: Optional[ApprovalActionPayload] = None,
    current_workspace: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id")
):
    header_actor_type = (x_actor_type or "").strip().lower()
    body_actor_type = (payload.actor_type if payload and payload.actor_type else "").strip().lower()

    if header_actor_type and body_actor_type and header_actor_type != body_actor_type:
        raise HTTPException(
            status_code=400,
            detail="Actor type discrepancy between credentials header (X-Actor-Type) and payload."
        )

    actor_type = header_actor_type or body_actor_type or "user"
    actor_id = x_actor_id or (payload.actor_id if payload and payload.actor_id else None) or "user-1234"

    # Fail-closed guard: agents cannot self-approve Insight
    if actor_type == "agent":
        raise HTTPException(
            status_code=403,
            detail="Agent cannot self-approve Insight or Flower. Human approval required."
        )

    db = SessionLocal()
    try:
        insight = db.query(CanvasInsight).filter(CanvasInsight.id == insight_id).first()
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found.")

        if current_workspace != insight.workspace_id:
            raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

        insight.status = "approved"
        record_canvas_audit_event(
            db=db,
            event_type="insight_approved",
            actor_type=actor_type,
            actor_id=actor_id,
            document_id=insight.document_id,
            payload={
                "insight_id": insight.id,
                "status": "approved",
                "approved_by": actor_id,
                "actor_source": "X-Actor-Type header" if header_actor_type else "body_payload"
            }
        )
        db.commit()
        db.refresh(insight)
        return {"id": insight.id, "status": insight.status, "approved_by": actor_id}
    finally:
        db.close()


@app.post("/api/v1/flowers/{flower_id}/approve")
def approve_flower(
    flower_id: str,
    payload: Optional[ApprovalActionPayload] = None,
    current_workspace: str = Depends(get_current_workspace_id),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type"),
    x_actor_id: Optional[str] = Header(None, alias="X-Actor-Id")
):
    header_actor_type = (x_actor_type or "").strip().lower()
    body_actor_type = (payload.actor_type if payload and payload.actor_type else "").strip().lower()

    if header_actor_type and body_actor_type and header_actor_type != body_actor_type:
        raise HTTPException(
            status_code=400,
            detail="Actor type discrepancy between credentials header (X-Actor-Type) and payload."
        )

    actor_type = header_actor_type or body_actor_type or "user"
    actor_id = x_actor_id or (payload.actor_id if payload and payload.actor_id else None) or "user-1234"

    # Fail-closed guard: agents cannot self-approve Flower
    if actor_type == "agent":
        raise HTTPException(
            status_code=403,
            detail="Agent cannot self-approve Insight or Flower. Human approval required."
        )

    db = SessionLocal()
    try:
        flower = db.query(FlowerDraft).filter(FlowerDraft.id == flower_id).first()
        if not flower:
            raise HTTPException(status_code=404, detail="Flower draft not found.")

        if current_workspace != flower.workspace_id:
            raise HTTPException(status_code=403, detail="Cross-workspace access denied.")

        flower.status = "approved"
        record_canvas_audit_event(
            db=db,
            event_type="flower_approved",
            actor_type=actor_type,
            actor_id=actor_id,
            document_id=flower.document_id,
            payload={
                "flower_id": flower.id,
                "status": "approved",
                "approved_by": actor_id,
                "actor_source": "X-Actor-Type header" if header_actor_type else "body_payload"
            }
        )
        db.commit()
        db.refresh(flower)
        return {"id": flower.id, "status": flower.status, "approved_by": actor_id}
    finally:
        db.close()


# =====================================================================
# Phase 2 Step 2: AI Action Adapters Endpoints
# =====================================================================

@app.post("/api/v1/canvas/ai/cutout", response_model=CanvasCutoutResponse)
async def cutout_background(
    payload: CanvasCutoutRequest,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """BiRefNet background removal / cutout endpoint."""
    img = payload.image_base64 or payload.image_url
    if not img or not str(img).strip():
        raise HTTPException(status_code=422, detail="Missing image_base64 or image_url in payload")
    
    img_data = str(img)
    result = await birefnet_client.cutout_background(
        image_data=img_data,
        return_mask=payload.return_mask,
        threshold=payload.threshold,
        **(payload.options or {})
    )
    return CanvasCutoutResponse(
        success=True,
        image_base64=result["image_base64"],
        mask_base64=result.get("mask_base64"),
        node_id=payload.node_id,
        mime_type="image/png",
        execution_time_ms=result.get("execution_time_ms", 0.0),
        model=result.get("model", "BiRefNet-v1"),
        metadata={
            "workspace_id": workspace_id,
            "canvas_id": payload.canvas_id,
            "source": result.get("source", "unknown")
        }
    )


@app.post("/api/v1/canvas/ai/relight", response_model=CanvasRelightResponse)
async def relight_image(
    payload: CanvasRelightRequest,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """IC-Light image relighting and environment harmonization endpoint."""
    fg = payload.foreground_base64 or payload.foreground_url
    if not fg or not str(fg).strip():
        raise HTTPException(status_code=422, detail="Missing foreground_base64 or foreground_url in payload")
    
    fg_data = str(fg)
    bg = payload.background_base64 or payload.background_url
    bg_data = str(bg) if bg and str(bg).strip() else None
    result = await iclight_client.relight(
        foreground=fg_data,
        background=bg_data,
        lighting_prompt=payload.lighting_prompt,
        light_direction=payload.light_direction,
        intensity=payload.intensity,
        **(payload.options or {})
    )
    return CanvasRelightResponse(
        success=True,
        image_base64=result["image_base64"],
        node_id=payload.foreground_node_id,
        mime_type="image/png",
        execution_time_ms=result.get("execution_time_ms", 0.0),
        model=result.get("model", "IC-Light-v1"),
        metadata={
            "workspace_id": workspace_id,
            "canvas_id": payload.canvas_id,
            "light_direction": payload.light_direction,
            "intensity": payload.intensity,
            "source": result.get("source", "unknown")
        }
    )


@app.post("/api/v1/canvas/ai/generate-layer", response_model=CanvasGenerateLayerResponse)
async def generate_layer(
    payload: CanvasGenerateLayerRequest,
    workspace_id: str = Depends(get_current_workspace_id)
):
    """FLUX.1 + LayerDiffuse isolated transparent layer generation endpoint."""
    if not payload.prompt or not payload.prompt.strip():
        raise HTTPException(status_code=422, detail="Prompt must not be empty")
    
    result = await flux_layerdiffuse_client.generate_layer(
        prompt=payload.prompt,
        negative_prompt=payload.negative_prompt,
        style=payload.style,
        width=payload.width,
        height=payload.height,
        transparent=payload.transparent_background,
        layer_type=payload.layer_type,
        **(payload.options or {})
    )
    return CanvasGenerateLayerResponse(
        success=True,
        image_base64=result["image_base64"],
        layer_data=result.get("layer_data", {}),
        mime_type="image/png",
        execution_time_ms=result.get("execution_time_ms", 0.0),
        model=result.get("model", "FLUX.1-LayerDiffuse"),
        metadata={
            "workspace_id": workspace_id,
            "canvas_id": payload.canvas_id,
            "prompt": payload.prompt,
            "style": payload.style,
            "source": result.get("source", "unknown")
        }
    )


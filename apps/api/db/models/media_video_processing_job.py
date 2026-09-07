# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_media_video_processing_job"
# purpose: "SQLAlchemy ORM Model for Video Processing Jobs (DNK-MEDIA-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    BigInteger,
    Numeric,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class MediaVideoProcessingJobModel(Base):
    __tablename__ = "media_video_processing_jobs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    source_file_path = Column(String(512), nullable=False)
    source_file_size_bytes = Column(BigInteger, nullable=False, default=0)
    source_duration_seconds = Column(Numeric(10, 2), nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # 'pending', 'chunking', 'transcoding', 'packaging', 'completed', 'failed'
    progress_percentage = Column(Numeric(5, 2), nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    chunks = relationship(
        "MediaVideoChunkModel",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    transcoding_tasks = relationship(
        "MediaTranscodingTaskModel",
        back_populates="job",
        cascade="all, delete-orphan",
    )
    packaging_outputs = relationship(
        "MediaPackagingOutputModel",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_media_job_workspace_status", "workspace_id", "status"),
    )

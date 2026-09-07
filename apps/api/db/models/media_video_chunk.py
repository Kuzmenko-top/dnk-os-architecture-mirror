# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_media_video_chunk"
# purpose: "SQLAlchemy ORM Model for GOP-aligned Video Chunks (DNK-MEDIA-002)"
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
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class MediaVideoChunkModel(Base):
    __tablename__ = "media_video_chunks"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(128), ForeignKey("media_video_processing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    start_frame = Column(Integer, nullable=False, default=0)
    end_frame = Column(Integer, nullable=False, default=0)
    start_time_seconds = Column(Numeric(10, 2), nullable=False, default=0.0)
    end_time_seconds = Column(Numeric(10, 2), nullable=False, default=0.0)
    chunk_file_path = Column(String(512), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # 'pending', 'processing', 'completed', 'failed'
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    job = relationship("MediaVideoProcessingJobModel", back_populates="chunks")
    transcoding_tasks = relationship(
        "MediaTranscodingTaskModel",
        back_populates="chunk",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_media_chunk_job_index", "job_id", "chunk_index"),
    )

# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_media_transcoding_task"
# purpose: "SQLAlchemy ORM Model for Chunk Transcoding Tasks (DNK-MEDIA-002)"
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


class MediaTranscodingTaskModel(Base):
    __tablename__ = "media_transcoding_tasks"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id = Column(String(128), ForeignKey("media_video_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(128), ForeignKey("media_video_processing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    codec = Column(String(20), nullable=False)  # 'h264', 'h265', 'vp9', 'av1'
    resolution = Column(String(10), nullable=False)  # '1080p', '720p', '480p', '360p'
    target_bitrate_kbps = Column(Integer, nullable=False)
    hardware_acceleration = Column(String(20), nullable=True)  # 'nvenc', 'vaapi', 'videotoolbox', None (software)
    status = Column(String(20), nullable=False, default="pending")  # 'pending', 'processing', 'completed', 'failed'
    worker_id = Column(String(255), nullable=True)
    output_file_path = Column(String(512), nullable=True)
    processing_time_seconds = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    chunk = relationship("MediaVideoChunkModel", back_populates="transcoding_tasks")
    job = relationship("MediaVideoProcessingJobModel", back_populates="transcoding_tasks")

    __table_args__ = (
        Index("ix_media_task_job_codec_res", "job_id", "codec", "resolution"),
    )

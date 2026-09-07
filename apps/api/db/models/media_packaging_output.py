# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_media_packaging_output"
# purpose: "SQLAlchemy ORM Model for HLS/DASH Packaging Outputs (DNK-MEDIA-002)"
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
    JSON,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class MediaPackagingOutputModel(Base):
    __tablename__ = "media_packaging_outputs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(128), ForeignKey("media_video_processing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    packaging_type = Column(String(10), nullable=False)  # 'hls', 'dash'
    playlist_file_path = Column(String(512), nullable=False)  # .m3u8 or .mpd
    variant_resolutions = Column(JSON, nullable=False, default=lambda: ["1080p", "720p", "480p", "360p"])
    segment_duration_seconds = Column(Integer, nullable=False, default=4)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    job = relationship("MediaVideoProcessingJobModel", back_populates="packaging_outputs")

    __table_args__ = (
        Index("ix_media_packaging_job_type", "job_id", "packaging_type"),
    )

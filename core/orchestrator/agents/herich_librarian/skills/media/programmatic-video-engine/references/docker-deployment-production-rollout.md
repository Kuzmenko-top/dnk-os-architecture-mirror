# DNK Video Librarian — Docker Deployment & Production Rollout Architecture (DNK-STD-0086)

## 📁 Architecture & File Layout

```
DNK OS/
├── Dockerfile                  # Multi-stage build for FastAPI & Celery
├── docker-compose.yml          # Core services: api, db, redis, worker
├── docker-compose.prod.yml     # Production overrides (limits, replicas)
├── .env.example                # Environment variables template
├── core/
│   └── workers/
│       ├── __init__.py
│       └── celery_app.py       # Celery task queue & async media handlers
├── scripts/
│   └── docker/
│       ├── init-db.sql         # pgvector extension & HNSW/IVFFlat indexes
│       └── healthcheck.sh      # Container health verification
└── docs/
    └── DEPLOYMENT.md           # Production deployment & operations guide
```

---

## 🛠️ Multi-Stage Dockerfile Pattern

```dockerfile # Stage 1: Builder
FROM python:3.12-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim as runtime
WORKDIR /app
RUN apt-get update && apt-get install -y \
    ffmpeg \
    ffprobe \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=builder /root/.local /home/appuser/.local
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🗄️ PostgreSQL + pgvector Init SQL (`init-db.sql`)

```sql
-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Video metadata & vector index creation
CREATE TABLE IF NOT EXISTS footage_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    footage_id UUID NOT NULL REFERENCES footage(id) ON DELETE CASCADE,
    segment_index INT NOT NULL,
    start_time_sec FLOAT NOT NULL,
    end_time_sec FLOAT NOT NULL,
    text_chunk TEXT NOT NULL,
    embedding vector(1024) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- IVFFlat index for fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_footage_vectors_embedding_ivfflat
ON footage_vectors USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## ⚡ Celery Worker Configuration (`celery_app.py`)

```python
import os
from celery import Celery

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("dnk_video_librarian", broker=broker_url, backend=result_backend)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

@celery_app.task(name="core.workers.celery_app.ingest_media_task")
def ingest_media_task(file_path: str) -> dict:
    # Async background media ingestion & SHA-256 deduplication
    return {"status": "success", "file_path": file_path}
```

---

## 🐍 Pytest Pyproject `pythonpath` Resolution Pattern

When running `pytest -c path/to/pyproject.toml`, pytest locks its `rootdir` to the folder containing `pyproject.toml`. To ensure imports resolve across both root and sub-modules:

```toml
[tool.pytest.ini_options]
pythonpath = [
  "..",
  ".",
  "DNK OS",
  "apps/api",
  "adapters",
  "dnk_os",
  "services"
]
```

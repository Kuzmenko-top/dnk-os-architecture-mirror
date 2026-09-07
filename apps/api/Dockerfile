# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/Dockerfile"
# purpose: "Dedicated Dockerfile for DNK OS Backend API component"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# ==============================================================================
# Stage 1: Dependency Builder
# ==============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Fast installation of core runtime and testing dependencies
RUN pip install --no-cache-dir \
    fastapi>=0.111.0 \
    uvicorn[standard]>=0.30.0 \
    pydantic>=2.7.0 \
    pydantic-settings>=2.2.0 \
    pytest>=8.0.0 \
    pytest-asyncio>=0.23.0 \
    pytest-cov>=5.0.0 \
    httpx>=0.27.0 \
    asyncpg>=0.29.0 \
    psycopg2-binary>=2.9.9 \
    redis>=5.0.0 \
    pyyaml>=6.0.1 \
    sqlalchemy>=2.0.30 \
    starlette>=0.37.0 \
    structlog>=24.1.0 \
    cryptography>=42.0.0 \
    python-multipart>=0.0.9 \
    pyjwt>=2.8.0 \
    psutil>=5.9.0

# ==============================================================================
# Stage 2: Application Runner
# ==============================================================================
FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    procps \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/services"
ENV PYTHONUNBUFFERED="1"
ENV ENVIRONMENT="development"

# Copy essential codebase into container
COPY pyproject.toml ./
COPY core/ ./core/
COPY apps/ ./apps/
COPY services/ ./services/
COPY tests/ ./tests/
COPY dnk_os/ ./dnk_os/
COPY adapters/ ./adapters/
COPY skills/ ./skills/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- DNK-MRH-HEADER ---
# mrh_id: "services_dnk_canvas_api_Dockerfile"
# purpose: "Production multi-stage Docker build for dnk_canvas_api backend service"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# --- END DNK-MRH-HEADER ---

# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt || true

COPY . .
RUN pip install --no-cache-dir --no-deps -e . || true

# Stage 2: Production Runner
FROM python:3.12-slim AS runner

WORKDIR /app

# Install runtime system libraries only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV ENVIRONMENT="production"
ENV PYTHONUNBUFFERED="1"

# Copy application source
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["uvicorn", "services.dnk_canvas_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

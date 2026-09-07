# --- DNK-MRH-HEADER ---
# mrh_id: "Dockerfile"
# purpose: "Multi-stage Docker build for DNK OS Multi-Agent Core (Python runtime + Node.js shell)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Stage 1: Python backend builder
FROM python:3.12-slim AS python-builder

WORKDIR /app

# Install build dependencies & python packages
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Node.js frontend builder (Next.js)
FROM node:24-slim AS node-builder

WORKDIR /app

# Copy frontend source if available
COPY apps/web/package*.json ./
RUN if [ -f package.json ]; then npm ci || npm install; fi

COPY apps/web/ ./
RUN if [ -f package.json ] && grep -q "build" package.json; then npm run build; fi

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
EXPOSE 3000
CMD ["npm", "start"]

# Stage 3: Final production runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install system utilities & curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq5 && rm -rf /var/lib/apt/lists/*

# Copy python packages from builder
COPY --from=python-builder /install /usr/local

# Copy application source
COPY dnk_os/ ./dnk_os/
COPY adapters/ ./adapters/
COPY skills/ ./skills/
COPY core/ ./core/
COPY services/ ./services/

# Container Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose API and frontend ports
EXPOSE 8000 3000

# Default entrypoint
CMD ["python", "-m", "uvicorn", "dnk_os.core.agent:app", "--host", "0.0.0.0", "--port", "8000"]

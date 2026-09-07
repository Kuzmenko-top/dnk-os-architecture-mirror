# --- DNK-MRH-HEADER ---
# mrh_id: "Dockerfile.frontend"
# purpose: "Production & Development Docker container for DNK OS Frontend (Next.js 14, React 18, Standalone runtime)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# ==========================================
# Stage 1: Dependency Resolver
# ==========================================
FROM node:20-alpine AS deps

RUN apk add --no-cache libc6-compat

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm install --legacy-peer-deps --ignore-scripts

# ==========================================
# Stage 2: Application Build
# ==========================================
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY apps/web/ ./
COPY packages/ /packages/

ENV NEXT_TELEMETRY_DISABLED="1"
ENV NODE_ENV="production"

RUN mkdir -p public && npm run build && \
    if [ -d .next/standalone ]; then \
      mkdir -p .next/standalone/.next && \
      cp -r .next/static .next/standalone/.next/ && \
      if [ -d public ]; then cp -r public .next/standalone/; fi; \
    fi

# ==========================================
# Stage 3: Production Runtime
# ==========================================
FROM node:20-alpine AS runner

WORKDIR /app

RUN apk add --no-cache curl wget

ENV NODE_ENV="production"
ENV NEXT_TELEMETRY_DISABLED="1"
ENV PORT="3000"
ENV HOSTNAME="0.0.0.0"

# Non-root security user
RUN addgroup --system --gid 10001 nodejs && \
    adduser --system --uid 10001 nextjs

# Copy runtime assets and application artifacts
COPY --from=builder --chown=nextjs:nodejs /app/ ./

USER 10001:10001

EXPOSE 3000

HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || curl -f http://localhost:3000/ || exit 1

CMD ["sh", "-c", "if [ -d .next/standalone ]; then node .next/standalone/server.js; elif [ -f server.js ]; then node server.js; else npm start; fi"]

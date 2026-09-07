# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/CANVAS_STUDIO_PRODUCTION_DEPLOYMENT.md"
# purpose: "Production Deployment Architecture and Microservices Specification for DNK OS Canvas Studio"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# --- END DNK-MRH-HEADER ---

# 🚀 DNK OS Canvas Studio — Production Deployment Architecture

## 1. System Topology Overview

DNK OS Canvas Studio delivers a cloud-native, high-performance visual composition and generative AI engine (CapCut Design & Figma-like capabilities).

```
 ┌──────────────────────────────────────────────────────────────┐
 │                      Client Browser                          │
 │         (React 18 / Next.js 14 + Zustand Store)              │
 └──────────────┬───────────────────────────────▲───────────────┘
                │ HTTP REST / WebSocket         │
                ▼                               │
 ┌──────────────────────────────────────────────┴───────────────┐
 │               Reverse Proxy Gateway (Nginx / Cloudflare)     │
 └──────────────┬───────────────────────────────┬───────────────┘
                │ /api/v1/canvas/*              │ /
                ▼                               ▼
 ┌──────────────────────────────┐ ┌─────────────────────────────┐
 │       dnk_canvas_api         │ │       apps/web (Next)       │
 │   FastAPI Backend (Port 8000)│ │    Frontend UI (Port 3000)  │
 └──────────────┬───────────────┘ └─────────────────────────────┘
                │
                ├──────────────────────────────┐
                ▼                              ▼
 ┌──────────────────────────────┐ ┌─────────────────────────────┐
 │     dnk_canvas_worker        │ │        Redis 7 Stack        │
 │  GPU Celery/Inference (8001) │ │  PubSub, Caching & Queues   │
 │ (BiRefNet, IC-Light, FLUX.1) │ │         (Port 6379)         │
 └──────────────────────────────┘ └─────────────────────────────┘
```

---

## 2. Containerized Microservices

### 2.1 `canvas-api` (FastAPI)
- **Role**: High-throughput REST API and WebSocket session hub.
- **Port**: `8000`
- **Key Endpoints**:
  - `POST /api/v1/canvas/ai/cutout` (BiRefNet background removal)
  - `POST /api/v1/canvas/ai/relight` (IC-Light environmental lighting)
  - `POST /api/v1/canvas/ai/generate-layer` (FLUX.1-LayerDiffuse generation)
  - `WS /api/v1/canvas/ws` (Real-time collaboration & presence)
- **Healthcheck**: `python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"`

### 2.2 `canvas-worker` (Inference Worker)
- **Role**: Dedicated GPU worker executing heavy diffusion and vision model pipelines.
- **Hardware Acceleration**: NVIDIA CUDA with PyTorch 2.x and TensorRT optimizations.
- **Model Suite**:
  - `BiRefNet-v1` (Dichotomous Image Segmentation)
  - `IC-Light-v1` (Consistent Lighting & Directional Shadowing)
  - `FLUX.1-LayerDiffuse` (RGBA Transparent Generation)

### 2.3 `canvas-web` (Frontend Next.js)
- **Role**: Client UI delivery, static asset optimization, server-side rendering for studio metadata.
- **Port**: `3000`

### 2.4 `canvas-redis` (Cache & Event Broker)
- **Role**: Undo/Redo delta syncing, snapshot caching, and Celery task broker.
- **Port**: `6379`

---

## 3. Production Deployment Commands

```bash
# 1. Clone and Navigate to DNK OS Root
cd DNK_HUB

# 2. Build and Launch Canvas Studio Stack
docker compose -f docker-compose.canvas.yml up -d --build

# 3. Check Container Health
docker compose -f docker-compose.canvas.yml ps

# 4. View Real-time Logs
docker compose -f docker-compose.canvas.yml logs -f canvas-api canvas-worker
```

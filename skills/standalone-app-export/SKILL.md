---
name: standalone-app-export
description: Exports a clean, standalone, deploy-ready client repository (Tier 2: DNKOS_APP) from the unified R&D Swarm Hub (Tier 1: DNK_HUB) per the Two-Tier Development Protocol.
---

# 🚀 Two-Tier Standalone App Export Skill (DNKOS_APP)

## 📌 Context & Purpose
The DNK OS ecosystem follows a **Two-Tier Architecture**:
1. **Tier 1 (`DNK_HUB`)**: The complete R&D Laboratory and Swarm Hub containing all 14 autonomous agents, SCONES memory, AST assimilators, research digests, and verification test suites.
2. **Tier 2 (`DNKOS_APP`)**: A clean, lightweight, standalone client product repository (~30-50 MB) containing only the runnable Next.js 14 Web Command Center (`apps/web`), FastAPI Backend (`apps/api`), Shopify 3.0 engines (`services/dnk_shopify`), and Docker deployment descriptors.

The legacy nested subfolders have been **permanently deprecated and deleted**.

---

## 🛠️ When to Use This Skill
Use this skill whenever:
- The user requests a clean repository/build for client testing, staging, or production deployment.
- Exporting a standalone version to GitHub (e.g. `DNKOS_APP`).
- Preparing a Docker Compose / Vercel / Cloud Run deployment package.

---

## ⚡ Execution Command

To export a fresh, standalone release to a target directory:

```bash
python3 scripts/export_standalone_app.py <target_directory_path>
```

### Example:
```bash
python3 scripts/export_standalone_app.py ../DNKOS_APP_STANDALONE
```

---

## 📦 What Is Packaged in Tier 2 (`DNKOS_APP`):
- `apps/web/` — Next.js 14 Visual Command Center (Canvas V3, Liquid Inspector, Spatial Canvas).
- `apps/api/` — FastAPI High-Velocity REST & WebSocket backend.
- `services/dnk_shopify/` & `services/dnk_shopify_builder/` — Shopify 3.0 Theme Engines.
- `services/dnk_video_ai_creator/` & `services/dnk_canvas_api/` — Microservice adapters.
- `core/` — Kernel & configuration logic.
- `Dockerfile`, `Dockerfile.web`, `Dockerfile.api`, `docker-compose.yml` — Containerization.
- Clean `.env.example` and automatically initialized git repository on `main`.

---

## 🛡️ Invariants:
1. Always run `python3 scripts/system/auto_precommit_guard.py` before running the export to ensure zero syntax or path errors.
2. Never manually copy `DNK_HUB` with `cp -r` — always use `scripts/export_standalone_app.py` to filter out R&D cache, SQLite databases, logs, and internal credentials.

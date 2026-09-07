# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/invokeai/RN-023_invokeai-research.md"
# purpose: "Research Digest & SOTA License/Architecture Audit for InvokeAI Assimilation into DNK OS"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

# 🔬 Research Digest: InvokeAI Assimilation & Engine Audit (RN-023)

## 📌 Executive Summary

This research digest documents the comprehensive technical audit and assimilation pipeline of **InvokeAI** (Source: [invoke-ai/InvokeAI](https://github.com/invoke-ai/InvokeAI) and [invoke.ai/start-here/installation/](https://invoke.ai/start-here/installation/)) into **DNK OS (DBK OS)**.

InvokeAI is a leading open-source creative generative AI engine designed for professionals, studios, and developers. It features a robust Python/FastAPI backend powered by a strongly-typed, DAG-based invocation graph engine, combined with a modular React/Redux/ReactFlow frontend featuring a Unified Canvas and node-based workflows.

---

## ⚖️ License & Intellectual Property Audit

- **Repository**: `invoke-ai/InvokeAI`
- **Core License**: **Apache License 2.0** (Permissive, Commercial-Safe)
- **Assimilation Track**: **Track 1 (Direct Template & Component Assimilation)**
- **Intellectual Property Assessment**:
  - The core engine, graph invoker, REST/WebSocket API, Unified Canvas UI components, and node schemas are 100% compliant for direct adaptation into DNK OS under Apache 2.0.
  - **Notice on Model Weights**: Diffusion model weights (e.g., Stable Diffusion 1.5/2.1, SDXL, SD 3.5, Flux.1, CogView, Wan) carry distinct model licenses (CreativeML OpenRAIL-M, Non-Commercial, or Apache 2.0 depending on the model checkpoint). DNK OS provides isolated model management adapters that respect individual model checkpoints without polluting the core engine codebase.

---

## 🛠️ Installation & Packaging Matrix Audit

Based on the official installation documentation ([invoke.ai/start-here/installation/](https://invoke.ai/start-here/installation/)):

1. **Invoke Launcher (Recommended for Desktop/Studio)**:
   - Standalone installer for macOS, Windows, and Linux.
   - Manages Python virtual environment, dependencies, automatic GPU acceleration detection, model directory configuration, and one-click updates without command-line overhead.
2. **Alternative LynxHub Launcher**:
   - Community launcher offering multi-environment isolation and portable installations.
3. **Manual Python CLI Installation (`pip` / `uv`)**:
   - Requirements: Python 3.10 – 3.12, virtualenv.
   - Hardware backend selection:
     - **NVIDIA GPU**: `torch` with CUDA 12.x / 11.8.
     - **Apple Silicon (Mac M1/M2/M3/M4)**: PyTorch MPS acceleration with unified memory management.
     - **AMD GPU**: ROCm for Linux, DirectML / ONNX Runtime for Windows.
     - **Intel Arc / CPU**: OpenVINO or standard CPU execution.
4. **Containerized / Docker Engine**:
   - Official `Dockerfile` and `docker-compose.yml` supporting NVIDIA Container Toolkit (`--gpus all`) and ROCm drivers.
   - Decoupled persistent volumes for `models`, `outputs`, and `databases` (`invokeai.db`).

---

## 🏗️ Core Architecture & Pattern Deconstruction

InvokeAI architecture consists of four deeply integrated layers:

```
┌──────────────────────────────────────────────────────────────────┐
│                    DNK Unified Visual Canvas UI                  │
│       (React 18 / Redux Toolkit / ReactFlow / Socket.IO)         │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ REST & WebSocket Event Stream
┌────────────────────────────────▼─────────────────────────────────┐
│              FastAPI Application Server & Event Router           │
│      (/api/v1/sessions, /api/v1/images, /api/v1/models, ws)      │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ Invocations & Batches
┌────────────────────────────────▼─────────────────────────────────┐
│               Invoker Engine & Graph Execution Runtime           │
│  ┌───────────────────────┐  ┌──────────────────────────────────┐ │
│  │ ExecutionMaterializer │  │ Class-Batched Invocation Queue   │ │
│  └───────────┬───────────┘  └─────────────────┬────────────────┘ │
│              │                                │                  │
│  ┌───────────▼────────────────────────────────▼────────────────┐ │
│  │ BaseInvocation DAG: Iterate / Collect / Inpaint / Generate   │ │
│  └───────────────────────────┬─────────────────────────────────┘ │
└──────────────────────────────┼───────────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────────┐
│       Model Manager & Acceleration Layer (Diffusers / Safetensors)│
│  (SDXL / Flux / LoRA / ControlNet / IP-Adapter / SAM2 / VAE)     │
└──────────────────────────────────────────────────────────────────┘
```

### 1. Invocations Graph Execution Engine (`GraphExecutionState`)
- All generative and image processing steps are modelled as discrete, typed **Nodes (Invocations)** extending `BaseInvocation`.
- Execution is handled via `Invoker` (`invokeai/app/services/invoker.py`) with support for:
  - **Dynamic Iteration / Collection**: Spawning multiple generation branches from prompt lists or seed ranges and collecting latents.
  - **Session State Snapshots**: Resumable execution graphs with intermediate caching of latents and tensor representations.
  - **Asynchronous Execution Queue**: Priority-based scheduling, progress broadcasting over WebSockets (`generator_progress`, `invocation_complete`).

### 2. Unified Canvas & Composition Pipeline
- Non-destructive infinite canvas supporting layered editing:
  - Inpainting (masked generative fill), Outpainting (bounding box expansion).
  - High-resolution iterative upscaling (ESRGAN, Spandrel, Tiled VAE).
  - Multi-ControlNet and IP-Adapter image prompt composition.
  - Real-time segmentation via Segment Anything (SAM / SAM2).

### 3. Model Management & Storage
- Centralized model hub scanning `.safetensors`, `.ckpt`, `.gguf`, and HuggingFace repositories.
- Dynamic VRAM offloading and precision switching (FP16, BF16, FP8, INT4 quantization).
- Embedded metadata: Every generated image PNG chunk contains complete JSON graph provenance and seed configuration for 100% deterministic reproducibility.

---

## 🚀 DNK OS Assimilation Plan

1. **Architecture Specification**: `DNK-ARCH-023_invokeai-patterns.md` (DAG invoker, unified visual canvas, swarm media generation).
2. **Component Contracts**: `DNK-COMP-023_invokeai-contracts.md` (Typed Python interfaces for Invocation ports and execution states).
3. **Security Standards**: `DNK-SEC-007_invokeai-execution-sandbox.md` (Safetensors enforcement, PyTorch pickle blocks, VRAM allocation guardrails).
4. **Swarm Skill**: `skills/invokeai_assimilated/SKILL.md` (Empowering `dnk_video_ai_creator` and `gerych_builder`).
5. **Core Adapter**: `core/adapters/dnk_invokeai_adapter.py` + unit tests in `core/tests/test_invokeai_assimilation.py`.

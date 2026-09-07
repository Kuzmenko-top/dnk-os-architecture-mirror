# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-023_invokeai-patterns.md"
# purpose: "Architecture & Generative Topology Specifications for InvokeAI Invocations Graph Assimilation"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

# 🏛️ Architecture Specification: InvokeAI Generative Invocations Graph (DNK-ARCH-023)

This specification defines the architectural patterns, DAG execution topologies, and Unified Canvas bridge assimilated from `invoke-ai/InvokeAI` into **DNK OS**.

---

## 📐 Invocations Graph Topology

### 1. Generative Text-to-Image / ControlNet DAG

```
 ┌─────────────────────┐      ┌─────────────────────────┐
 │   Prompt & Model    │      │ ControlNet Image Source │
 └──────────┬──────────┘      └────────────┬────────────┘
            │ UNet / VAE / TextEncoder     │ Depth / Canny / Pose
            ▼                              ▼
 ┌─────────────────────┐      ┌─────────────────────────┐
 │  Positive/Negative  │      │  ControlNet Invocation  │
 │  Conditioning Node  │      │       Processor         │
 └──────────┬──────────┘      └────────────┬────────────┘
            │                              │
            └──────────────┬───────────────┘
                           │ Conditionings
                           ▼
              ┌─────────────────────────┐
              │ Noise Generator (Seed)  │
              └────────────┬────────────┘
                           │ Latents
                           ▼
              ┌─────────────────────────┐
              │ Denoise / KSampler Node │
              └────────────┬────────────┘
                           │ Latents
                           ▼
              ┌─────────────────────────┐
              │ VAE Decode & Metadata   │
              └────────────┬────────────┘
                           │ Output Image with Provenance
                           ▼
              ┌─────────────────────────┐
              │ DNK Canvas Board/Layer  │
              └─────────────────────────┘
```

### 2. Multi-Branch Iterator / Collector Topology

```
                  ┌──────────────────────┐
                  │ Batch Seed Generator │ (e.g. 4 Seeds)
                  └──────────┬───────────┘
                             │
                     Iterator Invocation
                             │
             ┌───────────────┼───────────────┐
             ▼               ▼               ▼
      ┌────────────┐   ┌────────────┐  ┌────────────┐
      │ Branch #1  │   │ Branch #2  │  │ Branch #3  │
      └──────┬─────┘   └─────┬──────┘  └─────┬──────┘
             │               │               │
             └───────────────┼───────────────┘
                             │
                     Collect Invocation
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Composite Grid Tile  │
                  └──────────────────────┘
```

---

## ⚙️ Core Architectural Components

### 1. `DNKInvocationNode` & `DNKInvocationGraph`
- Strongly-typed Pydantic schemas representing operations (e.g., `PromptInvocation`, `DenoiseLatentsInvocation`, `VAEDecodeInvocation`, `InpaintInvocation`).
- Nodes declare input fields, output types, and dependencies forming an acyclic execution graph.

### 2. `DNKGraphExecutionRuntime`
- Asynchronous executor that schedules node evaluation in topological order.
- Supports intermediate tensor/latents caching and state restoration from thread checkpoints.

### 3. `DNKUnifiedCanvasBridge`
- Bridges the generative pipeline with DNK OS Canvas components (`DNK-UI-005` React Flow & `DNK-UI-006` tldraw whiteboard).
- Translates visual canvas bounding boxes, mask layers, and inpainting areas into structured invocation subgraphs.

### 4. `DNKModelManager`
- Dynamic registry managing checkpoints, LoRAs, and ControlNets with on-demand hardware offloading (Apple Silicon MPS / CUDA).

---
name: invokeai_assimilated
description: InvokeAI DAG invocations, Unified Canvas, safetensors sandbox.
category: mlops
---

# 🎨 InvokeAI Assimilated Engine (DNK OS Integration)

## 📌 Overview
Provides standardized generative AI invocation graphs, non-destructive canvas workflows, inpainting, ControlNet pipelines, and multi-branch execution for `dnk_video_ai_creator` and `gerych_builder`.

---

## ⚡ Quick Recipe: Constructing a Generation Graph

```python
from core.adapters.dnk_invokeai_adapter import (
    DNKInvokeAIAdapter,
    InvocationNodeDTO,
    InvocationEdgeDTO,
    GenerationGraphDTO,
)

# 1. Initialize Adapter
adapter = DNKInvokeAIAdapter()

# 2. Build Generation Graph
graph = GenerationGraphDTO(
    graph_id="gen_flux_portrait_001",
    nodes={
        "prompt": InvocationNodeDTO(
            id="prompt",
            type="prompt_node",
            inputs={"positive": "Cybernetic studio portrait, volumetric lighting, 8k"},
        ),
        "noise": InvocationNodeDTO(
            id="noise",
            type="noise_node",
            inputs={"seed": 4242, "width": 1024, "height": 1024},
        ),
        "denoise": InvocationNodeDTO(
            id="denoise",
            type="denoise_latents_node",
            inputs={"steps": 25, "cfg_scale": 7.5},
        ),
        "vae_decode": InvocationNodeDTO(
            id="vae_decode",
            type="vae_decode_node",
            inputs={},
        ),
    },
    edges=[
        InvocationEdgeDTO(
            source_node_id="prompt",
            source_field="conditioning",
            target_node_id="denoise",
            target_field="conditioning",
        ),
        InvocationEdgeDTO(
            source_node_id="noise",
            source_field="latents",
            target_node_id="denoise",
            target_field="latents",
        ),
        InvocationEdgeDTO(
            source_node_id="denoise",
            source_field="latents",
            target_node_id="vae_decode",
            target_field="latents",
        ),
    ],
)

# 3. Execute Graph
results = adapter.execute_graph(graph, session_id="session_001")
print(f"Generated Image: {results['vae_decode']['image_name']}")
```

---

## 🛡️ Security & Performance Invariants
1. Enforce `.safetensors` model formats only.
2. Maintain VRAM bounds using tiled VAE and dynamic sequential offloading.
3. Save full JSON graph provenance inside output PNG metadata.

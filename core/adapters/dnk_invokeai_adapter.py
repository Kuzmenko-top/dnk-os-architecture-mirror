# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/dnk_invokeai_adapter.py"
# purpose: "Hexagonal Port & Adapter for InvokeAI Generative Invocations DAG & Unified Canvas Engine"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, deque
from pydantic import BaseModel, Field

logger = logging.getLogger("DNKInvokeAIAdapter")


class ImageFieldDTO(BaseModel):
    """Reference to an image asset with dimensions and storage URI."""
    image_name: str
    image_url: Optional[str] = None
    width: int = 512
    height: int = 512
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LatentsFieldDTO(BaseModel):
    """Reference to cached or generated tensor latents."""
    latents_name: str
    seed: int
    width: int = 512
    height: int = 512


class InvocationNodeDTO(BaseModel):
    """Discrete node in the generation graph."""
    id: str
    type: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, executing, completed, failed


class InvocationEdgeDTO(BaseModel):
    """Directed connection between node output and node input."""
    source_node_id: str
    source_field: str
    target_node_id: str
    target_field: str


class GenerationGraphDTO(BaseModel):
    """Complete invocations DAG payload."""
    graph_id: str
    nodes: Dict[str, InvocationNodeDTO] = Field(default_factory=dict)
    edges: List[InvocationEdgeDTO] = Field(default_factory=list)


class DNKInvokeAIAdapter:
    """
    Adapter implementing the InvokeAI DAG Invocation Engine and Unified Canvas Bridge.
    Executes generative graphs in topological order with metadata provenance.
    """

    def __init__(self, output_dir: str = "outputs/generations"):
        self.output_dir = output_dir
        self.models_registry: Dict[str, Dict[str, Any]] = {
            "flux_dev": {
                "name": "FLUX.1-dev",
                "format": "safetensors",
                "type": "main",
                "base": "flux",
                "hash": "sha256:fluxdev001",
            },
            "sdxl_base": {
                "name": "SDXL Base 1.0",
                "format": "safetensors",
                "type": "main",
                "base": "sdxl",
                "hash": "sha256:sdxlbase001",
            },
            "canny_controlnet": {
                "name": "ControlNet Canny SDXL",
                "format": "safetensors",
                "type": "controlnet",
                "base": "sdxl",
                "hash": "sha256:cannycontrolnet001",
            },
        }

    def list_models(self) -> List[Dict[str, Any]]:
        """List registered diffusion models and adapters."""
        return list(self.models_registry.values())

    def register_model(self, model_key: str, model_info: Dict[str, Any]) -> None:
        """Register a new safetensors model into the registry."""
        if not model_info.get("format", "").lower() == "safetensors":
            raise ValueError("Security Violation: Only .safetensors model formats are permitted.")
        self.models_registry[model_key] = model_info

    def _topological_sort(self, graph: GenerationGraphDTO) -> List[str]:
        """Compute execution order for DAG nodes."""
        in_degree: Dict[str, int] = {node_id: 0 for node_id in graph.nodes}
        adj_list: Dict[str, List[str]] = defaultdict(list)

        for edge in graph.edges:
            if edge.source_node_id in graph.nodes and edge.target_node_id in graph.nodes:
                adj_list[edge.source_node_id].append(edge.target_node_id)
                in_degree[edge.target_node_id] += 1

        queue = deque([node_id for node_id, deg in in_degree.items() if deg == 0])
        order: List[str] = []

        while queue:
            curr = queue.popleft()
            order.append(curr)
            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(graph.nodes):
            raise ValueError("Cyclic dependency detected in GenerationGraph DAG.")

        return order

    def execute_node(self, node: InvocationNodeDTO, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute discrete invocation node logic."""
        node_type = node.type
        inputs = node.inputs

        if node_type == "prompt_node":
            positive = inputs.get("positive", "")
            negative = inputs.get("negative", "")
            return {
                "conditioning": {
                    "positive_prompt": positive,
                    "negative_prompt": negative,
                    "clip_embeddings_id": f"clip_{hashlib.md5(positive.encode()).hexdigest()[:8]}",
                }
            }

        elif node_type == "noise_node":
            seed = inputs.get("seed", 42)
            width = inputs.get("width", 512)
            height = inputs.get("height", 512)
            latents_id = f"latents_{seed}_{width}x{height}"
            return {
                "latents": LatentsFieldDTO(
                    latents_name=latents_id,
                    seed=seed,
                    width=width,
                    height=height,
                ).model_dump()
            }

        elif node_type == "denoise_latents_node":
            conditioning = inputs.get("conditioning", {})
            latents = inputs.get("latents", {})
            steps = inputs.get("steps", 20)
            cfg_scale = inputs.get("cfg_scale", 7.5)
            seed = latents.get("seed", 42) if isinstance(latents, dict) else 42
            denoised_id = f"denoised_{seed}_steps{steps}_cfg{cfg_scale}"
            return {
                "latents": {
                    "latents_name": denoised_id,
                    "seed": seed,
                    "steps": steps,
                    "cfg_scale": cfg_scale,
                    "conditioning": conditioning,
                }
            }

        elif node_type == "vae_decode_node":
            latents = inputs.get("latents", {})
            seed = latents.get("seed", 42) if isinstance(latents, dict) else 42
            img_id = f"invoke_img_{seed}_{hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:8]}.png"
            return {
                "image": ImageFieldDTO(
                    image_name=img_id,
                    image_url=f"/outputs/{img_id}",
                    width=latents.get("width", 512) if isinstance(latents, dict) else 512,
                    height=latents.get("height", 512) if isinstance(latents, dict) else 512,
                    metadata={"provenance_graph": context.get("graph_id", "unknown"), "seed": seed},
                ).model_dump()
            }

        elif node_type == "controlnet_node":
            image = inputs.get("image", {})
            control_mode = inputs.get("control_mode", "canny")
            weight = inputs.get("weight", 1.0)
            return {
                "control_conditioning": {
                    "source_image": image,
                    "control_mode": control_mode,
                    "weight": weight,
                }
            }

        elif node_type == "iterate_node":
            items = inputs.get("items", [])
            return {"iterator": items}

        elif node_type == "collect_node":
            collected_items = inputs.get("items", [])
            return {"collection": collected_items}

        else:
            # Generic fallback
            return {"status": "executed", "echo_inputs": inputs}

    def execute_graph(self, graph: GenerationGraphDTO, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute generation graph in topological order and route data along edges."""
        order = self._topological_sort(graph)
        node_outputs: Dict[str, Dict[str, Any]] = {}
        context = {"graph_id": graph.graph_id, "session_id": session_id or "default_session"}

        for node_id in order:
            node = graph.nodes[node_id]
            node.status = "executing"

            # Resolve incoming edges into inputs
            resolved_inputs = dict(node.inputs)
            for edge in graph.edges:
                if edge.target_node_id == node_id:
                    source_out = node_outputs.get(edge.source_node_id, {})
                    if edge.source_field in source_out:
                        resolved_inputs[edge.target_field] = source_out[edge.source_field]

            node.inputs = resolved_inputs
            outputs = self.execute_node(node, context)
            node.outputs = outputs
            node.status = "completed"
            node_outputs[node_id] = outputs

        return node_outputs

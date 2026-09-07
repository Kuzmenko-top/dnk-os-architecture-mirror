# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_invokeai_assimilation.py"
# purpose: "Unit & Integration Test Suite for Assimilated InvokeAI Generative Invocations DAG & Adapter"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

import pytest
from core.adapters.dnk_invokeai_adapter import (
    DNKInvokeAIAdapter,
    InvocationNodeDTO,
    InvocationEdgeDTO,
    GenerationGraphDTO,
    ImageFieldDTO,
    LatentsFieldDTO,
)


def test_invokeai_model_registry_and_safetensors_guard():
    adapter = DNKInvokeAIAdapter()
    models = adapter.list_models()
    assert len(models) >= 2
    assert any(m["base"] == "flux" for m in models)

    # Valid safetensors registration
    adapter.register_model("custom_lora", {
        "name": "Cinematic LoRA",
        "format": "safetensors",
        "type": "lora",
        "base": "flux",
    })
    assert len(adapter.list_models()) == 4

    # Security rejection for unsafe pickle formats
    with pytest.raises(ValueError, match="Security Violation"):
        adapter.register_model("unsafe_ckpt", {
            "name": "Legacy Checkpoint",
            "format": "ckpt",
            "type": "main",
        })


def test_invokeai_generation_graph_topological_execution():
    adapter = DNKInvokeAIAdapter()

    graph = GenerationGraphDTO(
        graph_id="test_dag_portrait_001",
        nodes={
            "prompt": InvocationNodeDTO(
                id="prompt",
                type="prompt_node",
                inputs={"positive": "Modern architectural glass pavilion in forest, photorealistic"},
            ),
            "noise": InvocationNodeDTO(
                id="noise",
                type="noise_node",
                inputs={"seed": 1337, "width": 1024, "height": 1024},
            ),
            "denoise": InvocationNodeDTO(
                id="denoise",
                type="denoise_latents_node",
                inputs={"steps": 30, "cfg_scale": 8.0},
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

    results = adapter.execute_graph(graph, session_id="test_sess_01")

    # Validate output pipeline
    assert "prompt" in results
    assert "conditioning" in results["prompt"]
    assert "noise" in results
    assert results["noise"]["latents"]["seed"] == 1337
    assert "denoise" in results
    assert results["denoise"]["latents"]["steps"] == 30
    assert "vae_decode" in results
    assert "image" in results["vae_decode"]

    image_dto = results["vae_decode"]["image"]
    assert image_dto["image_name"].startswith("invoke_img_1337_")
    assert image_dto["metadata"]["provenance_graph"] == "test_dag_portrait_001"
    assert image_dto["metadata"]["seed"] == 1337


def test_invokeai_cyclic_graph_detection():
    adapter = DNKInvokeAIAdapter()

    # Graph with cycle: node_a -> node_b -> node_a
    graph = GenerationGraphDTO(
        graph_id="cycle_graph",
        nodes={
            "node_a": InvocationNodeDTO(id="node_a", type="prompt_node"),
            "node_b": InvocationNodeDTO(id="node_b", type="prompt_node"),
        },
        edges=[
            InvocationEdgeDTO(source_node_id="node_a", source_field="out", target_node_id="node_b", target_field="in"),
            InvocationEdgeDTO(source_node_id="node_b", source_field="out", target_node_id="node_a", target_field="in"),
        ],
    )

    with pytest.raises(ValueError, match="Cyclic dependency detected"):
        adapter.execute_graph(graph)

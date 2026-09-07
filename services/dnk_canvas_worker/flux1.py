# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_canvas_worker/flux1.py"
# purpose: "FLUX.1 + LayerDiffuse isolated layer generation adapter for canvas background workers."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym & Gerych"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Optional, Dict, Any
from ..dnk_canvas_api.ai_models import flux_layerdiffuse_client, CanvasGenerateLayerRequest

logger = logging.getLogger("dnk_canvas_worker.flux1")

class Flux1Adapter:
    """
    Adapter for FLUX.1 + LayerDiffuse isolated layer generation.
    Integrates directly with the dnk_canvas_api AI model layers
    to generate high-fidelity, isolated e-commerce assets inside background work execution tasks.
    """

    def __init__(self, client=None):
        self.client = client or flux_layerdiffuse_client

    async def execute_generate_layer(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        style: Optional[str] = "photorealistic",
        width: int = 1024,
        height: int = 1024,
        transparent_background: bool = True,
        layer_type: str = "image",
        canvas_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes transparent/isolated layer generation via FluxLayerDiffuseClient.
        """
        logger.info(f"Executing FLUX.1 generation for canvas_id: {canvas_id}, prompt: {prompt}")
        
        try:
            result = await self.client.generate_layer(
                prompt=prompt,
                negative_prompt=negative_prompt,
                style=style,
                width=width,
                height=height,
                transparent=transparent_background,
                layer_type=layer_type,
                **(options or {})
            )
            return {
                "success": True,
                "image_base64": result.get("image_base64"),
                "layer_data": result.get("layer_data", {}),
                "execution_time_ms": result.get("execution_time_ms", 0.0),
                "model": result.get("model", "FLUX.1-LayerDiffuse"),
                "metadata": {
                    "canvas_id": canvas_id,
                    "prompt": prompt,
                    "style": style,
                    "transparent": transparent_background,
                    "source": result.get("source", "worker_adapter")
                }
            }
        except Exception as e:
            logger.error(f"FLUX.1 generation execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

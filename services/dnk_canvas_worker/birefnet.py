# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_canvas_worker/birefnet.py"
# purpose: "BiRefNet background removal adapter for canvas background workers."
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
from typing import Optional, Dict, Any, Union
from ..dnk_canvas_api.ai_models import birefnet_client, CanvasCutoutRequest

logger = logging.getLogger("dnk_canvas_worker.birefnet")

class BiRefNetAdapter:
    """
    Adapter for BiRefNet background removal.
    Integrates directly with the dnk_canvas_api AI model layers
    to provide background removal capabilities inside background work execution tasks.
    """

    def __init__(self, client=None):
        self.client = client or birefnet_client

    async def execute_cutout(
        self,
        image_data: Union[str, bytes],
        return_mask: bool = False,
        threshold: float = 0.5,
        node_id: Optional[str] = None,
        canvas_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes background removal via BiRefNetClient.
        Accepts raw image base64, data URLs, or image URLs, and returns cutout data.
        """
        logger.info(f"Executing BiRefNet background cutout for node_id: {node_id}, canvas_id: {canvas_id}")
        
        try:
            result = await self.client.cutout_background(
                image_data=image_data,
                return_mask=return_mask,
                threshold=threshold,
                **(options or {})
            )
            return {
                "success": True,
                "image_base64": result.get("image_base64"),
                "mask_base64": result.get("mask_base64"),
                "node_id": node_id,
                "execution_time_ms": result.get("execution_time_ms", 0.0),
                "model": result.get("model", "BiRefNet-v1"),
                "metadata": {
                    "canvas_id": canvas_id,
                    "source": result.get("source", "worker_adapter")
                }
            }
        except Exception as e:
            logger.error(f"BiRefNet cutout execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "node_id": node_id
            }

# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_canvas_worker/iclight.py"
# purpose: "IC-Light image relighting and harmonization adapter for canvas background workers."
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
from ..dnk_canvas_api.ai_models import iclight_client, CanvasRelightRequest

logger = logging.getLogger("dnk_canvas_worker.iclight")

class ICLightAdapter:
    """
    Adapter for IC-Light image relighting.
    Integrates directly with the dnk_canvas_api AI model layers
    to provide environment lighting harmonization inside background work execution tasks.
    """

    def __init__(self, client=None):
        self.client = client or iclight_client

    async def execute_relight(
        self,
        foreground: Union[str, bytes],
        background: Optional[Union[str, bytes]] = None,
        lighting_prompt: Optional[str] = None,
        light_direction: str = "natural",
        intensity: float = 1.0,
        foreground_node_id: Optional[str] = None,
        background_node_id: Optional[str] = None,
        canvas_id: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes ambient lighting harmonization via ICLightClient.
        """
        logger.info(f"Executing IC-Light relighting for foreground node: {foreground_node_id}, canvas_id: {canvas_id}")
        
        try:
            result = await self.client.relight(
                foreground=foreground,
                background=background,
                lighting_prompt=lighting_prompt,
                light_direction=light_direction,
                intensity=intensity,
                **(options or {})
            )
            return {
                "success": True,
                "image_base64": result.get("image_base64"),
                "node_id": foreground_node_id,
                "execution_time_ms": result.get("execution_time_ms", 0.0),
                "model": result.get("model", "IC-Light-v1"),
                "metadata": {
                    "canvas_id": canvas_id,
                    "light_direction": light_direction,
                    "intensity": intensity,
                    "background_node_id": background_node_id,
                    "source": result.get("source", "worker_adapter")
                }
            }
        except Exception as e:
            logger.error(f"IC-Light relighting execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "node_id": foreground_node_id
            }

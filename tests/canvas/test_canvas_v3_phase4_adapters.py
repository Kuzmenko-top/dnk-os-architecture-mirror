# --- DNK-MRH-HEADER ---
# mrh_id: "tests/canvas/test_canvas_v3_phase4_adapters.py"
# purpose: "Unit tests for Phase 4 Photo Studio adapters (BiRefNet, IC-Light, FLUX.1 + LayerDiffuse)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import asyncio
from services.dnk_canvas_worker.birefnet import BiRefNetAdapter
from services.dnk_canvas_worker.iclight import ICLightAdapter
from services.dnk_canvas_worker.flux1 import Flux1Adapter

# 1x1 transparent PNG in base64
MOCK_PNG_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

@pytest.mark.asyncio
async def test_birefnet_adapter_execute():
    adapter = BiRefNetAdapter()
    result = await adapter.execute_cutout(image_data=MOCK_PNG_B64, threshold=0.45)
    
    assert result is not None
    assert result["success"] is True
    assert "image_base64" in result
    assert "mask_base64" in result
    assert result["image_base64"].startswith("data:image/") or len(result["image_base64"]) > 0

@pytest.mark.asyncio
async def test_iclight_adapter_execute():
    adapter = ICLightAdapter()
    result = await adapter.execute_relight(
        foreground=MOCK_PNG_B64,
        background=MOCK_PNG_B64,
        lighting_prompt="neon dark synthwave style",
        light_direction="left"
    )
    
    assert result is not None
    assert result["success"] is True
    assert "image_base64" in result
    assert result["image_base64"].startswith("data:image/") or len(result["image_base64"]) > 0

@pytest.mark.asyncio
async def test_flux1_adapter_execute():
    adapter = Flux1Adapter()
    result = await adapter.execute_generate_layer(
        prompt="high-end product packaging bottle, realistic shadows",
        transparent_background=True,
        style="commercial"
    )
    
    assert result is not None
    assert result["success"] is True
    assert "image_base64" in result
    assert "layer_data" in result
    assert result["image_base64"].startswith("data:image/") or len(result["image_base64"]) > 0

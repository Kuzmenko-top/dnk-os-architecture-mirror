# --- DNK-MRH-HEADER ---
# mrh_id: "tests/canvas/test_canvas_ai_actions.py"
# purpose: "Comprehensive test suite for Canvas Engine AI Action Adapters: BiRefNet, IC-Light, and FLUX.1 + LayerDiffuse clients and FastAPI gateway endpoints."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Gerych"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import pytest
import base64
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from services.dnk_canvas_api.main import app
from services.dnk_canvas_api.ai_models import (
    BiRefNetClient,
    ICLightClient,
    FluxLayerDiffuseClient,
    normalize_to_base64,
    format_data_url,
    TINY_TRANSPARENT_PNG_BASE64,
    TINY_WHITE_PNG_BASE64,
)

SAMPLE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
SAMPLE_B64 = base64.b64encode(SAMPLE_IMAGE_BYTES).decode("utf-8")
SAMPLE_DATA_URL = f"data:image/png;base64,{SAMPLE_B64}"

AUTH_HEADERS = {
    "X-Workspace-Id": "ws-test-ai",
    "Authorization": "Bearer ws-test-ai:user-tester"
}


# =====================================================================
# Unit Tests: Base64 & Format Utilities
# =====================================================================

def test_normalize_to_base64_from_bytes():
    result = normalize_to_base64(SAMPLE_IMAGE_BYTES)
    assert result == SAMPLE_B64


def test_normalize_to_base64_from_data_url():
    result = normalize_to_base64(SAMPLE_DATA_URL)
    assert result == SAMPLE_B64


def test_normalize_to_base64_from_plain_str():
    result = normalize_to_base64(SAMPLE_B64)
    assert result == SAMPLE_B64


def test_format_data_url():
    formatted = format_data_url(SAMPLE_B64, "image/png")
    assert formatted.startswith("data:image/png;base64,")
    already_formatted = format_data_url(SAMPLE_DATA_URL)
    assert already_formatted == SAMPLE_DATA_URL


# =====================================================================
# Unit Tests: BiRefNetClient
# =====================================================================

@pytest.mark.asyncio
async def test_birefnet_client_mock_fallback():
    client = BiRefNetClient(endpoint_url="https://invalid-url.mock", timeout=0.1, max_retries=0)
    result = await client.cutout_background(image_data=SAMPLE_B64, return_mask=True, threshold=0.6)
    assert "image_base64" in result
    assert result["mask_base64"] is not None
    assert result["source"] == "local_fallback"
    assert result["threshold"] == 0.6


@pytest.mark.asyncio
async def test_birefnet_client_with_bytes():
    client = BiRefNetClient(endpoint_url="https://invalid-url.mock", timeout=0.1, max_retries=0)
    result = await client.cutout_background(image_data=SAMPLE_IMAGE_BYTES, return_mask=False)
    assert "image_base64" in result
    assert result["mask_base64"] is None


@pytest.mark.asyncio
async def test_birefnet_client_remote_success():
    client = BiRefNetClient(endpoint_url="https://api.test/ai/birefnet", api_key="secret-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "image": SAMPLE_B64,
        "mask": TINY_WHITE_PNG_BASE64
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await client.cutout_background(image_data=SAMPLE_B64, return_mask=True)
        assert result["source"] == "remote_api"
        assert result["image_base64"] == SAMPLE_B64
        assert result["mask_base64"] == TINY_WHITE_PNG_BASE64
        assert result["model"] == "BiRefNet-v1"


# =====================================================================
# Unit Tests: ICLightClient
# =====================================================================

@pytest.mark.asyncio
async def test_iclight_client_mock_fallback():
    client = ICLightClient(endpoint_url="https://invalid-url.mock", timeout=0.1, max_retries=0)
    result = await client.relight(
        foreground=SAMPLE_B64,
        background=SAMPLE_B64,
        lighting_prompt="dramatic side light",
        light_direction="left",
        intensity=1.5
    )
    assert "image_base64" in result
    assert result["source"] == "local_fallback"
    assert result["light_direction"] == "left"
    assert result["intensity"] == 1.5


@pytest.mark.asyncio
async def test_iclight_client_remote_success():
    client = ICLightClient(endpoint_url="https://api.test/ai/ic-light", api_key="secret-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "image": SAMPLE_B64
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await client.relight(
            foreground=SAMPLE_B64,
            background=SAMPLE_B64,
            lighting_prompt="golden hour"
        )
        assert result["source"] == "remote_api"
        assert result["image_base64"] == SAMPLE_B64
        assert result["model"] == "IC-Light-v1"


# =====================================================================
# Unit Tests: FluxLayerDiffuseClient
# =====================================================================

@pytest.mark.asyncio
async def test_flux_layerdiffuse_mock_fallback():
    client = FluxLayerDiffuseClient(endpoint_url="https://invalid-url.mock", timeout=0.1, max_retries=0)
    result = await client.generate_layer(
        prompt="neon glowing sneaker floating in mid-air",
        style="cyberpunk",
        width=512,
        height=512,
        transparent=True
    )
    assert "image_base64" in result
    assert "layer_data" in result
    assert result["source"] == "local_fallback"
    assert result["layer_data"]["width"] == 512
    assert result["layer_data"]["height"] == 512
    assert result["prompt"] == "neon glowing sneaker floating in mid-air"


@pytest.mark.asyncio
async def test_flux_layerdiffuse_remote_success():
    client = FluxLayerDiffuseClient(endpoint_url="https://api.test/ai/flux", api_key="secret-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "image": SAMPLE_B64,
        "layer_data": {"type": "image", "width": 1024, "height": 1024, "name": "Remote Layer"}
    }

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        result = await client.generate_layer(
            prompt="modern minimalist chair",
            style="photorealistic"
        )
        assert result["source"] == "remote_api"
        assert result["image_base64"] == SAMPLE_B64
        assert result["layer_data"]["name"] == "Remote Layer"


# =====================================================================
# Integration Tests: FastAPI Gateway Endpoints
# =====================================================================

client = TestClient(app)


def test_api_cutout_success():
    payload = {
        "image_base64": SAMPLE_DATA_URL,
        "node_id": "node-img-123",
        "canvas_id": "canvas-777",
        "return_mask": True,
        "threshold": 0.55
    }
    response = client.post("/api/v1/canvas/ai/cutout", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "image_base64" in data
    assert data["node_id"] == "node-img-123"
    assert data["metadata"]["canvas_id"] == "canvas-777"


def test_api_cutout_missing_image():
    payload = {
        "node_id": "node-img-123"
    }
    response = client.post("/api/v1/canvas/ai/cutout", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 422


def test_api_cutout_unauthorized():
    payload = {
        "image_base64": SAMPLE_DATA_URL
    }
    response = client.post("/api/v1/canvas/ai/cutout", json=payload)
    assert response.status_code == 401


def test_api_relight_success():
    payload = {
        "foreground_base64": SAMPLE_DATA_URL,
        "background_base64": SAMPLE_DATA_URL,
        "foreground_node_id": "fg-node-1",
        "background_node_id": "bg-node-2",
        "lighting_prompt": "sunset warm glow",
        "light_direction": "right",
        "intensity": 1.2,
        "canvas_id": "canvas-888"
    }
    response = client.post("/api/v1/canvas/ai/relight", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "image_base64" in data
    assert data["node_id"] == "fg-node-1"
    assert data["metadata"]["light_direction"] == "right"
    assert data["metadata"]["intensity"] == 1.2


def test_api_relight_missing_foreground():
    payload = {
        "lighting_prompt": "sunset"
    }
    response = client.post("/api/v1/canvas/ai/relight", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 422


def test_api_generate_layer_success():
    payload = {
        "prompt": "organic green leaf with water drops",
        "style": "photorealistic",
        "width": 800,
        "height": 600,
        "transparent_background": True,
        "layer_type": "image",
        "canvas_id": "canvas-999"
    }
    response = client.post("/api/v1/canvas/ai/generate-layer", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "image_base64" in data
    assert "layer_data" in data
    assert data["metadata"]["prompt"] == "organic green leaf with water drops"
    assert data["metadata"]["style"] == "photorealistic"


def test_api_generate_layer_empty_prompt():
    payload = {
        "prompt": "   ",
        "style": "photorealistic"
    }
    response = client.post("/api/v1/canvas/ai/generate-layer", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 422

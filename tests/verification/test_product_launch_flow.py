# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_product_launch_flow.py"
# purpose: "Automated test suite verifying the One-Click Product Launch Multi-Agent Pipeline (CMO + Shopify + Video AI + CFO)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import pytest
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
MVP_PATH = HUB_ROOT
if str(MVP_PATH) not in sys.path:
    sys.path.insert(0, str(MVP_PATH))

from core.flows.product_launch_flow import (
    product_launch_pipeline,
    ProductLaunchInput,
    ProductLaunchResult,
)


@pytest.mark.asyncio
async def test_product_launch_pipeline_execution():
    payload = ProductLaunchInput(
        product_name="DNK Ergonomic Smart Chair",
        target_audience="Software Engineers & Tech Founders",
        price_usd=599.0,
        cost_usd=199.0,
        key_features=["Adaptive Lumbar Support", "Carbon Fiber Frame", "Autonomous Posture Sensing"],
        workspace_id="ws-alpha-001",
    )

    result = await product_launch_pipeline.execute(payload)

    # 1. Pipeline contract assertions
    assert isinstance(result, ProductLaunchResult)
    assert result.success is True
    assert result.product_name == "DNK Ergonomic Smart Chair"
    assert result.workspace_id == "ws-alpha-001"

    # 2. Marketing CMO assertions
    assert "Software Engineers" in result.marketing.hook or "Tech Founders" in result.marketing.hook
    assert len(result.marketing.pain_points) >= 3
    assert len(result.marketing.ad_copies) >= 2

    # 3. Shopify Liquid assertions
    assert "dnk-pdp-container" in result.shopify.liquid_code
    assert "$599.00" in result.shopify.liquid_code
    assert "Adaptive Lumbar Support" in result.shopify.liquid_code
    assert "liquid_schema" in result.shopify.model_dump()

    # 4. Video AI Remotion assertions
    assert result.video_ai.aspect_ratio == "9:16"
    assert "AbsoluteFill" in result.video_ai.remotion_tsx_code
    assert "$599.00" in result.video_ai.remotion_tsx_code

    # 5. Financial CFO assertions
    assert result.financials.retail_price == 599.0
    assert result.financials.cogs == 199.0
    assert result.financials.gross_profit_per_unit == 400.0
    assert result.financials.gross_margin_pct == 66.78
    assert result.financials.break_even_roas == 1.50
    assert result.financials.recommended_target_cpa == 160.0
    assert result.financials.projected_profit_100_orders == 24000.0

    # 6. Timeline Events
    assert len(result.timeline_events) == 8  # 4 agents x 2 states (RUNNING + DONE)
    agents_logged = {e["agent"] for e in result.timeline_events}
    assert agents_logged == {"dnk_marketing_cmo", "dnk_shopify", "dnk_video_ai_creator", "dnk_finance_cfo"}


def test_native_hermes_tool_bridge():
    from core.hermes_agent.tools.dnk_product_launch_tool import (
        dnk_one_click_product_launch,
        get_product_launch_schemas,
    )

    schemas = get_product_launch_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "dnk_one_click_product_launch"

    raw_res = dnk_one_click_product_launch(
        product_name="DNK Smart Lamp",
        target_audience="Designers",
        price_usd=120.0,
        cost_usd=30.0,
        key_features_csv="Auto-Dimming, USB-C Hub, Aluminum Body",
    )
    res = json.loads(raw_res)
    assert res["success"] is True
    assert res["product_name"] == "DNK Smart Lamp"
    assert res["financials"]["gross_profit_per_unit"] == 90.0

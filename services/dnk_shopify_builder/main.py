# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_shopify_builder/main.py"
# purpose: "Production entrypoint and FastAPI router for dnk_shopify_builder microservice."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Imports of local modules
from services.dnk_shopify_builder.cart_drawer.engine import generate_cart_drawer_assets
from services.dnk_shopify_builder.bundles.engine import generate_pdp_bundles_assets

app = FastAPI(
    title="Shopify Builder Microservice",
    description="Microservice for automated Liquid theme section generation & optimization in DNK OS",
    version="1.0.0"
)

# 1. Base Request Models
class BuildRequest(BaseModel):
    section_name: str
    settings: Dict[str, Any] = {}
    components: List[str] = []

# 2. Commerce Suite Request Models
class CartDrawerRequest(BaseModel):
    free_shipping_threshold: float = Field(..., description="Target cost for free shipping")
    current_cart_total: float = Field(..., description="Current value of items in user's cart")

class BundlesRequest(BaseModel):
    product_id: str = Field(..., description="Main PDP product ID")
    buy_together_products: List[str] = Field(default_factory=list, description="IDs of products to buy together")
    discount_percentage: float = Field(..., description="Discount rate on the total bundle pack")


@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    """Liveness probe."""
    return {"status": "healthy", "service_id": "dnk_shopify_builder"}

@app.get("/api/v1/canvas/node")
def get_canvas_node():
    """Returns the visual canvas node representation for visual monitoring."""
    return {
        "id": "dnk_shopify_builder",
        "name": "Shopify Builder Microservice",
        "type": "AgentNode",
        "state": "Done",
        "indicator": "🟢 Done",
        "metadata": {
          "port": 8081,
          "domain": "shopify",
          "version": "1.0.0"
        }
    }

@app.post("/api/v1/build")
def build_theme_section(req: BuildRequest):
    """Generates Shopify Liquid and JSON schema for modular PDP sections."""
    if not req.section_name:
        raise HTTPException(status_code=400, detail="section_name is required")
        
    # Generate mock high-quality Liquid code
    liquid_code = f"""<!--
  DNK OS Generated Section: {req.section_name}
  Automatically synthesized by Shopify Builder Microservice
-->
<section id="dnk-section-{{{{ section.id }}}}" class="dnk-shopify-section">
  <div class="container">
    <h2 class="section-title">{{{{ section.settings.title | default: "{req.section_name}" }}}}</h2>
    <div class="dnk-grid">
      {" ".join(f'<div class="dnk-component">{comp}</div>' for comp in req.components)}
    </div>
  </div>
</section>

{{% schema %}}
{{{{
  "name": "{req.section_name}",
  "settings": [
    {{{{
      "type": "text",
      "id": "title",
      "label": "Section Title",
      "default": "{req.section_name}"
    }}}}
  ]
}}}}
{{% endschema %}}
"""
    return {
        "status": "success",
        "section_name": req.section_name,
        "liquid": liquid_code,
        "metadata": {
            "generator": "dnk_shopify_builder",
            "version": "1.0.0"
        }
    }

# 3. New commerce suite endpoints
@app.post("/api/v1/cart-drawer/generate")
def generate_cart_drawer(req: CartDrawerRequest):
    """Generates Liquid & AJAX JS assets for the checkout Cart Drawer."""
    if req.free_shipping_threshold < 0 or req.current_cart_total < 0:
        raise HTTPException(status_code=400, detail="Threshold and cart total must be positive numbers")
        
    return generate_cart_drawer_assets(
        free_shipping_threshold=req.free_shipping_threshold,
        current_cart_total=req.current_cart_total
    )

@app.post("/api/v1/bundles/generate")
def generate_pdp_bundles(req: BundlesRequest):
    """Generates Liquid, CSS & JS for Frequently Bought Together blocks."""
    if not req.product_id:
        raise HTTPException(status_code=400, detail="product_id is required")
    if req.discount_percentage < 0 or req.discount_percentage > 100:
        raise HTTPException(status_code=400, detail="discount_percentage must be between 0 and 100")
        
    return generate_pdp_bundles_assets(
        product_id=req.product_id,
        buy_together_products=req.buy_together_products,
        discount_percentage=req.discount_percentage
    )

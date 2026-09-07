# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/brick_04_shopify_engine/contracts/schemas.py"
# purpose: "Pydantic contract schemas for Brick 04: Shopify 3.0 Engine & Liquid AST Transpiler."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ShopifySection(BaseModel):
    id: str
    type: str
    settings: Dict[str, Any] = Field(default_factory=dict)
    blocks: Dict[str, Any] = Field(default_factory=dict)
    block_order: List[str] = Field(default_factory=list)


class ShopifyTemplateState(BaseModel):
    name: str
    layout: str = "theme.liquid"
    sections: Dict[str, ShopifySection] = Field(default_factory=dict)
    order: List[str] = Field(default_factory=list)


class BuildThemeRequest(BaseModel):
    store_domain: str
    theme_name: str = "DNK-OS-Theme"
    environment: str = "production"

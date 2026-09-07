# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/liquid_block_generator.py"
# purpose: "Generative UI Engine for Shopify Theme App Extensions & Liquid Blocks."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class LiquidBlockSpec(BaseModel):
    name: str
    block_type: str  # "upsell_banner", "loyalty_widget", "product_recommendations"
    schema_fields: List[Dict[str, Any]] = Field(default_factory=list)
    template: Optional[str] = None
    target: str = "section"


class LiquidBlockGenerator:
    """
    Generative UI Engine for synthesizing production-ready Shopify Liquid App Blocks
    and accompanying JSON schemas for Theme App Extensions.
    """

    def __init__(self):
        self.templates = {
            "upsell_banner": self._generate_upsell_banner,
            "loyalty_widget": self._generate_loyalty_widget,
            "product_recommendations": self._generate_product_recommendations,
        }

    def generate(self, spec: LiquidBlockSpec) -> Dict[str, Any]:
        """
        Generate Liquid code and schema JSON based on specification.
        """
        generator_func = self.templates.get(spec.block_type, self._generate_generic_block)
        rendered_template = generator_func(spec)
        schema_dict = self._generate_schema(spec)

        return {
            "liquid_file": f"{spec.name}.liquid",
            "schema_file": f"{spec.name}.json",
            "template": rendered_template,
            "schema": schema_dict,
        }

    def _generate_upsell_banner(self, spec: LiquidBlockSpec) -> str:
        return f"""{{{{ 'upsell-banner.css' | asset_url | stylesheet_tag }}}}

<div class="dnk-upsell-banner" data-product-id="{{{{ product.id }}}}">
  <h3>{{{{ block.settings.banner_text | default: "Додайте ще для безкоштовної доставки!" }}}}</h3>
  
  {{% if block.settings.recommended_product != blank %}}
    {{% assign rec = block.settings.recommended_product %}}
    <div class="recommended-product">
      <img src="{{{{ rec.featured_image | image_url: width: 200 }}}}" alt="{{{{ rec.title }}}}">
      <h4>{{{{ rec.title }}}}</h4>
      <p>{{{{ rec.price | money }}}}</p>
      <button data-add-to-cart="{{{{ rec.variants.first.id }}}}" class="dnk-add-btn">
        Додати до кошика
      </button>
    </div>
  {{% endif %}}
</div>

<script>
  document.querySelectorAll('.dnk-upsell-banner [data-add-to-cart]').forEach((btn) => {{
    btn.addEventListener('click', async (e) => {{
      const variantId = e.target.dataset.addToCart;
      await fetch('/cart/add.js', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ id: variantId, quantity: 1 }}),
      }});
      location.reload();
    }});
  }});
</script>""".strip()

    def _generate_loyalty_widget(self, spec: LiquidBlockSpec) -> str:
        return f"""{{{{ 'loyalty-widget.css' | asset_url | stylesheet_tag }}}}

<div class="dnk-loyalty-widget" data-customer-id="{{{{ customer.id }}}}">
  <div class="dnk-loyalty-header">
    <span class="dnk-loyalty-badge">{{{{ block.settings.widget_title | default: "DNK Rewards Club" }}}}</span>
  </div>
  
  {{% if customer %}}
    <div class="dnk-loyalty-body">
      <p>У вас є <strong id="dnk-points-val">150</strong> балів!</p>
      <div class="dnk-loyalty-progress-bar">
        <div class="dnk-loyalty-progress-fill" style="width: 75%;"></div>
      </div>
      <button id="dnk-redeem-btn" class="dnk-redeem-btn" data-points="100">
        {{{{ block.settings.redeem_text | default: "Обміняти 100 балів на $10 знижки" }}}}
      </button>
    </div>
  {{% else %}}
    <div class="dnk-loyalty-guest">
      <p>Увійдіть, щоб накопичувати бали та отримувати знижки.</p>
      <a href="/account/login" class="dnk-login-link">Увійти</a>
    </div>
  {{% endif %}}
</div>

<script>
  const redeemBtn = document.getElementById('dnk-redeem-btn');
  if (redeemBtn) {{
    redeemBtn.addEventListener('click', async () => {{
      redeemBtn.textContent = 'Знижка застосована!';
      redeemBtn.disabled = true;
    }});
  }}
</script>""".strip()

    def _generate_product_recommendations(self, spec: LiquidBlockSpec) -> str:
        return f"""{{{{ 'product-recommendations.css' | asset_url | stylesheet_tag }}}}

<div class="dnk-product-recommendations" data-product-id="{{{{ product.id }}}}">
  <h2>{{{{ block.settings.section_title | default: "Вам також може сподобатися" }}}}</h2>
  <div class="dnk-rec-grid">
    {{% for rec in recommendations.products limit: 4 %}}
      <div class="dnk-rec-card">
        <a href="{{{{ rec.url }}}}">
          <img src="{{{{ rec.featured_image | image_url: width: 300 }}}}" alt="{{{{ rec.title }}}}">
          <h3>{{{{ rec.title }}}}</h3>
          <p>{{{{ rec.price | money }}}}</p>
        </a>
      </div>
    {{% endfor %}}
  </div>
</div>""".strip()

    def _generate_generic_block(self, spec: LiquidBlockSpec) -> str:
        if spec.template:
            return spec.template.strip()
        return f"""<div class="dnk-generic-block {spec.name}">
  <h3>{{{{ block.settings.title | default: "{spec.name}" }}}}</h3>
</div>""".strip()

    def _generate_schema(self, spec: LiquidBlockSpec) -> Dict[str, Any]:
        return {
            "name": spec.name,
            "target": spec.target,
            "schema": spec.schema_fields,
        }

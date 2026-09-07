# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_shopify_builder/bundles/engine.py"
# purpose: "Dynamic Frequently Bought Together (FBT) and Volume Discounts Bundle Generator."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

def generate_pdp_bundles_assets(product_id: str, buy_together_products: list, discount_percentage: float) -> dict:
    """
    Generates Shopify Liquid and interactive CSS/JS for PDP Frequently Bought Together (FBT)
    as well as dynamic Volume Discounts table.
    """
    liquid_code = f"""<!--
  High-Conversion PDP Bundles Engine Block: Frequently Bought Together
  Generated automatically by DNK OS Shopify Builder
-->
<div class="dnk-bundles-section" data-product-id="{product_id}">
  <h3>Разом дешевше! Купуйте комплектом:</h3>
  
  <div class="dnk-fbt-grid">
    <!-- Primary PDP Product -->
    <div class="dnk-fbt-product dnk-fbt-product--primary" data-fbt-main>
      <div class="dnk-fbt-product__badge">Цей товар</div>
      <p class="dnk-fbt-product__title">Поточний товар (ID: {product_id})</p>
    </div>
    
    <div class="dnk-fbt-plus">+</div>

    <!-- Buy Together Products -->
    {" ".join(f'''<div class="dnk-fbt-product" data-fbt-addon="{p_id}">
      <label class="dnk-fbt-checkbox-container">
        <input type="checkbox" checked data-fbt-checkbox value="{p_id}">
        <span class="dnk-fbt-product__title">Супутній товар (ID: {p_id})</span>
      </label>
    </div>''' for p_id in buy_together_products)}
  </div>

  <!-- Pricing Summary Box -->
  <div class="dnk-fbt-summary-box">
    <div class="dnk-fbt-discount-alert">🏷️ Знижка {discount_percentage}% на весь комплект активована!</div>
    <div class="dnk-fbt-price-total">
      <span class="dnk-fbt-price-label">Загальна вартість:</span>
      <span class="dnk-fbt-old-price" data-fbt-old-price-val>0.00 ₴</span>
      <span class="dnk-fbt-new-price" data-fbt-new-price-val>0.00 ₴</span>
    </div>
    <button class="dnk-btn dnk-btn--add-bundle" data-add-bundle-btn>Додати комплект у кошик</button>
  </div>

  <!-- Volume Discounts Tier Box -->
  <div class="dnk-volume-discounts">
    <h3>Купуйте більше - платіть менше (Volume Discounts)</h3>
    <table class="dnk-volume-table">
      <thead>
        <tr>
          <th>Кількість</th>
          <th>Знижка</th>
          <th>Ціна за одиницю</th>
        </tr>
      </thead>
      <tbody>
        <tr data-tier="1">
          <td>1-2 шт.</td>
          <td>0%</td>
          <td>Базова ціна</td>
        </tr>
        <tr data-tier="2">
          <td>3-5 шт.</td>
          <td>10%</td>
          <td>-{discount_percentage}%</td>
        </tr>
        <tr data-tier="3">
          <td>6+ шт.</td>
          <td>20%</td>
          <td>-{(discount_percentage * 2):.1f}%</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
"""

    js_code = f"""/**
 * Dynamic PDP Bundles Engine Handler
 */
class DNKPDPBundles {{
  constructor() {{
    this.container = document.querySelector('.dnk-bundles-section');
    this.discount = {discount_percentage};
    this.init();
  }}

  init() {{
    if (!this.container) return;
    
    this.checkboxes = this.container.querySelectorAll('[data-fbt-checkbox]');
    this.checkboxes.forEach(cb => {{
      cb.addEventListener('change', () => this.recalculateTotalPrice());
    }});

    const addBtn = this.container.querySelector('[data-add-bundle-btn]');
    if (addBtn) {{
      addBtn.addEventListener('click', () => this.addBundleToCart());
    }}

    this.recalculateTotalPrice();
  }}

  recalculateTotalPrice() {{
    let oldTotal = 1500; // Mock base price of primary PDP product
    let selectedCount = 1;

    this.checkboxes.forEach(cb => {{
      if (cb.checked) {{
        oldTotal += 800; // Mock price of companion products
        selectedCount++;
      }}
    }});

    const hasDiscount = selectedCount > 1;
    const finalTotal = hasDiscount ? oldTotal * (1 - this.discount / 100) : oldTotal;

    const oldPriceEl = this.container.querySelector('[data-fbt-old-price-val]');
    const newPriceEl = this.container.querySelector('[data-fbt-new-price-val]');
    const alertEl = this.container.querySelector('.dnk-fbt-discount-alert');

    if (oldPriceEl) oldPriceEl.textContent = `${{oldTotal.toFixed(2)}} ₴`;
    if (newPriceEl) newPriceEl.textContent = `${{finalTotal.toFixed(2)}} ₴`;
    
    if (alertEl) {{
      alertEl.style.display = hasDiscount ? 'block' : 'none';
    }}
  }}

  async addBundleToCart() {{
    const items = [
      {{ id: parseInt(this.container.dataset.productId) || 12345, quantity: 1 }}
    ];

    this.checkboxes.forEach(cb => {{
      if (cb.checked) {{
        items.push({{ id: parseInt(cb.value) || 67890, quantity: 1 }});
      }}
    }});

    // AJAX Cart Form submission
    const response = await fetch('/cart/add.js', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ items }})
    }});

    if (response.ok) {{
      // Dynamically open Cart Drawer
      if (window.DNK_CartDrawer) {{
        window.DNK_CartDrawer.open();
      }} else {{
        window.location.href = '/cart';
      }}
    }}
  }}
}}
"""

    return {
        "status": "success",
        "liquid": liquid_code,
        "javascript": js_code,
        "metadata": {
            "product_id": product_id,
            "buy_together_products": buy_together_products,
            "discount_percentage": discount_percentage
        }
    }

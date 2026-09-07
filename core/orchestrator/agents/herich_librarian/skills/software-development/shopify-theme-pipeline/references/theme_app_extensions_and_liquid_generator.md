# Theme App Extensions & Generative UI Liquid Blocks Reference

## 🎯 Architectural Overview

Theme App Extensions (App Blocks) allow merchants to add dynamic app functionality directly inside their theme templates via Shopify's Theme Editor without manual code editing or destructive theme modifications.

```
[ Merchant Theme Editor ] ➔ ( Configures Block Settings via JSON Schema )
                                    ↓
                         ( Renders Liquid Template )
                                    ↓
                 [ Dynamic In-Store UI (Upsell / Loyalty) ]
```

---

## 🧱 1. Theme App Extension Structure (`apps/shopify/theme-extensions/`)

Every Theme App Extension package contains:

```
apps/shopify/theme-extensions/<extension-handle>/
├── blocks/
│   ├── <block-name>.liquid     # Liquid template markup with embedded logic & JavaScript
│   └── <block-name>.json       # Theme Editor schema definition for merchant configuration
├── assets/
│   └── <block-name>.css        # Block styling linked via {{ '<name>.css' | asset_url | stylesheet_tag }}
└── shopify.extension.toml      # Theme App Extension metadata & handle
```

### Manifest (`shopify.extension.toml`)
```toml
name = "dnk-app-blocks"
type = "theme_app_extension"

[theme_app_extension]
name = "DNK App Blocks"
handle = "dnk-app-blocks"
```

---

## ⚡ 2. Liquid Block Generator (`LiquidBlockGenerator`)

`LiquidBlockGenerator` (`apps/api/services/liquid_block_generator.py`) synthesizes Liquid blocks and accompanying Theme Editor schema definitions programmatically based on `LiquidBlockSpec`:

```python
from apps.api.services.liquid_block_generator import LiquidBlockGenerator, LiquidBlockSpec

generator = LiquidBlockGenerator()
spec = LiquidBlockSpec(
    name="dnk-upsell-banner",
    block_type="upsell_banner",
    schema_fields=[
        {"type": "product", "id": "recommended_product", "label": "Рекомендований товар"},
        {"type": "text", "id": "banner_text", "label": "Текст банера", "default": "Додайте ще для безкоштовної доставки!"}
    ],
    target="section"
)

result = generator.generate(spec)
# result contains:
# - "liquid_file": "dnk-upsell-banner.liquid"
# - "schema_file": "dnk-upsell-banner.json"
# - "template": rendered liquid template string
# - "schema": theme editor JSON schema dict
```

### Supported Block Types:
1. `upsell_banner`: Dynamic product upsell card with Ajax `/cart/add.js` handler.
2. `loyalty_widget`: Rewards club balance tracker and loyalty points redemption interface.
3. `product_recommendations`: Recommendation grid utilizing Shopify's `recommendations.products` object.
4. `generic_block`: Extensible custom Liquid block template with section-targeting support.

---

## 🖥️ 3. Embedded React Admin Dashboard (`DNKAdminDashboard.tsx`)

Embedded Admin extensions allow merchants to interact with backend services directly from the Shopify Admin UI via Shopify App Bridge:

```typescript
import React from 'react';
import { useAppBridge } from '@shopify/app-bridge-react';

export function DNKAdminDashboard({ storeDomain, apiVersion }) { ... }
```

### Access Scopes (`shopify.extension.toml`)
```toml
name = "dnk-admin-dashboard"
type = "admin"

[access_scopes]
scopes = "read_products,write_products,read_orders,write_orders"
```

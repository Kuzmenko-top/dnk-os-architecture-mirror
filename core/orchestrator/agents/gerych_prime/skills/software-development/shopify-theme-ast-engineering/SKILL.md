---
name: shopify-theme-ast-engineering
description: Shopify OS 2.0 AST mutations & Canvas-to-Liquid transpiler.
category: software-development
version: "1.0.0"
author: "DNK-e.com Maksym"
license: "MIT"
metadata:
  hermes:
    tags: ["shopify", "liquid", "ast", "templates", "transpiler", "rfc-6902", "canvas"]
    related_skills: ["sota-repository-assimilation", "test-driven-development"]
---

# 🛍️ Shopify Theme OS 2.0 AST & Mechanical Transpiler Engineering

## When to Use
Use when building, mutating, or transpiling Shopify Online Store 2.0 themes (`templates/*.json`, `sections/*.liquid`, `config/settings_data.json`), applying RFC 6902 JSON patches to template trees, or transforming visual Canvas HTML/Tailwind nodes into production Liquid sections with schema and design token bindings.

## 🧱 1. Template State Engine (RFC 6902 & Ordinal Management)
Shopify Online Store 2.0 JSON templates define sections under `"sections"` and ordering under `"order"`.

### Core Invariants:
1. **Atomic RFC 6902 Patching**: Use standard JSON patch operations (`add`, `remove`, `replace`, `move`, `copy`, `test`) to mutate template trees idempotently.
2. **Dynamic Ordinal Indexing**:
   - `outline(template_name)`: Returns an ordered view `[{id, type, ordinal, blocks: [{id, type}]}]`.
   - `add_section(type, after_ordinal, settings)`: Generates unique ID `section_<hash>` or `<type>_<timestamp>` and inserts into `order` after the specified ordinal index.
   - `remove_section(ordinal_or_id)`: Removes section definition and purges its ID from `order`.
   - `reorder(order_list)` / `move_section(id, new_ordinal)`: Safely updates the `order` array while ensuring all referenced IDs exist.
   - `add_block(section_id, block_type, settings)`: Manages nested `block_order` arrays within sections.

## ⚙️ 2. Mechanical Transpiler (Canvas HTML ➡️ Liquid AST)
Converts visual canvas elements (HTML + Tailwind + Open Design Tokens) into clean, customizable Shopify Liquid sections.

### Key Transpilation Steps:
1. **HTML & Block Decomposition**:
   - Detect repeated structural siblings (e.g. cards, list items) and convert them into Liquid block loops:
     ```liquid
     {% for block in section.blocks %}
       <div class="card-item" {{ block.shopify_attributes }}>
         ...
       </div>
     {% endfor %}
     ```
2. **Shopify Attributes Placement**:
   - `{{ block.shopify_attributes }}` MUST be placed directly inside the opening tag of the outermost DOM element of each block to support the Shopify Theme Customizer inspector.
3. **Open Design CSS Token Injection (`{% style %}`)**:
   - Extract design tokens and bind them to root CSS custom properties with the `--dnk-*` prefix:
     ```liquid
     {% style %}
       #shopify-section-{{ section.id }} {
         --dnk-accent: {{ section.settings.accent_color | default: '#6366f1' }};
         --dnk-card-bg: {{ section.settings.card_bg | default: '#1e1e2e' }};
       }
     {% endstyle %}
     ```
4. **Schema & Preset Synthesis (`{% schema %}`)**:
   - Generate valid Shopify schema JSON with appropriate setting types: `text`, `textarea`, `image_picker`, `color`, `range`, `select`, `checkbox`, `richtext`.
   - Always supply at least one preset under `presets: [{ name: "Default" }]` so merchants can add the section in the Shopify editor.

## ⚡ 3. Zero-Latency Live Liquid Sandbox & Inspector Panel
When rendering Liquid sections inside React/Canvas applications (e.g. `ShopifyBuilderNode.tsx`, `ShopifyInspectorSection.tsx`, `InspectorPanel.tsx`):
- **Two-Way Node State Binding**: Sync node state (`templateSections`, `settings`) between spatial canvas nodes and the right-hand `InspectorPanel` via `onUpdateNodeData` callbacks and React `useEffect` listeners.
- **Dual Visual / Code Editing**: Provide instant switching between visual controls (color pickers, heading inputs, toggles) and raw Liquid source code editing with syntax highlighting.
- **Client-Side Live Substitution**: Perform instant client-side token replacement (`{{ section.settings.heading }}`, `{{ 'style.css' | asset_url }}`) without round-tripping to Shopify servers for draft previews.
- **TemplateStateEngine Interactive Block Lifecycle**: Enable merchants/builders to add (`add_block`), delete (`remove_block`), reorder (`move_up`/`move_down`), and tune settings of modular blocks (`heading`, `button`, `badge`, `variant_picker`, `buy_buttons`, `custom_liquid`) directly from the inspector panel with automatic `block_order` synchronization.
- **Pre-Export JSON Schema Compliance Gate**: Run in-browser JSON Schema validation against Shopify OS 2.0 specifications (checking `sections`, `order`, `blocks`, `block_order`, and `{% schema %}` tags) before dispatching to `/api/shopify/store/export-manifest` or `/api/shopify/store/export-zip`.

## 🏪 4. Autonomous Store Synthesizer & Mega-Registry
Synthesizes entire Shopify OS 2.0 stores per niche (`tech_apparel`, `health_supplements`, `luxury_jewelry`, `general_ecom`):
1. **Mega-Component Registry**:
   - Classify components across 5 key conversion categories: `pdp_conversion`, `cart_checkout`, `social_proof`, `hero_banners`, `discovery_nav`.
   - Adapt legacy monolithic sections into modular Tinker `blocks/*.liquid` with schema and CSS extraction.
2. **Deterministic Multi-Template Synthesis**:
   - `templates/index.json`: 5-7 high-converting sections (Hero split, Value Props, Featured Collection, Social Proof, Comparison, FAQ).
   - `templates/product.json`: 10+ modular Tinker blocks (Tiered Bundles, Delivery Estimator, Variant Picker, Sticky Buy, Trust Badges).
3. **Stateless Template Mutations**:
   - Ensure `TemplateStateEngine.mutate(template_dict, action, **params)` supports both stateless dictionary transformations and stateful instance workflows.

## 📦 5. Production Theme Packaging & ZIP Exporter
Package the full theme into an official Shopify-compatible `.zip` archive ready for `Themes > Upload zip`:
1. **Archive Directory Hierarchy**:
   - `layout/`: `theme.liquid`, `password.liquid`
   - `templates/`: synthesized `index.json`, `product.json`, `cart.json`, etc.
   - `blocks/`: all modular Tinker blocks (`*.liquid`)
   - `sections/`: base sections (`*.liquid`)
   - `snippets/`: supporting snippets (`*.liquid`)
   - `assets/`: compiled JS, CSS, SVG icons
   - `config/`: `settings_data.json` (with store name, Open Design color palette injected) and `settings_schema.json`
   - `locales/`: default `en.default.json` + internationalization bundles.
2. **FastAPI ZIP Streaming**:
   - Return raw `Response(content=zip_bytes, media_type="application/zip")` with `Content-Disposition: attachment; filename="<store>_shopify_theme.zip"` for zero-dependency 1-click browser downloads.

## 🎬 6. Canvas Graph to Liquid Transpiler & Remotion Video Bridge
Converts visual graph nodes (`hero_banner`, `product_grid`, `feature_list`, `video_player`) into production-ready Shopify OS 2.0 Liquid sections with embedded Remotion 9:16 vertical video support (`core/shopify_liquid/canvas_to_liquid_transpiler.py`):
1. **Node Schema & Block Generation**:
   - Map Canvas nodes to customizable Liquid blocks and settings (`{% schema %}` JSON specification).
   - Render vertical 9:16 Remotion MP4 video embeds with responsive CSS containers (`aspect-ratio: 9/16`).
2. **Swarm Shared Memory Ledger Registration**:
   - Automatically publishes generated Liquid code into the `SwarmSharedMemoryLedger` under `ArtifactCategory.LIQUID_SECTION` with deterministic SHA-256 hash.
   - Allows parallel subagents (e.g. `gerych_auditor`, `dnk_shopify`) to consume the generated section AST directly without local disk read roundtrips.
3. **REST API Contract**:
   - Exposed via `POST /api/v3/shopify/transpile-canvas-graph` taking `{ "section_name": str, "canvas_graph": { "nodes": [...] } }` and returning `{ "status": "success", "section_name": str, "liquid_code": str, "artifact_id": str }`.

## 🛡️ Pitfalls & Common Errors
- **Missing `block_order`**: Shopify requires both `"blocks": { ... }` and `"block_order": [ ... ]` when blocks are present.
- **Dangling Order References**: Removing a section from `"sections"` without removing it from `"order"` causes Shopify theme parse failures.
- **Non-Standard Settings Types**: Shopify Schema strictly permits specific types. Ensure all transpiled controls map to official Shopify schema types.
- **Header Pollution in Binary ZIP Downloads**: When testing HTTP ZIP download endpoints via `curl`, avoid `-i` with `--output` because headers get prepended into the binary zip file. Use `-s` with `--output file.zip` and verify with `unzip -t`.

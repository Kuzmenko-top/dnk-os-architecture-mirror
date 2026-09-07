---
name: shopify-theme-pipeline
description: Use when bundling, rewriting, or deploying Shopify themes.
version: "1.0.0"
author: "DNK-e.com Maksym"
license: "MIT"
metadata:
  hermes:
    tags: ["shopify", "vite", "liquid", "deploy", "sri", "cdn"]
    related_skills: ["test-driven-development", "requesting-code-review"]
---

# Shopify Theme Pipeline & Zero-Downtime Deployment

This skill provides architectural guidance, patterns, and procedures for compiling, bundling, rewriting, syncing, and deploying Shopify themes with zero downtime and 100% cache efficiency.

## 🎯 When to Use

- Building frontend assets for Shopify themes using Vite or modern bundlers.
- Rewriting Liquid AST asset URLs and injecting SRI integrity attributes into script tags.
- Syncing theme assets to Edge CDN with optimal Cache-Control headers.
- Implementing zero-downtime atomic theme deployments and instant rollbacks.

## 📚 Reference Documentation

- Detailed cache header rules and SRI standards: `references/cache_headers_and_sri.md`
- Data models contract and FastAPI routes: `references/pipeline_models_and_endpoints.md`
- Checkout UI extensions, multi-gateway payments, post-purchase upsell & webhooks: `references/checkout_extensions_and_gateways.md`
- Web Pixel API, GDPR PII anonymization & event ingestion pipeline: `references/web_pixel_and_gdpr_ingestion.md`
- Admin API GraphQL Engine, Token-Bucket Rate Limiter & Bulk Operations: `references/admin_graphql_and_bulk_operations.md`
- Theme App Extensions, Liquid Block Generator & Embedded Admin Dashboard: `references/theme_app_extensions_and_liquid_generator.md`
- Flow Automation, Webhook HMAC-SHA256 Bridge & Event Routing: `references/flow_automation_and_webhook_hmac.md`
- Shopify Functions, Wasm Custom Checkout Logic & Cart Transforms: `references/shopify_functions_and_wasm_checkout.md`

## 🏗️ Core Architecture & Pipeline Phases

```
[ Theme Assets ] ➔ ( 1. Vite Bundling & Hashing ) ➔ [ manifest.json + SRI ]
                        ↓
                 ( 2. Liquid AST Rewriting ) ➔ [ Rewritten Liquid Templates ]
                        ↓
                 ( 3. CDN Sync + Cache Headers ) ➔ Edge CDN Upload
                        ↓
                 ( 4. Zero-Downtime Deploy Engine ) ➔ [ Snapshot ➔ Draft ➔ Validate ➔ Atomic Active ]
```

---

## ⚡ 1. Vite Asset Bundling & Manifest Generation

When processing frontend theme assets (JS, CSS, images, fonts):

1. **SHA-256 Content Hashing**:
   - Compute SHA-256 hash of file content.
   - Truncate hash to 8–12 characters.
   - Format output filename as `[name].[hash].[ext]` (e.g., `theme.a1b2c3d4.js`).
2. **Subresource Integrity (SRI)**:
   - Compute `sha384` digest of the bundled file.
   - Encode in Base64: `sha384-<base64_digest>`.
3. **Manifest Construction**:
   - Emit a `manifest.json` mapping original paths to hashed paths, sizes, and SRI signatures:
     ```json
     {
       "assets/theme.js": {
         "hashed_name": "theme.a1b2c3d4.js",
         "hashed_path": "assets/theme.a1b2c3d4.js",
         "sri": "sha384-...",
         "size_bytes": 1024
       }
     }
     ```

---

## 🧬 2. Liquid AST & HTML Tag Rewriting

Rewriting template asset references ensures that Liquid filters and static HTML tags target cache-busted CDN assets without breaking theme logic.

1. **Liquid Filter Mapping**:
   - Target filters: `asset_url`, `asset_img_url`, `image_url`, `file_url`, `file_img_url`.
   - Pattern: `'app.js' | asset_url` ➔ `'app.a1b2c3d4.js' | asset_url`.
2. **Static Tag Rewriting & SRI Injection**:
   - `<script src="{{ 'app.js' | asset_url }}"></script>` ➔
     `<script src="{{ 'app.a1b2c3d4.js' | asset_url }}" integrity="sha384-..." crossorigin="anonymous"></script>`.
   - Update `<link rel="stylesheet" href="...">` and `<img>` tags.
3. **Syntax Preservation Invariants**:
   - Never modify content inside `{% raw %} ... {% endraw %}` or `{% comment %} ... {% endcomment %}` blocks.
   - Preserve spacing and line endings around Liquid tags.

---

## 🚀 3. CDN Sync & Cache-Control Strategy

Enforce strict HTTP caching headers based on asset mutability:

- **Hashed Assets (`*.[hash].ext`)**:
  - `Cache-Control: public, max-age=31536000, immutable`
  - High-performance 1-year browser and Edge CDN caching.
- **Manifest & Unhashed Layouts (`manifest.json`, root Liquid layouts)**:
  - `Cache-Control: public, max-age=60, stale-while-revalidate=300`
  - Short TTL with background revalidation to ensure immediate manifest update propagation.

---

## 🛡️ 4. Zero-Downtime Deployment & Rollback Engine

To guarantee zero broken windows during theme releases:

1. **Snapshot Stage**:
   - Download/read current live main theme assets.
   - Store immutable snapshot indexed by store domain and timestamp.
2. **Draft Theme Upload**:
   - Upload new bundle & rewritten Liquid templates to a hidden/unpublished draft theme.
3. **Quality Gate Validation**:
   - Run automated verification on draft theme (Liquid syntax check, asset resolution check).
   - If validation fails: **Abort deploy instantly**; live main theme remains untouched.
4. **Atomic Switch**:
   - Publish draft theme to `main` role via Shopify Admin REST/GraphQL API.
5. **Rollback Workflow**:
   - If issues arise post-publish, retrieve the latest stable snapshot.
   - Restore snapshot assets directly to main theme or switch role back to previous live theme ID.

---

## 🔒 5. Security & Boundary Protocols

- **Token Isolation**: Keep Shopify API Admin tokens strictly server-side.
- **Domain Whitelisting**: Check incoming deploy requests against `ALLOWED_SHOPIFY_STORES`.
- **Fail-Closed Strategy**: On HTTP 401 (Unauthorized), 403 (Forbidden), or 429 (Rate Limit), stop deployment sequence and raise standard error response.

---

## ⚡ 6. Shopify Functions & Wasm Sandbox Execution Engine

When building and executing Shopify Functions (`cart_transform`, `product_discounts`, `delivery_customization`, `payment_customization`, `order_routing`):

1. **Wasm Sandbox Limits**:
   - Hard execution ceiling of **5.0 ms** CPU budget per invocation.
   - Strict memory ceiling of **10 MB** allocation.
2. **Fail-Safe Graceful Fallback**:
   - In case of timeout or sandbox error, never disrupt checkout; return empty operations/discounts gracefully and log telemetry via `ShopifyFunctionExecutionLogModel`.
3. **Cart Transform & Bundle Expansion**:
   - Automatically split bundle parent lines into component merchandise IDs with `expand` operations and optional fixed price adjustments.
4. **Dynamic Discounts**:
   - Evaluate tiered volume discounts, B2B wholesale tag matches, and VIP customer rules returning standard `FunctionResult` schema.

---

## ⚠️ Pitfalls & Implementation Notes

- **SRI Injection Trigger**: In AST rewriters, if an `integrity_map` parameter is provided during compilation/rewriting, automatically activate SRI attribute injection so script tags receive matching `integrity="sha384-..."` attributes even if the boolean configuration flag wasn't explicitly set.
- **API Alias Alignment**: `ShopifyCDNSync` must expose both `sync_bundle` and `sync_assets` as callable interfaces to ensure compatibility across batch deployment callers and pipeline orchestrators.


# Shopify CDN Cache-Control Headers & SRI Reference

## Cache-Control Header Decision Matrix

| Asset Type | Pattern | Cache-Control Header | Reasoning |
|---|---|---|---|
| Hashed JS / CSS | `*.[hash].js`, `*.[hash].css` | `public, max-age=31536000, immutable` | Content hash guarantees uniqueness. Cached forever on Edge CDN & browsers. |
| Hashed Media | `*.[hash].png`, `*.[hash].svg` | `public, max-age=31536000, immutable` | Media content is immutable once hashed. |
| Manifest File | `manifest.json` | `public, max-age=60, stale-while-revalidate=300` | Manifest changes with every release; short 60s TTL with SWR fallback. |
| Unhashed Templates | `*.liquid`, `layout/*.liquid` | `public, max-age=60, stale-while-revalidate=300` | Templates refer to manifest; must revalidate quickly. |

## Subresource Integrity (SRI) Standard

- **Algorithm**: `sha384`
- **Format**: `sha384-<base64_digest>`
- **Usage**: Added to HTML script tags as `integrity="sha384-..." crossorigin="anonymous"` during Liquid AST rewriting.

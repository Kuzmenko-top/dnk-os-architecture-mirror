# Shopify Deployment Pipeline Models & FastAPI Endpoints Reference

## 1. Pydantic Models Contract

### ViteBundleResult (`ShopifyViteBundler`)
- `bundle_id`: `str` (e.g., `bundle_20260828_120000_a1b2`)
- `bundled_files`: `Dict[str, str | bytes]` (output file path -> content)
- `manifest_mapping`: `Dict[str, str]` (raw asset path -> hashed asset path)
- `integrity_map`: `Dict[str, str]` (hashed path -> `sha384-...`)
- `manifest`: `Dict[str, ViteManifestChunk]`
- `total_size_bytes`: `int`

### LiquidRewriteResult (`LiquidASTAssetRewriter`)
- `source_template`: `str`
- `rewritten_template`: `str`
- `replacements_count`: `int`
- `rewritten_mappings`: `Dict[str, str]`
- `unmapped_assets`: `List[str]`
- `warnings`: `List[str]`

### CDNSyncReport (`ShopifyCDNSync`)
- `synced_count`: `int`
- `failed_count`: `int`
- `synced_assets`: `List[CDNAssetMeta]`
- `cache_header_summary`: `Dict[str, str]` (file path -> Cache-Control string)

### DeployPipelineResult (`ShopifyDeployEngine`)
- `success`: `bool`
- `release`: `ShopifyRelease`
- `snapshot`: `ThemeSnapshot`
- `bundle_result`: `Optional[ViteBundleResult]`
- `cdn_report`: `Optional[CDNSyncReport]`
- `timing_ms`: `Dict[str, float]`
- `error_code`: `Optional[str]`

## 2. Standard FastAPI Routes (`apps/api/routers/shopify.py`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/shopify/build` | Triggers Vite asset bundling & manifest generation |
| `POST` | `/api/shopify/deploy` | Executes zero-downtime release pipeline |
| `POST` | `/api/shopify/rollback` | Restores prior stable snapshot atomically |
| `GET` | `/api/shopify/releases/{store_domain}` | Lists historical deployment releases |
| `GET` | `/api/shopify/status/{store_domain}` | Returns active release & latest snapshot state |

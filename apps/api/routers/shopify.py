# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_shopify"
# purpose: "FastAPI router exposing read-only Shopify endpoints with dependency injection and error isolation"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response
from pydantic import BaseModel, Field

from apps.api.services.shopify_adapter import ShopifyAdapter
from apps.api.services.shopify_models import ShopifyAdapterResult
from apps.api.services.liquid_preview_engine import LiquidPreviewEngine, LiquidRenderResult
from apps.api.services.tailwind_v4_jit import TailwindV4JITCompiler, TailwindCompilationResult
from apps.api.services.shopify_theme_extension import (
    AppBlockSchemaGenerator,
    SectionConfigManager,
    ThemeStoreV2Validator,
    ComplianceReport
)
from services.dnk_shopify_builder.template_state_engine import TemplateStateEngine
from services.dnk_shopify_builder.mechanical_transpiler import mechanical_transpiler
from services.dnk_shopify_builder.liquid_compiler import liquid_compiler
from services.dnk_shopify_builder.theme_adapter import theme_adapter
from services.dnk_shopify_builder.store_synthesizer import store_synthesizer
from services.dnk_shopify_builder.theme_exporter import theme_exporter


class LiquidPreviewRequest(BaseModel):
    source: str = Field(..., description="Liquid template source string")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Mock store context variables")
    snippets: Optional[Dict[str, str]] = Field(default=None, description="Reusable snippet templates dict")
    sections: Optional[Dict[str, str]] = Field(default=None, description="Reusable section templates dict")
    inject_tailwind_css: bool = Field(default=True, description="Inject compiled Tailwind v4 JIT CSS bundle")


class TailwindCompileRequest(BaseModel):
    source: str = Field(..., description="Liquid template source string or AST")
    theme_tokens: Optional[Dict[str, Any]] = Field(default=None, description="Custom theme tokens mapping")
    include_reset: bool = Field(default=False, description="Include CSS reset rules")


class ExtensionValidationRequest(BaseModel):
    files: Dict[str, str] = Field(..., description="Map of theme extension file paths to string contents")


class AppBlockSchemaGenerateRequest(BaseModel):
    name: str = Field(..., description="App block display name")
    target: str = Field(default="section", description="Target: section, body, or head")
    javascript: Optional[str] = Field(default=None, description="Optional bundled JavaScript asset")
    stylesheet: Optional[str] = Field(default=None, description="Optional bundled CSS stylesheet asset")
    settings: Optional[List[Dict[str, Any]]] = Field(default=None, description="App block schema settings list")
    available_if: Optional[str] = Field(default=None, description="Optional conditional availability")


class SectionConfigGenerateRequest(BaseModel):
    name: str = Field(..., description="Section display name")
    tag: Optional[str] = Field(default="section", description="HTML wrapper tag")
    settings: Optional[List[Dict[str, Any]]] = Field(default=None, description="Section settings list")
    blocks: Optional[List[Dict[str, Any]]] = Field(default=None, description="Section block definitions")
    presets: Optional[List[Dict[str, Any]]] = Field(default=None, description="Section presets")
    max_blocks: Optional[int] = Field(default=None, description="Max allowed blocks limit")


class TemplateMutateRequest(BaseModel):
    template: Dict[str, Any] = Field(..., description="Shopify OS 2.0 template JSON object")
    action: str = Field(..., description="Action: add_section | remove_section | reorder | move_section | add_block | remove_block | patch_setting | outline | json_patch")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the specific mutation action")


class CanvasNodeTranspileRequest(BaseModel):
    html_content: str = Field(..., description="HTML / Tailwind snippet from canvas node")
    section_name: Optional[str] = Field(default="Canvas Transpiled Section", description="Shopify section name")
    theme_tokens: Optional[Dict[str, Any]] = Field(default=None, description="Open Design theme tokens dictionary")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Transpilation options")


class SectionValidateRequest(BaseModel):
    liquid_code: str = Field(..., description="Shopify Liquid section code containing liquid tags, styles, and schema")


class StoreSynthesizeRequest(BaseModel):
    store_name: str = Field(..., description="Store or brand name")
    niche: str = Field(default="general_ecom", description="Niche preset: tech_apparel, health_supplements, luxury_jewelry, general_ecom")
    theme_tokens: Optional[Dict[str, str]] = Field(default=None, description="Open Design CSS color and style tokens")


class AdaptBlockRequest(BaseModel):
    section_name: str = Field(..., description="Legacy section file name to adapt into Tinker block")
    target_block_name: Optional[str] = Field(default=None, description="Optional custom target block name")


class StoreExportZipRequest(BaseModel):
    store_name: str = Field(default="Apex Cybernetics", description="Store or brand name")
    niche: str = Field(default="tech_apparel", description="Niche: tech_apparel, health_supplements, luxury_jewelry, general_ecom")
    theme_tokens: Optional[Dict[str, str]] = Field(default=None, description="Custom theme tokens")
    custom_templates: Optional[Dict[str, Any]] = Field(default=None, description="Optional customized JSON templates dict")


router = APIRouter(prefix="/api/shopify", tags=["shopify"])

_adapter_instance: Optional[ShopifyAdapter] = None


def set_adapter(adapter: Optional[ShopifyAdapter]) -> None:
    """Explicitly override the ShopifyAdapter instance (useful in testing)."""
    global _adapter_instance
    _adapter_instance = adapter


def get_shopify_adapter() -> ShopifyAdapter:
    """Dependency provider for ShopifyAdapter."""
    global _adapter_instance
    if _adapter_instance is not None:
        return _adapter_instance
    return ShopifyAdapter()


@router.get("/{store_domain}/meta", response_model=ShopifyAdapterResult)
def get_shop_metadata(
    store_domain: str = Path(..., description="Store domain, e.g., dnk-e-com.myshopify.com"),
    allow_fixture: bool = Query(False, description="Allow fixture fallback on failure"),
    adapter: ShopifyAdapter = Depends(get_shopify_adapter)
) -> ShopifyAdapterResult:
    """Fetch shop information and rate limit metrics."""
    result = adapter.get_shop_meta(store_domain, allow_fixture_fallback=allow_fixture)
    if result.error_code == "forbidden_store":
        raise HTTPException(status_code=403, detail="Store domain is not in the allowed list")
    return result


@router.get("/{store_domain}/themes", response_model=ShopifyAdapterResult)
def get_shop_themes(
    store_domain: str = Path(..., description="Store domain, e.g., dnk-e-com.myshopify.com"),
    allow_fixture: bool = Query(False, description="Allow fixture fallback on failure"),
    adapter: ShopifyAdapter = Depends(get_shopify_adapter)
) -> ShopifyAdapterResult:
    """List all available themes for a store."""
    result = adapter.get_themes(store_domain, allow_fixture_fallback=allow_fixture)
    if result.error_code == "forbidden_store":
        raise HTTPException(status_code=403, detail="Store domain is not in the allowed list")
    return result


@router.get("/{store_domain}/themes/{theme_id}/assets", response_model=ShopifyAdapterResult)
def get_theme_assets(
    store_domain: str = Path(..., description="Store domain, e.g., dnk-e-com.myshopify.com"),
    theme_id: str = Path(..., description="Unique theme ID"),
    allow_fixture: bool = Query(False, description="Allow fixture fallback on failure"),
    adapter: ShopifyAdapter = Depends(get_shopify_adapter)
) -> ShopifyAdapterResult:
    """Get the file tree and asset keys for a theme."""
    result = adapter.get_theme_assets(store_domain, theme_id, allow_fixture_fallback=allow_fixture)
    if result.error_code == "forbidden_store":
        raise HTTPException(status_code=403, detail="Store domain is not in the allowed list")
    return result


@router.get("/{store_domain}/themes/{theme_id}/asset", response_model=ShopifyAdapterResult)
def get_asset_content(
    store_domain: str = Path(..., description="Store domain, e.g., dnk-e-com.myshopify.com"),
    theme_id: str = Path(..., description="Unique theme ID"),
    asset_key: str = Query(..., description="Asset key, e.g. layout/theme.liquid"),
    allow_fixture: bool = Query(False, description="Allow fixture fallback on failure"),
    adapter: ShopifyAdapter = Depends(get_shopify_adapter)
) -> ShopifyAdapterResult:
    """Read the content (Liquid/JSON/CSS) of a specific asset."""
    result = adapter.get_asset_content(store_domain, theme_id, asset_key, allow_fixture_fallback=allow_fixture)
    if result.error_code == "forbidden_store":
        raise HTTPException(status_code=403, detail="Store domain is not in the allowed list")
    if result.error_code == "invalid_asset":
        raise HTTPException(status_code=400, detail="Invalid asset key")
    return result


@router.get("/{store_domain}/themes/{theme_id}/tree", response_model=ShopifyAdapterResult)
def get_theme_tree(
    store_domain: str = Path(..., description="Store domain, e.g., dnk-e-com.myshopify.com"),
    theme_id: str = Path(..., description="Unique theme ID"),
    allow_fixture: bool = Query(False, description="Allow fixture fallback on failure"),
    adapter: ShopifyAdapter = Depends(get_shopify_adapter)
) -> ShopifyAdapterResult:
    """Fetch categorized asset hierarchy tree (layout, templates, sections, snippets, etc.)."""
    result = adapter.get_theme_asset_tree(store_domain, theme_id, allow_fixture_fallback=allow_fixture)
    if result.error_code == "forbidden_store":
        raise HTTPException(status_code=403, detail="Store domain is not in the allowed list")
    return result


@router.get("/{store_domain}/themes/{theme_id}/canvas-graph", response_model=ShopifyAdapterResult)
def get_theme_canvas_graph(
    store_domain: str = Path(..., description="Store domain, e.g., dnk-e-com.myshopify.com"),
    theme_id: str = Path(..., description="Unique theme ID"),
    allow_fixture: bool = Query(False, description="Allow fixture fallback on failure"),
    adapter: ShopifyAdapter = Depends(get_shopify_adapter)
) -> ShopifyAdapterResult:
    """Generate Visual Canvas graph with section nodes and snippet render edges."""
    result = adapter.get_theme_canvas_graph(store_domain, theme_id, allow_fixture_fallback=allow_fixture)
    if result.error_code == "forbidden_store":
        raise HTTPException(status_code=403, detail="Store domain is not in the allowed list")
    return result


@router.post("/preview/render")
def render_liquid_preview(req: LiquidPreviewRequest) -> Dict[str, Any]:
    """Renders Liquid template with real-time context hydration and Tailwind v4 JIT compilation."""
    engine = LiquidPreviewEngine(snippets=req.snippets, sections=req.sections)
    res = engine.render(req.source, context=req.context, inject_tailwind_css=req.inject_tailwind_css)
    return {
        "html": res.html,
        "css": res.css,
        "classes_used": res.classes_used,
        "execution_time_ms": res.execution_time_ms,
        "sections_rendered": res.sections_rendered,
        "snippets_rendered": res.snippets_rendered,
        "schemas_extracted": res.schemas_extracted,
        "error": res.error
    }


@router.post("/tailwind/compile")
def compile_tailwind_jit(req: TailwindCompileRequest) -> Dict[str, Any]:
    """Compiles atomic Tailwind v4 JIT CSS from Liquid AST or template source."""
    engine = LiquidPreviewEngine(theme_tokens=req.theme_tokens)
    ast = engine.parse_source(req.source)
    res = engine.tailwind_compiler.compile(ast, include_reset=req.include_reset)
    return {
        "css": res.css,
        "classes_found": res.classes_found,
        "rules_generated": res.rules_generated,
        "css_size_bytes": res.css_size_bytes
    }


@router.post("/extension/validate")
def validate_theme_extension(req: ExtensionValidationRequest) -> Dict[str, Any]:
    """Validates Theme App Extension files against Shopify Theme Store V2 guidelines."""
    report = ThemeStoreV2Validator.validate_theme_extension_directory(req.files)
    return {
        "is_valid": report.is_valid,
        "score": report.score,
        "errors": [
            {
                "severity": err.severity,
                "code": err.code,
                "message": err.message,
                "file_path": err.file_path,
                "line": err.line
            }
            for err in report.errors
        ],
        "warnings": [
            {
                "severity": w.severity,
                "code": w.code,
                "message": w.message,
                "file_path": w.file_path,
                "line": w.line
            }
            for w in report.warnings
        ],
        "recommendations": report.recommendations,
        "metadata": report.metadata
    }


@router.post("/schema/generate")
def generate_app_block_schema(req: AppBlockSchemaGenerateRequest) -> Dict[str, Any]:
    """Generates Shopify {% schema %} block for an App Block / Section."""
    schema_str = AppBlockSchemaGenerator.generate_app_block_schema(
        name=req.name,
        target=req.target,
        javascript=req.javascript,
        stylesheet=req.stylesheet,
        settings=req.settings,
        available_if=req.available_if
    )
    return {
        "schema_liquid": schema_str,
        "parsed_schema": AppBlockSchemaGenerator.extract_schema_from_liquid(schema_str)
    }


@router.post("/section/schema")
def generate_section_schema(req: SectionConfigGenerateRequest) -> Dict[str, Any]:
    """Generates Shopify {% schema %} block for an Online Store 2.0 Section."""
    schema_str = AppBlockSchemaGenerator.generate_section_schema(
        name=req.name,
        tag=req.tag,
        settings=req.settings,
        blocks=req.blocks,
        presets=req.presets,
        max_blocks=req.max_blocks
    )
    return {
        "schema_liquid": schema_str,
        "parsed_schema": AppBlockSchemaGenerator.extract_schema_from_liquid(schema_str)
    }


@router.post("/template/mutate")
def mutate_template(req: TemplateMutateRequest) -> Dict[str, Any]:
    """
    Executes atomic RFC 6902 / ordinal mutation on a Shopify OS 2.0 template JSON.
    Actions supported:
    - add_section, remove_section, reorder, move_section
    - add_block, remove_block, patch_setting, outline, json_patch
    """
    engine = TemplateStateEngine(template_data=req.template)
    action = req.action.lower()
    p = req.params

    try:
        if action == "outline":
            outline_data = engine.outline()
            return {
                "success": True,
                "action": action,
                "outline": outline_data,
                "template": engine.get_template()
            }
        elif action == "add_section":
            res = engine.add_section(
                type=p.get("type", "custom-section"),
                after_ordinal=p.get("after_ordinal"),
                settings=p.get("settings"),
                section_id=p.get("section_id"),
                disabled=p.get("disabled", False),
                blocks=p.get("blocks"),
                block_order=p.get("block_order")
            )
            return {"success": True, "action": action, "result": res, "template": engine.get_template()}
        elif action == "remove_section":
            target = p.get("ordinal_or_id", p.get("section_id", p.get("ordinal", 0)))
            res = engine.remove_section(ordinal_or_id=target)
            return {"success": True, "action": action, "result": res, "template": engine.get_template()}
        elif action == "reorder":
            order_list = p.get("order", p.get("order_list", []))
            res = engine.reorder(order_list=order_list)
            return {"success": True, "action": action, "result": res, "template": engine.get_template()}
        elif action == "move_section":
            res = engine.move_section(ordinal=p["ordinal"], target_ordinal=p["target_ordinal"])
            return {"success": True, "action": action, "result": res, "template": engine.get_template()}
        elif action == "add_block":
            target = p.get("section_ordinal_or_id", p.get("section_id", p.get("section_ordinal", 0)))
            res = engine.add_block(
                section_ordinal_or_id=target,
                block_type=p.get("block_type", "block"),
                settings=p.get("settings"),
                block_id=p.get("block_id"),
                after_ordinal=p.get("after_ordinal")
            )
            return {"success": True, "action": action, "result": res, "template": engine.get_template()}
        elif action == "remove_block":
            sec_target = p.get("section_ordinal_or_id", p.get("section_id", p.get("section_ordinal", 0)))
            blk_target = p.get("block_ordinal_or_id", p.get("block_id", p.get("block_ordinal", 0)))
            if sec_target is None:
                sec_target = 0
            if blk_target is None:
                blk_target = 0
            res = engine.remove_block(section_ordinal_or_id=sec_target, block_ordinal_or_id=blk_target)
            return {"success": True, "action": action, "result": res, "template": engine.get_template()}
        elif action == "patch_setting":
            sec_target = p.get("section_ordinal_or_id", p.get("section_id", p.get("section_ordinal", 0)))
            setting_id = str(p.get("setting_id", ""))
            value = p.get("value")
            blk_target = p.get("block_ordinal_or_id", p.get("block_id", p.get("block_ordinal")))
            res = engine.patch_setting(section_ordinal_or_id=sec_target, setting_id=setting_id, value=value, block_ordinal_or_id=blk_target)
            return {"success": True, "action": action, "result": res, "template": engine.get_template()}
        elif action == "json_patch":
            patch_ops = p.get("patch_ops", p.get("ops", []))
            res = engine.apply_json_patch(patch_ops=patch_ops)
            return {"success": True, "action": action, "result": res, "template": engine.get_template()}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported mutation action: {action}")
    except (ValueError, KeyError, IndexError) as e:
        raise HTTPException(status_code=422, detail=f"Mutation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal template mutation error: {str(e)}")


@router.post("/transpile/canvas-node")
def transpile_canvas_node(req: CanvasNodeTranspileRequest) -> Dict[str, Any]:
    """
    Mechanical Transpiler converting Canvas visual node HTML/Tailwind into
    a production-grade Shopify Liquid Section with schema and Open Design styles.
    """
    try:
        res = mechanical_transpiler.transpile(
            html_content=req.html_content,
            section_name=req.section_name or "Canvas Section",
            theme_tokens=req.theme_tokens,
            options=req.options
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transpilation failed: {str(e)}")


@router.post("/validate/section")
def validate_liquid_section(req: SectionValidateRequest) -> Dict[str, Any]:
    """
    Full diagnostic engine and linter for Shopify Liquid Sections.
    Validates tags, schema, settings types, and {{ block.shopify_attributes }} placement.
    """
    try:
        res = liquid_compiler.validate_section_full(req.liquid_code)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Section validation failed: {str(e)}")


# ============================================================================
# Production Hardening Pipeline Endpoints (DNK-ECOM-005)
# ============================================================================

class ShopifyBuildRequest(BaseModel):
    files: Dict[str, str] = Field(..., description="Raw asset files mapping (key -> content)")
    hash_length: int = Field(default=8, description="Length of content hash suffix")
    generate_sri: bool = Field(default=True, description="Generate Subresource Integrity sha384 hashes")


class ShopifyDeployRequest(BaseModel):
    store_domain: str = Field(..., description="Target Shopify myshopify.com domain")
    theme_files: Optional[Dict[str, str]] = Field(default=None, description="Theme files dictionary")
    theme_assets: Optional[Dict[str, str]] = Field(default=None, description="Theme assets dictionary")
    bundle_name: str = Field(default="production_deploy", description="Bundle release tag")


class ShopifyRollbackRequest(BaseModel):
    store_domain: str = Field(..., description="Target Shopify store domain")
    target_release_id: Optional[str] = Field(default=None, description="Target release ID or rollback to previous")


@router.post("/build")
def shopify_vite_build(req: ShopifyBuildRequest) -> Dict[str, Any]:
    """Compiles and hashes theme assets via ShopifyViteBundler."""
    try:
        from apps.api.services.shopify_vite_bundler import ShopifyViteBundler
        bundler = ShopifyViteBundler(hash_length=req.hash_length, generate_sri=req.generate_sri)
        res = bundler.bundle(req.files)
        return {
            "bundle_id": res.bundle_id,
            "manifest": {k: v.model_dump() for k, v in res.manifest.items()},
            "integrity_map": res.integrity_map,
            "stats": res.stats.model_dump(),
            "bundled_files": res.bundled_files,
            "bundled_files_count": len(res.bundled_files),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vite bundle failed: {str(e)}")


@router.post("/deploy")
def shopify_theme_deploy(req: ShopifyDeployRequest) -> Dict[str, Any]:
    """Executes atomic zero-downtime deployment with live snapshotting."""
    try:
        from apps.api.services.shopify_deploy_engine import shopify_deploy_engine
        res = shopify_deploy_engine.deploy(
            store_domain=req.store_domain,
            theme_files=req.theme_files,
            theme_assets=req.theme_assets,
            bundle_name=req.bundle_name,
        )
        return {
            "success": res.success,
            "release": res.release.model_dump() if res.release else None,
            "snapshot": res.snapshot.model_dump() if res.snapshot else None,
            "error_message": res.error_message,
            "error_code": res.error_code,
            "timings": res.step_timings_ms,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deploy failed: {str(e)}")


@router.get("/releases/{store_domain}")
def shopify_list_releases(store_domain: str) -> Dict[str, Any]:
    """Retrieves deployment history and active releases for a store."""
    try:
        from apps.api.services.shopify_deploy_engine import shopify_deploy_engine
        releases = shopify_deploy_engine.list_releases(store_domain)
        return {
            "store_domain": store_domain,
            "count": len(releases),
            "releases": [r.model_dump() for r in releases],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get releases failed: {str(e)}")


@router.post("/rollback")
def shopify_rollback_release(req: ShopifyRollbackRequest) -> Dict[str, Any]:
    """Rolls back store theme to previous stable snapshot or target release."""
    try:
        from apps.api.services.shopify_deploy_engine import shopify_deploy_engine
        res = shopify_deploy_engine.rollback(store_domain=req.store_domain, target_release_id=req.target_release_id)
        return {
            "success": res.success,
            "store_domain": res.store_domain,
            "rollback_release_id": res.rollback_release_id,
            "restored_snapshot_id": res.restored_snapshot_id,
            "restored_assets_count": res.restored_assets_count,
            "error_message": res.error_message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


@router.get("/components/registry")
def get_components_registry() -> Dict[str, Any]:
    """Retrieves the unified 529+ component mega-registry with categories and schemas."""
    try:
        return theme_adapter.build_mega_registry()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load components registry: {str(e)}")


@router.post("/store/synthesize")
def synthesize_store(req: StoreSynthesizeRequest) -> Dict[str, Any]:
    """Autonomous Store Synthesizer: builds full OS 2.0 theme templates (index, product) for a niche."""
    try:
        return store_synthesizer.synthesize_store(
            store_name=req.store_name,
            niche=req.niche,
            theme_tokens=req.theme_tokens
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Store synthesis failed: {str(e)}")


@router.post("/components/adapt-block")
def adapt_legacy_section_to_block(req: AdaptBlockRequest) -> Dict[str, Any]:
    """Adapts a legacy section into a standalone Tinker block file."""
    try:
        res = theme_adapter.adapt_legacy_section_to_tinker_block(
            section_name=req.section_name,
            target_block_name=req.target_block_name
        )
        if not res.get("success", False):
            raise HTTPException(status_code=404, detail=res.get("error", "Adaptation failed"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Block adaptation failed: {str(e)}")


@router.post("/store/export-manifest")
def export_store_manifest(req: StoreExportZipRequest) -> Dict[str, Any]:
    """Calculates theme export statistics and file manifest without downloading the archive."""
    try:
        _, manifest = theme_exporter.export_store_zip(
            store_name=req.store_name,
            niche=req.niche,
            theme_tokens=req.theme_tokens,
            custom_templates=req.custom_templates
        )
        return manifest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theme export manifest failed: {str(e)}")


@router.post("/store/export-zip")
def export_store_zip(req: StoreExportZipRequest):
    """Packages the full synthesized store into a valid Shopify Theme ZIP and returns it as a downloadable stream."""
    try:
        zip_bytes, manifest = theme_exporter.export_store_zip(
            store_name=req.store_name,
            niche=req.niche,
            theme_tokens=req.theme_tokens,
            custom_templates=req.custom_templates
        )
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=\"{manifest['archive_name']}\"",
                "X-Archive-Name": manifest["archive_name"],
                "X-Archive-Size-KB": str(manifest["size_kb"]),
                "X-Total-Files": str(manifest["files_summary"]["total_files"])
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Theme ZIP export failed: {str(e)}")



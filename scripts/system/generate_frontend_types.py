# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_generate_frontend_types"
# purpose: "Automated OpenAPI extraction & TypeScript types generation for apps/web API contracts"
# canonical_source: true
# alters_files: ["apps/web/openapi.json", "apps/web/types/apiGenerated.ts"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("generate_frontend_types")


def get_hub_root() -> Path:
    return Path(__file__).resolve().parents[2]


def export_openapi_json(hub_root: Path, output_path: Path) -> Dict[str, Any]:
    """Imports FastAPI app and dumps the OpenAPI 3.1 JSON schema."""
    logger.info("Extracting OpenAPI schema from apps.api.main:app...")
    sys.path.insert(0, str(hub_root))
    
    # Silence terminal warnings during import
    os.environ["TESTING"] = "1"
    
    from apps.api.main import app
    schema = app.openapi()

    # Deduplicate operationIds to prevent TypeScript identifier collisions
    seen_ops = set()
    for path_item in schema.get("paths", {}).values():
        for method, op in path_item.items():
            if isinstance(op, dict) and "operationId" in op:
                op_id = op["operationId"]
                if op_id in seen_ops:
                    count = 2
                    new_op_id = f"{op_id}_{count}"
                    while new_op_id in seen_ops:
                        count += 1
                        new_op_id = f"{op_id}_{count}"
                    logger.warning(f"Deduplicating operationId: {op_id} -> {new_op_id}")
                    op["operationId"] = new_op_id
                    seen_ops.add(new_op_id)
                else:
                    seen_ops.add(op_id)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Exported OpenAPI schema to {output_path} ({len(schema.get('paths', {}))} paths, {len(schema.get('components', {}).get('schemas', {}))} schemas)")
    return schema


def generate_typescript_with_npx(openapi_json_path: Path, output_ts_path: Path) -> bool:
    """Attempts generation via openapi-typescript CLI."""
    try:
        cmd = [
            "npx", "--yes", "openapi-typescript",
            str(openapi_json_path),
            "-o", str(output_ts_path)
        ]
        logger.info(f"Running {' '.join(cmd)}...")
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            logger.info("Generated TypeScript types using openapi-typescript successfully.")
            return True
        else:
            logger.warning(f"openapi-typescript failed with exit code {res.returncode}: {res.stderr}")
            return False
    except Exception as e:
        logger.warning(f"openapi-typescript execution failed: {e}")
        return False


def generate_typescript_fallback(schema: Dict[str, Any], output_ts_path: Path) -> None:
    """Fallback zero-dependency pure Python TypeScript generator for OpenAPI schemas."""
    logger.info("Generating TypeScript types with internal Python generator...")
    schemas = schema.get("components", {}).get("schemas", {})
    
    lines: List[str] = [
        "// --- DNK-MRH-HEADER ---",
        "// mrh_id: \"apps_web_types_api_generated\"",
        "// purpose: \"Auto-generated TypeScript interfaces from FastAPI OpenAPI Schema\"",
        "// canonical_source: false",
        "// alters_files: []",
        "// triggers_tasks: []",
        "// status: \"Active\"",
        "// version: \"1.0.0\"",
        "// updated_at: \"2026-09-06\"",
        "// author: \"DNK Swarm Auto-Generator\"",
        "// --- END DNK-MRH-HEADER ---",
        "",
        "/* eslint-disable @typescript-eslint/no-explicit-any */",
        "// Auto-generated types from FastAPI OpenAPI schema. Do not edit manually.",
        "",
    ]

    def resolve_type(prop_schema: Dict[str, Any]) -> str:
        if "$ref" in prop_schema:
            ref_name = prop_schema["$ref"].split("/")[-1]
            return ref_name
        if "anyOf" in prop_schema:
            types = [resolve_type(sub) for sub in prop_schema["anyOf"] if sub.get("type") != "null"]
            nullable = any(sub.get("type") == "null" for sub in prop_schema["anyOf"])
            res = " | ".join(types) if types else "any"
            return f"({res}) | null" if nullable else res
        if "oneOf" in prop_schema:
            types = [resolve_type(sub) for sub in prop_schema["oneOf"] if sub.get("type") != "null"]
            nullable = any(sub.get("type") == "null" for sub in prop_schema["oneOf"])
            res = " | ".join(types) if types else "any"
            return f"({res}) | null" if nullable else res
            
        t = prop_schema.get("type")
        if t == "string":
            if "enum" in prop_schema:
                enums = [f"'{val}'" for val in prop_schema["enum"]]
                return " | ".join(enums)
            return "string"
        elif t in ("integer", "number", "float"):
            return "number"
        elif t == "boolean":
            return "boolean"
        elif t == "array":
            items = prop_schema.get("items", {})
            item_type = resolve_type(items)
            return f"{item_type}[]"
        elif t == "object":
            return "Record<string, any>"
        elif t == "null":
            return "null"
        return "any"

    for schema_name, s_def in sorted(schemas.items()):
        if not re.match(r"^[A-Za-z0-9_]+$", schema_name):
            continue
            
        s_type = s_def.get("type", "object")
        title = s_def.get("title", schema_name)
        desc = s_def.get("description", "")
        
        if desc:
            lines.append(f"/** {desc.strip()} */")
            
        if "enum" in s_def:
            vals = " | ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in s_def["enum"])
            lines.append(f"export type {schema_name} = {vals};")
            lines.append("")
            continue
            
        if s_type == "object" or "properties" in s_def:
            lines.append(f"export interface {schema_name} {{")
            props = s_def.get("properties", {})
            required_set = set(s_def.get("required", []))
            
            for p_name, p_def in props.items():
                p_desc = p_def.get("description", "")
                if p_desc:
                    lines.append(f"  /** {p_desc.strip()} */")
                is_req = p_name in required_set
                opt = "" if is_req else "?"
                ts_type = resolve_type(p_def)
                safe_name = f"'{p_name}'" if not p_name.isidentifier() else p_name
                lines.append(f"  {safe_name}{opt}: {ts_type};")
            lines.append("}")
            lines.append("")
        else:
            lines.append(f"export type {schema_name} = {resolve_type(s_def)};")
            lines.append("")

    with open(output_ts_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(f"Wrote fallback TypeScript interfaces to {output_ts_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate TypeScript types from FastAPI OpenAPI schema.")
    parser.add_argument("--json-only", action="store_true", help="Only dump openapi.json, skip TypeScript generation")
    parser.add_argument("--force-fallback", action="store_true", help="Force internal pure-Python generator")
    args = parser.parse_args()

    hub_root = get_hub_root()
    output_json = hub_root / "apps" / "web" / "openapi.json"
    output_ts = hub_root / "apps" / "web" / "types" / "apiGenerated.ts"

    schema = export_openapi_json(hub_root, output_json)

    if args.json_only:
        return 0

    success = False
    if not args.force_fallback:
        success = generate_typescript_with_npx(output_json, output_ts)
        
    if not success:
        generate_typescript_fallback(schema, output_ts)

    logger.info("API Contract Generation Complete! ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())

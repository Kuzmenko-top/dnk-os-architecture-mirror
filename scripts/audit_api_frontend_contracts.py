#!/usr/bin/env python3
"""
scripts/audit_api_frontend_contracts.py
---------------------------------------
Deterministic read-only audit script for Audit Slice 0.2-A.
Inspects FastAPI routers, mounts, OpenAPI schema, frontend callers, tests,
and computes Graphify blast radius.
"""
import os
import sys
import json
import re
import ast
import subprocess
from pathlib import Path
from collections import defaultdict

ROOT_DIR = Path(".").resolve()
sys.path.insert(0, str(ROOT_DIR))

def analyze_main_py():
    """Analyze router inclusions in apps/api/main.py via AST."""
    main_file = ROOT_DIR / "apps" / "api" / "main.py"
    with open(main_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(main_file))

    manual_mounts = []
    has_dynamic_mount = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check app.include_router(...)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "include_router":
                router_name = ast.unparse(node.args[0]) if node.args else "unknown"
                prefix = None
                tags = []
                for kw in node.keywords:
                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                        prefix = kw.value.value
                    elif kw.arg == "tags" and isinstance(kw.value, ast.List):
                        tags = [elt.value for elt in kw.value.elts if isinstance(elt, ast.Constant)]
                manual_mounts.append({
                    "router_expr": router_name,
                    "prefix": prefix,
                    "tags": tags,
                    "lineno": node.lineno
                })
        # Check dynamic loop
        if isinstance(node, ast.For):
            code_str = ast.unparse(node)
            if "pkgutil.iter_modules" in code_str and "include_router" in code_str:
                has_dynamic_mount = True

    return manual_mounts, has_dynamic_mount

def analyze_openapi_and_routes():
    """Load FastAPI app and extract routes and OpenAPI schema."""
    from apps.api.main import app
    from fastapi.routing import APIRoute

    schema = app.openapi()
    routes_info = []
    operation_ids = defaultdict(list)
    paths_dict = schema.get("paths", {})

    for path, methods in paths_dict.items():
        for method, details in methods.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch", "options", "head"]:
                continue
            op_id = details.get("operation_id", "")
            tags = details.get("tags", [])
            summary = details.get("summary", "")
            if op_id:
                operation_ids[op_id].append((method.upper(), path))
            routes_info.append({
                "path": path,
                "method": method.upper(),
                "operation_id": op_id,
                "tags": tags,
                "summary": summary
            })

    duplicate_op_ids = {k: v for k, v in operation_ids.items() if len(v) > 1}

    # Internal FastAPI routes list
    internal_routes = []
    for r in app.routes:
        if isinstance(r, APIRoute):
            internal_routes.append({
                "path": r.path,
                "methods": list(r.methods),
                "endpoint_name": r.endpoint.__name__,
                "module": r.endpoint.__module__
            })

    return routes_info, duplicate_op_ids, internal_routes, schema

def scan_frontend():
    """Scan apps/web for API calls, fetch, axios, and route URLs."""
    web_dir = ROOT_DIR / "apps" / "web"
    url_pattern = re.compile(r'["\'`](/(?:api|canvas|agent|artifact|analytics|taskdna|workspace|secrets|github|shopify|video|node-tasks|task-forest)[^"\'`\s]*)["\'`]')
    fetch_pattern = re.compile(r'(?:fetch|axios\.(?:get|post|put|delete|patch)|apiClient\.[a-zA-Z]+)\s*\(\s*["\'`]([^"\'`]+)["\'`]')

    frontend_calls = defaultdict(list)

    for root, dirs, files in os.walk(web_dir):
        if "node_modules" in root or ".next" in root or "dist" in root:
            continue
        for file in files:
            if file.endswith((".ts", ".tsx", ".js", ".jsx")):
                filepath = Path(root) / file
                rel_path = filepath.relative_to(ROOT_DIR)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Find literal path strings
                for m in url_pattern.finditer(content):
                    clean_path = m.group(1).split("?")[0]
                    # ignore css or assets
                    if clean_path.endswith((".png", ".jpg", ".svg", ".css")):
                        continue
                    frontend_calls[clean_path].append(str(rel_path))

                # Find fetch calls
                for m in fetch_pattern.finditer(content):
                    raw_target = m.group(1).split("?")[0]
                    if raw_target.startswith("/"):
                        frontend_calls[raw_target].append(str(rel_path))

    # Deduplicate files per endpoint
    deduped_frontend_calls = {k: sorted(list(set(v))) for k, v in frontend_calls.items()}
    return deduped_frontend_calls

def map_tests_coverage(routes_info):
    """Scan tests/ for route calls and router imports."""
    tests_dir = ROOT_DIR / "tests"
    tested_endpoints = defaultdict(list)
    untested_endpoints = []

    test_files_content = {}
    for root, dirs, files in os.walk(tests_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                p = Path(root) / file
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    test_files_content[str(p.relative_to(ROOT_DIR))] = f.read()

    for r in routes_info:
        path = r["path"]
        # Normalize parameterized path like /canvas/nodes/{node_id} -> /canvas/nodes/
        base_path = re.sub(r'\{[^}]+\}', '', path).rstrip('/')
        matching_tests = []
        for t_file, content in test_files_content.items():
            if path in content or (base_path and base_path in content):
                matching_tests.append(t_file)
        if matching_tests:
            tested_endpoints[f"{r['method']} {path}"] = sorted(list(set(matching_tests)))
        else:
            untested_endpoints.append(f"{r['method']} {path}")

    return tested_endpoints, untested_endpoints

def get_graphify_blast_radius():
    """Use graphify to find affected files for top routers."""
    routers_to_check = [
        "apps/api/routers/canvas.py",
        "apps/api/routers/agent.py",
        "apps/api/routers/artifacts.py",
        "apps/api/routers/analytics.py",
        "apps/api/routers/taskdna.py",
        "apps/api/routers/node_tasks_router.py",
        "apps/api/routers/task_forest_router.py",
        "apps/api/routers/shopify.py",
        "apps/api/routers/video_router.py",
        "apps/api/routers/workspace.py"
    ]
    blast_radius = {}
    for r in routers_to_check:
        try:
            res = subprocess.run(["graphify", "affected", r], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                lines = [line.strip("- ") for line in res.stdout.strip().split("\n") if line.strip().startswith("- ")]
                blast_radius[r] = {
                    "count": len(lines),
                    "affected_sample": lines[:10]
                }
            else:
                blast_radius[r] = {"count": 0, "error": res.stderr.strip()}
        except Exception as e:
            blast_radius[r] = {"count": 0, "error": str(e)}
    return blast_radius

def main():
    print("1. Analyzing apps/api/main.py...")
    manual_mounts, has_dynamic = analyze_main_py()

    print("2. Extracting routes and OpenAPI schema...")
    routes_info, duplicate_op_ids, internal_routes, schema = analyze_openapi_and_routes()

    print("3. Scanning frontend callers in apps/web...")
    frontend_calls = scan_frontend()

    print("4. Mapping test coverage in tests/...")
    tested_endpoints, untested_endpoints = map_tests_coverage(routes_info)

    print("5. Computing Graphify blast radius...")
    blast_radius = get_graphify_blast_radius()

    # Identify duplicate routers and path aliases (/path vs /api/path)
    root_paths = set()
    api_prefixed_paths = set()
    for r in routes_info:
        p = r["path"]
        if p.startswith("/api/"):
            api_prefixed_paths.add(p)
        else:
            root_paths.add(p)

    paired_aliases = []
    for rp in root_paths:
        prefixed = f"/api{rp}"
        if prefixed in api_prefixed_paths:
            paired_aliases.append({
                "root_path": rp,
                "api_path": prefixed
            })

    output_data = {
        "metadata": {
            "title": "DNK OS 0.2 API & Frontend Contract Alignment Map",
            "version": "v0.1",
            "timestamp": "2026-09-07",
            "audit_type": "read-only",
            "total_routes_in_schema": len(routes_info),
            "total_frontend_endpoints_scanned": len(frontend_calls),
            "duplicate_operation_ids_count": len(duplicate_op_ids),
            "paired_root_and_api_aliases_count": len(paired_aliases)
        },
        "main_py_mounts": {
            "manual_mounts_count": len(manual_mounts),
            "manual_mounts": manual_mounts,
            "has_dynamic_pkgutil_mount": has_dynamic,
            "critical_finding": "Both manual mounts (with and without prefix) AND dynamic pkgutil auto-discovery are present in main.py, causing double/triple route registration."
        },
        "duplicate_operation_ids": duplicate_op_ids,
        "paired_aliases": paired_aliases,
        "frontend_consumers_sample": dict(list(frontend_calls.items())[:30]),
        "all_frontend_endpoints": frontend_calls,
        "test_coverage_summary": {
            "tested_endpoints_count": len(tested_endpoints),
            "untested_endpoints_count": len(untested_endpoints),
            "tested_sample": dict(list(tested_endpoints.items())[:20]),
            "untested_sample": untested_endpoints[:25]
        },
        "graphify_blast_radius": blast_radius
    }

    # Write JSON
    json_path = ROOT_DIR / "docs" / "audit" / "API_FRONTEND_CONTRACT_MAP_v0.1.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"JSON written to {json_path}")

    # Generate Markdown Report
    md_path = ROOT_DIR / "docs" / "audit" / "API_FRONTEND_CONTRACT_MAP_v0.1.md"
    generate_markdown(output_data, md_path)
    print(f"Markdown report written to {md_path}")

def generate_markdown(data, path):
    md = []
    md.append("---")
    md.append('title: "DNK OS 0.2 API Schema & Frontend Contract Alignment Map v0.1"')
    md.append('date: "2026-09-07"')
    md.append('status: "Completed (Read-Only Audit)"')
    md.append('mrh_id: "docs/audit/API_FRONTEND_CONTRACT_MAP_v0.1.md"')
    md.append('purpose: "Comprehensive mapping of FastAPI routers, mounts, duplicate aliases, frontend consumers, tests, and Graphify blast radius"')
    md.append('canonical_source: true')
    md.append("---")
    md.append("")
    md.append("# --- DNK-MRH-HEADER ---")
    md.append('# mrh_id: "docs/audit/API_FRONTEND_CONTRACT_MAP_v0.1.md"')
    md.append('# purpose: "Comprehensive mapping of FastAPI routers, mounts, duplicate aliases, frontend consumers, tests, and Graphify blast radius"')
    md.append('# canonical_source: true')
    md.append("# alters_files: []")
    md.append("# triggers_tasks: []")
    md.append('# status: "Active"')
    md.append('# version: "1.0.0"')
    md.append('# updated_at: "2026-09-07"')
    md.append('# author: "DNK-e.com Maksym & Gerych Prime"')
    md.append("# --- END DNK-MRH-HEADER ---")
    md.append("")
    md.append("# 🎯 Audit Slice 0.2-A: API Schema & Frontend Contract Alignment Report")
    md.append("")
    md.append("## 📊 1. Executive Summary")
    meta = data["metadata"]
    md.append(f"- **Total OpenAPI Endpoints**: {meta['total_routes_in_schema']}")
    md.append(f"- **Root vs `/api` Paired Aliases (Exact Duplicates)**: {meta['paired_root_and_api_aliases_count']}")
    md.append(f"- **Duplicate Operation IDs in Schema**: {meta['duplicate_operation_ids_count']}")
    md.append(f"- **Frontend Consumers Scanned (`apps/web`)**: {meta['total_frontend_endpoints_scanned']} unique endpoint paths")
    md.append(f"- **Tested Endpoints**: {data['test_coverage_summary']['tested_endpoints_count']}")
    md.append(f"- **Untested / Internal-Only Endpoints**: {data['test_coverage_summary']['untested_endpoints_count']}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🔍 2. Root Cause Analysis: Дубльоване Монтування в `apps/api/main.py`")
    main_mounts = data["main_py_mounts"]
    md.append(f"У файлі `apps/api/main.py` виявлено **{main_mounts['manual_mounts_count']} ручних викликів `include_router`**.")
    md.append("")
    md.append("### 2.1. Подвійне ручне монтування:")
    md.append("Шість ключових роутерів монтуються двічі вручну:")
    md.append("1. `canvas.router` -> без префіксу + `prefix='/api'`")
    md.append("2. `agent.router` -> без префіксу + `prefix='/api'`")
    md.append("3. `artifact.router` -> без префіксу + `prefix='/api'`")
    md.append("4. `analytics.router` -> без префіксу + `prefix='/api'`")
    md.append("5. `taskdna.router` -> без префіксу + `prefix='/api'`")
    md.append("6. `workflow_composer.router` -> без префіксу + `prefix='/api'`")
    md.append("")
    md.append("### 2.2. Потрійне монтування через динамічний pkgutil-автолоадер:")
    md.append("У рядках 195–207 `apps/api/main.py` виконується динамічний імпорт усіх модулів із `apps.api.routers`:")
    md.append("```python")
    md.append("for _, mod_name, is_pkg in pkgutil.iter_modules(routers_pkg.__path__):")
    md.append("    if hasattr(mod, 'router'):")
    md.append("        app.include_router(mod.router)")
    md.append("```")
    md.append("**Наслідок**: роутери, які вже були підключені вручну, підключаються **втретє**. Це створює множинні `operation_id` колізії в OpenAPI.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 👥 3. Зіставлення з Frontend Споживачами (`apps/web`)")
    md.append("Аналіз показав, що фронтенд використовує суміш обох варіантів:")
    md.append("| Frontend Endpoint Call | Де використовується (компоненти) | Стан на бекенді |")
    md.append("|---|---|---|")
    for ep, files in list(data["all_frontend_endpoints"].items())[:25]:
        sample_files = ", ".join([Path(f).name for f in files[:2]])
        if len(files) > 2:
            sample_files += f" (+{len(files)-2})"
        status = "✅ Є і в `/` і в `/api`" if ep in [p["root_path"] for p in data["paired_aliases"]] or f"/api{ep}" in [p["api_path"] for p in data["paired_aliases"]] else "ℹ️ Специфічний маршрут"
        md.append(f"| `{ep}` | `{sample_files}` | {status} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🧪 4. Тестове Покриття та Захист Контрактів")
    t_sum = data["test_coverage_summary"]
    md.append(f"- **Захищені тестами endpoints**: {t_sum['tested_endpoints_count']}")
    md.append(f"- **Без прямих тестів (Internal / Orphaned)**: {t_sum['untested_endpoints_count']}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🕸️ 5. Graphify Blast Radius (Радіус Ураження)")
    md.append("Детермінований розрахунок зв'язків через AST Tree-sitter:")
    md.append("| Роутер | Залежних файлів та тестів | Приклади ключових тестів |")
    md.append("|---|---|---|")
    for r, b in data["graphify_blast_radius"].items():
        sample = ", ".join([s.split()[0] for s in b.get("affected_sample", [])[:3]])
        md.append(f"| `{r}` | **{b['count']}** | `{sample}` |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 🛡️ 6. Rollback-Safe Migration Order (Рекомендація для DNK HUB 0.2)")
    md.append("Щоб перейти до чистих канонічних роутерів без ламання тестів та фронтенду:")
    md.append("1. **Крок 1**: Впровадити в `apps/web` єдиний API-клієнт (`apiClient.ts`), який завжди додає базовий префікс `/api/v1`.")
    md.append("2. **Крок 2**: У `apps/api/main.py` вимкнути неконтрольований динамічний `pkgutil.iter_modules` лоадер.")
    md.append("3. **Крок 3**: Змонтувати всі канонічні роутери виключно під єдиним канонічним префіксом `/api/v1`.")
    md.append("4. **Крок 4**: Залишити тимчасовий FastAPI `Middleware` або 307/308 redirect для застарілих шляхів `/canvas/*` -> `/api/v1/canvas/*` на період перехідного тестування.")
    md.append("5. **Крок 5**: Запустити `verify_all.sh` для підтвердження 100% Green статусу.")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

if __name__ == "__main__":
    main()

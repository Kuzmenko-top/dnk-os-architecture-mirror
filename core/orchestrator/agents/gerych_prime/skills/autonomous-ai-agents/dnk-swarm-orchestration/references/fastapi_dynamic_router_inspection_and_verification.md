# --- DNK-MRH-HEADER ---
# mrh_id: "references/fastapi_dynamic_router_inspection_and_verification.md"
# purpose: "FastAPI dynamic router inspection, TestClient probing, and route verification patterns."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# FastAPI Dynamic Router Inspection & Route Verification Protocol

### Context & Problem Statement
In FastAPI 0.115+ and modern Starlette applications where APIRouters are dynamically auto-discovered and mounted (e.g. via `pkgutil.iter_modules()`), inspecting `app.routes` directly to verify route presence can fail:
- **Error**: `AttributeError: '_IncludedRouter' object has no attribute 'path'`
- **Root Cause**: Included routers are wrapped in `fastapi.routing._IncludedRouter` instances rather than plain `starlette.routing.Route` objects. The route path prefix and nested endpoints are stored within `_IncludedRouter.routes` or resolved during URL routing.

### Verified Inspection & Verification Patterns

#### 1. Black-Box HTTP TestClient Probing (Recommended)
The cleanest, most reliable way to verify that a dynamically loaded endpoint is active and answering:
```python
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
response = client.get("/api/v1/rag/canvas-graph?workspace_id=ws-alpha-001")
assert response.status_code in (200, 401, 403, 422)  # Route exists, not 404
```

#### 2. OpenAPI Schema Inspection
When full offline route mapping is required without dispatching test requests:
```python
openapi_schema = app.openapi()
all_paths = openapi_schema.get("paths", {}).keys()
assert any(path.startswith("/api/v1/rag") for path in all_paths)
```

#### 3. Defensive Recursive Route Traversal
If inspecting the internal router tree directly:
```python
def extract_all_routes(routes):
    paths = []
    for r in routes:
        if hasattr(r, "path"):
            paths.append(r.path)
        elif hasattr(r, "routes"):
            paths.extend(extract_all_routes(r.routes))
    return paths

all_registered_paths = extract_all_routes(app.routes)
```

### Invariants
- Never assume an APIRouter is missing just because `[r.path for r in app.routes]` raises an error.
- Always use `TestClient` or `app.openapi()["paths"]` for definitive route verification in integration tests and agent triage.

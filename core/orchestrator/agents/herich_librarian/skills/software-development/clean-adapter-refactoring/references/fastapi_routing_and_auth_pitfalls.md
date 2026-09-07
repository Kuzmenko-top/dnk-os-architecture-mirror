# FastAPI Routing, Auth Middleware & Fixture Fallback Patterns

Detailed reference for building clean, resilient FastAPI routers and adapters with fixture fallbacks.

## 1. Unauthorized Token Fallback to Fixture Data
When integration adapters run in environments with pre-injected tokens (e.g. `$GH_TOKEN`), live HTTP calls to external APIs may fail with 401 Unauthorized (e.g. invalid permissions or expired token).

### Pattern: Intercepting `unauthorized` Error Code
If `allow_fixture_fallback=True` or `FIXTURE_MODE=true` is active, intercept 401/unauthorized errors inside adapter methods:

```python
if error_code == "unauthorized":
    if allow_fixture_fallback or os.getenv("FIXTURE_MODE", "false").lower() == "true":
        return GitHubAdapterResult(
            data=FIXTURE_DATA,
            data_source="fixture",
            stale=False,
            fetched_at=now_iso,
            expires_at=expires_iso,
        )
    return GitHubAdapterResult(
        data=None,
        data_source="live",
        error_code="unauthorized"
    )
```

## 2. FastAPI Wildcard Route Shadowing
In FastAPI and Starlette, route ordering in `main.py` determines matching precedence.

### Anti-Pattern: Wildcard Workspace / ID Routers Before Specific Routers
```python
# BAD: workspace_router has `/{workspace_id}` which intercepts `/api/github` or `/api/timeline`
app.include_router(workspace_router, prefix="/api")
app.include_router(github_router, prefix="/api/github")
```

### Fix: Specific Domain Routers Included First
```python
# GOOD: Specific endpoints registered before wildcard parameter routers
app.include_router(github_router, prefix="/api/github")
app.include_router(timeline_router, prefix="/api/timeline")
app.include_router(workspace_router, prefix="/api")
```

## 3. Middleware Exclusions Alignment
When adding new read-only API routers (e.g. `/api/github`, `/api/timeline`), ensure security middleware (`SecurityMiddleware`) exclusions are updated:

```python
if (
    path in ("/docs", "/redoc", "/openapi.json", "/")
    or path.startswith("/ws")
    or path.startswith("/api/cabinet")
    or path.startswith("/api/github")
    or path.startswith("/api/timeline")
):
    return await call_next(request)
```

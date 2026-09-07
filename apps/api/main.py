# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_main"
# purpose: "Main entrypoint for FastAPI backend mounting routers, security, tenant routing middleware, and collaboration WebSockets"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.3.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import (
    canvas,
    agent,
    artifact,
    analytics,
    taskdna,
    workspace,
    secrets_vault,
    admin_security,
    workspace_collaboration,
    github,
    timeline,
    workspace_analytics,
    analytics_alerting,
    analytics_forecasting,
    worker_management,
    shopify,
    video_router,
    whiteboard_router,
    product_launch,
    patent_shield,
    memory_l3,
    workflow_composer,
    swarm_resilience_router,
    distiller,
)
from apps.api.routers.workspace import handle_workspace_websocket
from core.decorators.security_gate import SecurityGateDenied
from apps.api.middleware.security import SecurityMiddleware
from apps.api.middleware.tenant_router import TenantRouterMiddleware
from apps.api.logging.structured_logger import TraceMiddleware
from apps.api.db.database import db_manager
from apps.api.services.redis_client import redis_client
from apps.api.services.redis_pubsub import pubsub_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database & Redis connections
    await db_manager.connect()
    await redis_client.init()
    await pubsub_manager.init()
    yield
    # Shutdown: Graceful connection teardown
    await pubsub_manager.close()
    await redis_client.close()
    await db_manager.disconnect()


app = FastAPI(
    title="DNK OS Visual Shell MVP API",
    version="0.1.0",
    lifespan=lifespan
)

# Trace Middleware for Distributed Tracing & Logging
app.add_middleware(TraceMiddleware)

# Tenant Routing & Sharding Middleware
app.add_middleware(TenantRouterMiddleware)

# Security Middleware
app.add_middleware(SecurityMiddleware)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiter Middleware (DDoS & Brute-Force protection with Redis & in-memory failover)
from apps.api.middleware.rate_limit import RateLimiterMiddleware
app.add_middleware(RateLimiterMiddleware)

# Prometheus Metrics Instrumentation
import time
from fastapi import Response
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    from apps.api.monitoring.metrics import metrics_registry
    HAVE_PROMETHEUS = True
except ImportError:
    HAVE_PROMETHEUS = False
    Counter = Histogram = generate_latest = CONTENT_TYPE_LATEST = None
    metrics_registry = None

if HAVE_PROMETHEUS and Counter and Histogram:
    HTTP_REQUESTS_TOTAL = Counter(
        "http_requests_total",
        "Total HTTP requests processed by method, endpoint, and status",
        ["method", "endpoint", "status"],
    )
    HTTP_REQUEST_DURATION_SECONDS = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration in seconds by method and endpoint",
        ["method", "endpoint"],
    )
else:
    HTTP_REQUESTS_TOTAL = None
    HTTP_REQUEST_DURATION_SECONDS = None

@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    if request.url.path in ("/metrics", "/favicon.ico"):
        return await call_next(request)
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    # Normalize route path to prevent high cardinality
    route = request.scope.get("route")
    endpoint = route.path if route and hasattr(route, "path") else request.url.path.split("?")[0]
    status = str(response.status_code)
    try:
        if HTTP_REQUESTS_TOTAL:
            HTTP_REQUESTS_TOTAL.labels(method=request.method, endpoint=endpoint, status=status).inc()
        if HTTP_REQUEST_DURATION_SECONDS:
            HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, endpoint=endpoint).observe(duration)
    except Exception:
        pass
    return response

@app.get("/metrics", tags=["Monitoring"], include_in_schema=False)
def get_prometheus_metrics():
    """Prometheus exposition format metrics endpoint for scraping."""
    if not HAVE_PROMETHEUS or metrics_registry is None:
        return Response(content="# Prometheus metrics not available\n", media_type="text/plain")
    return Response(content=metrics_registry.export_metrics(), media_type=CONTENT_TYPE_LATEST)

# Exception handler for Security Gate denials
@app.exception_handler(SecurityGateDenied)
async def security_gate_denied_handler(request: Request, exc: SecurityGateDenied):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc), "error_type": "SecurityGateDenied"}
    )

# Include routers
app.include_router(canvas.router)
app.include_router(canvas.router, prefix="/api")
app.include_router(agent.router)
app.include_router(agent.router, prefix="/api")
app.include_router(artifact.router)
app.include_router(artifact.router, prefix="/api")
app.include_router(analytics.router)
app.include_router(analytics.router, prefix="/api")
app.include_router(taskdna.router)
app.include_router(taskdna.router, prefix="/api")
app.include_router(workspace.router)
app.include_router(secrets_vault.router)
app.include_router(admin_security.router)
app.include_router(workspace_collaboration.router)
app.include_router(github.router)
app.include_router(timeline.router)
app.include_router(workspace_analytics.router)
app.include_router(analytics_alerting.router)
app.include_router(analytics_forecasting.router)
app.include_router(worker_management.router)
app.include_router(shopify.router)
app.include_router(video_router.router)
app.include_router(whiteboard_router.router)
app.include_router(product_launch.router)
app.include_router(patent_shield.router)
app.include_router(memory_l3.router)
app.include_router(workflow_composer.router)
app.include_router(workflow_composer.router, prefix="/api")
app.include_router(swarm_resilience_router.router)
from apps.api.routers import swarm_ws
from apps.api.routers import node_tasks_router
from apps.api.routers import task_forest_router
from apps.api.routers import canvas_bridge
app.include_router(swarm_ws.router)
app.include_router(node_tasks_router.router)
app.include_router(task_forest_router.router)
app.include_router(canvas_bridge.router)

# Dynamically discover and mount all available routers in apps.api.routers
import importlib
import pkgutil
import apps.api.routers as routers_pkg

for _, mod_name, is_pkg in pkgutil.iter_modules(routers_pkg.__path__):
    if not is_pkg and not mod_name.startswith("__"):
        try:
            mod = importlib.import_module(f"apps.api.routers.{mod_name}")
            if hasattr(mod, "router"):
                app.include_router(mod.router)
        except Exception:
            pass


@app.websocket("/ws/workspaces/{workspace_id}")
async def ws_workspace_endpoint(websocket: WebSocket, workspace_id: str):
    await handle_workspace_websocket(websocket, workspace_id)

@app.get("/")
@app.get("/health")
@app.get("/api/health")
def read_root():
    return {"status": "ok", "service": "DNK OS Visual Shell MVP", "version": "5.0.0"}

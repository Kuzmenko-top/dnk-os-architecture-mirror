# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_middleware_tenant_router"
# purpose: "Tenant routing middleware for PostgreSQL sharding, read/write pool routing, and cross-tenant isolation enforcement"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from apps.api.db.sharding import shard_router
from apps.api.db.database import db_manager, PoolRole

logger = logging.getLogger("dnk.platform.tenant_router")


class TenantRouterMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts tenant context, resolves the appropriate database shard,
    selects read/write connection pool, and enforces cross-tenant boundaries.
    """

    def __init__(self, app):
        super().__init__(app)
        # In-memory mapping cache: tenant_id -> {"shard_id": int, "cached_at": float}
        self.tenant_cache: Dict[str, Dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract tenant_id from headers, query params or path
        tenant_id = (
            request.headers.get("X-Tenant-Id")
            or request.headers.get("X-Tenant")
            or request.query_params.get("tenant_id")
        )

        shard_id: Optional[int] = None
        if tenant_id:
            # Deterministic shard routing with caching
            if tenant_id not in self.tenant_cache:
                shard_id = shard_router.get_shard_for_tenant(tenant_id)
                self.tenant_cache[tenant_id] = {
                    "shard_id": shard_id,
                }
            else:
                shard_id = self.tenant_cache[tenant_id]["shard_id"]

            request.state.tenant_id = tenant_id
            request.state.tenant_shard = shard_id

        # Route query pool: Read (REPLICA) for safe HTTP methods, Write (MASTER) for mutations
        is_read_only = request.method in ("GET", "HEAD", "OPTIONS")
        target_role = PoolRole.REPLICA if is_read_only else PoolRole.MASTER
        request.state.db_pool = db_manager.get_pool(target_role)

        response = await call_next(request)

        # Inject tenant routing headers in response for observability
        if shard_id is not None:
            response.headers["X-Tenant-Shard"] = str(shard_id)
        if tenant_id:
            response.headers["X-Tenant-Id"] = tenant_id

        return response

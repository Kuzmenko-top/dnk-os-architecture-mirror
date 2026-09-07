# Horizontal Scaling, Tenant Sharding & Multi-Node Pub/Sub Architecture

## Overview
A guide for scaling multi-tenant realtime applications across multiple FastAPI nodes, PostgreSQL Read Replicas, Tenant Shard Clusters, and Redis Pub/Sub event buses.

## 1. PostgreSQL Read Replicas Router (`DatabaseManager`)
- **Master Pool (`PoolRole.MASTER`):** Handles all write operations and fallback queries.
- **Replica Pools (`PoolRole.REPLICA`):** Round-robin read query distribution across active replicas (`DATABASE_REPLICA_URLS`).
- **Graceful Fallback:** Automatically redirects read queries to Master when no active replicas are available or initialized.
- **Mock Safety in Unit Tests:** When filtering `[p for p in replica_pools if p and not getattr(p, "_closed", False)]`, use `getattr(p, "_closed", False)` rather than `p._closed` because `MagicMock._closed` evaluates to truthy (`bool(MagicMock()) == True`), causing active mocks to be silently filtered out.

## 2. Deterministic Tenant Sharding (`TenantShardRouter`)
- **Hash Sharding:** Deterministically maps `tenant_id` to a target database shard `shard_0`, `shard_1`, ..., `shard_N-1` via `md5(tenant_id) % num_shards`.
- **Pool Caching:** Lazily creates and caches database connection pools per shard.
- **Middleware Extraction:** `TenantRouterMiddleware` inspects `X-Tenant-Id` header, determines the database shard, sets `request.state.tenant_id` and `request.state.tenant_shard`, and appends `X-Tenant-Shard` to HTTP response headers.

## 3. Redis Cluster Slot Pinning & Hash Tags
- **Slot Pinning (`{workspace_id}`):** Wrap workspace identifiers in curly braces `{workspace_id}` for Redis Pub/Sub channels and lock keys:
  - Pub/Sub Channel: `dnk:ws:{workspace_id}` (e.g. `f"dnk:ws:{{{workspace_id}}}"`)
  - Section Lock: `dnk:lock:{workspace_id}:{section_id}` (e.g. `f"dnk:lock:{{{workspace_id}}}:{section_id}"`)
- **Template Consistency:** Ensure string formatting templates in `subscribe()` and `publish()` match exactly. Mis-matched braces cause messages to publish to `dnk:ws:ws-alpha` while subscribers listen on `dnk:ws:{ws-alpha}`.

## 4. Cross-Node WebSocket Pub/Sub Broadcast
- **Echo Suppression:** Include `origin_node` in the envelope payload. When receiving cross-node events via Redis Pub/Sub, nodes discard messages originating from `self.node_id` to avoid infinite broadcast loops.
- **Async Listener Loop:** Use `async for msg in ps.listen():` inside background tasks instead of polling with `get_message(timeout=...)` to avoid message delivery delays and test hangs.
- **Event Loop Management:** In singleton Redis clients, verify `asyncio.get_running_loop() == self._loop`. Reinitialize standalone/cluster connections when running across isolated test event loops.
- **In-Memory Fallback:** When Redis is unavailable or unconfigured, fallback to an in-memory event bus or local broadcast mode to keep local unit tests and developer environments fast and isolated.

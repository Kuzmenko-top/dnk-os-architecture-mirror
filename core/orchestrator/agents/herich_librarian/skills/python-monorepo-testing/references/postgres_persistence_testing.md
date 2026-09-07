# 🗄️ PostgreSQL Persistence and connection pool testing in Python Monorepos

## 🎯 Context
This reference file details the patterns and practices for configuring, verifying, and testing the database connection pool using the pure `asyncpg` engine and SQLAlchemy 2.0 inside a nested monorepo structure (e.g., `DNK_HUB` under `DNK_HUB`).

---

## 🛠️ Connection & Codec Initialization Pattern

When using `asyncpg` directly with a connection pool, always ensure that custom JSON/JSONB encoders and decoders are set on the connection initialization stage to safely handle PostgreSQL database objects:

```python
import json
import asyncpg

async def init_connection(conn):
    # Register custom JSONB encoder/decoder
    await conn.set_type_codec(
        'jsonb',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )
    # Register custom JSON encoder/decoder
    await conn.set_type_codec(
        'json',
        encoder=json.dumps,
        decoder=json.loads,
        schema='pg_catalog'
    )

# Create high-performance asyncpg pool
pool = await asyncpg.create_pool(
    dsn="postgresql://postgres:password@localhost:5432/dnk_hub",
    min_size=5,
    max_size=20,
    timeout=30.0,
    init=init_connection
)
```

---

## 🏎️ Dynamic Protocol Conversion (asyncpg integration)

SQLAlchemy 2.0 URLs often default to the `postgresql://` protocol (blocking/sync driver). For `asyncpg` (non-blocking async driver), the protocol must be dynamically replaced with `postgresql+asyncpg://`:

```python
import os

DATABASE_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:password@localhost:5432/dnk_hub")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
```

---

## 🧪 pytest Execution with Database Integrations

### Local Docker DB Detection
To locate and inspect running pgvector or Postgres Docker containers on macOS/Linux:

```bash
docker ps
# Inspect container variables
docker inspect dnk-db | grep POSTGRES_
```

### Path-Safe Monorepo Command
To execute integration tests requiring correct parent-directory module resolution (such as nested imports in `DNK_HUB` relying on `DNK_HUB` structures), prepend parent paths to `PYTHONPATH`:

```bash
PYTHONPATH=. ./.venv/bin/pytest tests/workspace -v
```

All 61 workspace state mutation, OCC commit, rollback, and kill-switch verification tests passed cleanly using this localized execution method.

---

## 👥 Multi-Workspace Collaboration & OCC Context Switching

### Database Schema Design
When implementing multi-tenant collaboration, split mapping into three tables:
1. `workspace_members` — tracks active memberships and RBAC roles (`admin`, `developer`, `viewer`).
2. `workspace_invitations` — tracks cryptographic ticket flow (`pending`, `accepted`, `rejected`, `expired`).
3. `user_workspace_context` — tracks active workspace selected by the user with a sequential `version` counter.

### Optimistic Concurrency Control (OCC) Pattern
To prevent lost updates during high-concurrency switching, enforce version matching on context update:
```python
# Check expected version against current record version
if current_record and expected_version is not None and expected_version != current_record["version"]:
    raise ValueError(f"OCC_CONFLICT: expected version {expected_version}, current is {current_record['version']}")

# Execute atomic update incrementing version
res = await conn.execute(
    "UPDATE user_workspace_context SET active_workspace_id = $1, version = $2 WHERE user_id = $3 AND version = $4",
    active_workspace_id, next_version, user_id, current_record["version"]
)
if "UPDATE 0" in res:
    raise ValueError("OCC_CONFLICT: Concurrent update detected")
```

### AuthProvider Sync Bridge
To bridge token-based OAuth/JWT middleware and active database membership records, synchronize changes made in `WorkspaceMembershipService` immediately into the stateful `AuthProvider` or `USER_REGISTRY` so that HTTP/WebSocket connection checkers have zero-latency access to updated workspaces list:
```python
# When adding/removing member:
user = auth_provider.get_user(target_user_id)
if user:
    ws_list = set(user.get("workspaces", []))
    ws_list.add(workspace_id) # or ws_list.discard(workspace_id)
    auth_provider.update_user(target_user_id, workspaces=list(ws_list))
```

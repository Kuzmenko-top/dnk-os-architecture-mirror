---
name: clean-adapter-refactoring
description: "Use when REDUCE/SPLIT strategy is needed on dirty PRs."
version: "1.0.0"
author: "DNK OS Gerych"
license: "MIT"
metadata:
  hermes:
    tags: ["adapter-pattern", "pr-refactoring", "reduce-split", "clean-architecture", "security-invariants", "fastapi"]
    related_skills: ["software-development/requesting-code-review", "software-development/systematic-debugging"]
---

# Clean Adapter Refactoring & REDUCE/SPLIT Strategy

A class-level architectural guide for resolving rejected, mixed-scope, or dirty pull requests by executing the REDUCE/SPLIT strategy to build isolated, server-side read-only adapters.

## When to Use

- A PR is rejected in review due to scope creep (e.g. mixing frontend web cabinet UI files with server-side backend adapters).
- Security middleware (e.g. `apps/api/middleware/security.py`) was unauthorizedly modified, downgraded, or injected with hardcoded default fallback secrets.
- Missing outbound network transport abstractions or lack of explicit domain contracts (e.g. PR, check runs, changed files models).
- The PR has a `DIRTY` mergeable state or missing CI check runs.

## Core Architectural Pillars

### 1. The REDUCE/SPLIT Strategy
Instead of attempting iterative patch fixes on a 20+ file dirty PR:
1. **Reject & Supersede**: Reject the dirty PR and open a fresh feature branch baselined directly on current `main`:
   ```bash
   git fetch origin
   git checkout -b feature/<task-id>-clean origin/main
   ```
2. **Scope Boundary Reversion**: Delete/revert all unauthorized frontend assets (`apps/web/**`) and legacy evidence files. Keep strictly allowed server-side files.
3. **Pristine Security Restoration**: Restore security middleware files directly from `main`. Ensure zero hardcoded fallback keys or CORS removals.

### 2. Dedicated Transport Layer Abstraction
Decouple outbound HTTPS communication from adapter domain logic using an Abstract Base Class (ABC) transport layer:

```python
class BaseGitHubTransport(ABC):
    @abstractmethod
    def get(self, endpoint: str) -> Tuple[int, Dict[str, Any]]:
        pass

class HttpGitHubTransport(BaseGitHubTransport):
    def __init__(self, token: str, timeout_seconds: float = 10.0):
        self.token = token
        self.timeout = timeout_seconds

    def get(self, endpoint: str) -> Tuple[int, Dict[str, Any]]:
        # Handles socket.timeout, TimeoutError, urllib.error.HTTPError, URLError
        # Maps HTTP statuses: 401/403 -> unauthorized, 404 -> not_found, 429 -> rate_limit, 5xx -> upstream_5xx
```

### 3. Pydantic Domain Contracts, Zero-Egress FIXTURE_MODE & Resilient Caching
- **Domain Contracts & Uniform Metadata Container**: Define clean, normalized schemas wrapped in a standardized adapter result envelope:
  - `data_source`: `"live"` | `"cache"` | `"fixture"`
  - `stale`: `bool` (true when returning expired cache during upstream outage)
  - `error_code`: `None` | `"timeout"` | `"rate_limit"` | `"upstream_5xx"` | `"unauthorized"` | `"not_found"` | `"forbidden_repo"` | `"forbidden_store"`
- **FIXTURE_MODE Invariant**: When `FIXTURE_MODE=true`, guarantee 100% zero outbound network egress by returning deterministic mock payloads immediately.
- **Fail-Closed In-Memory Cache (M1)**: Cache normalized API responses in-memory with TTL (e.g. 60s for listings, 300s for static assets). Fallback hierarchy: `live -> cache (valid/stale) -> fixture (if permitted) -> controlled error`. Redis caching is introduced only after proven scale requirement.
- **Target Allowlists & Security Boundary**: Enforce strict server-side domain/repository allowlists (`ALLOWED_REPOSITORIES`, `ALLOWED_SHOPIFY_STORES`). Reject unauthorized targets with HTTP 403 / `forbidden_*`. Pass tokens strictly server-side (never leak to browser or logs). Zero mutations allowed on read-only adapters.
- **AST Static Analysis Contract Tests**: For read-only adapters, enforce the zero-mutation invariant at test time via Python AST static analysis (`ast.NodeVisitor`). Scan for forbidden HTTP verbs (`POST`, `PUT`, `DELETE`), GraphQL `mutation` strings, or mutation method calls before running against live/mock transport.
- **Leaky Bucket Rate-Limit Telemetry**: Parse rate limit headers (e.g., `X-Shopify-Shop-Api-Call-Limit: 1/40`) in the transport layer, expose current usage/capacity in response metadata envelopes, and surface capacity meters in frontend UI components.

### 4. Verification & Audit Evidence
- **Local Test Suite**: Run unit and integration tests with explicit `PYTHONPATH` handling:
  ```bash
  PYTHONPATH=. uv run pytest tests/<task_dir>/
  ```
- **Evidence JSON**: Generate structured, verifiable audit evidence matching the clean commit HEAD SHA, base SHA, strict security invariants, and passed test metrics.

## Pitfalls & Anti-Patterns

- **Pydantic v2 Serialization & Migration (`.dict()` vs `.model_dump()`)**: In Pydantic v2, `.dict()` is deprecated/removed. Calling `payload.dict()` in routers or service adapters raises runtime `AttributeError`. Always use `payload.model_dump(exclude_unset=True)` or `TypeAdapter` validation.
- **Dynamic Path Hygiene in Automation Scripts**: Hardcoding absolute developer home directories (e.g., `/Users/<username>/...` or `/home/<user>/...`) in bash scripts or test fixtures violates path hygiene gates. Always dynamically anchor to the script directory via `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` or `Path(__file__).resolve().parent`.
- **Iterative Patching on Dirty PRs**: Trying to fix merge conflicts and out-of-scope files on a contaminated branch leads to stale commits and reviewer rejections.
- **Hardcoded Fallback Keys**: Injecting default fallback secrets (e.g. `dnk_secret_key_2026`) into security middleware introduces critical vulnerabilities.
- **Coupling Transport to Business Logic**: Making direct `urllib` / `httpx` calls inside API routers makes unit testing difficult and bypasses centralized timeout handling.
- **Top-Level TestClient Instantiation**: Instantiating `client = TestClient(app)` at module scope in test files can cause route registration mismatch if routes/middlewares dynamically initialize. Use a pytest `@pytest.fixture` to return `TestClient(app)`.
- **Missing Middleware Exclusions for Read-Only APIs**: When introducing new read-only endpoints (e.g., `/api/github`, `/api/timeline`), verify `SECURITY_EXCLUDED_PATHS` or pass full workspace authentication headers (`X-API-Key`, `X-Workspace-ID`) in test runners to avoid unexpected HTTP 401 failures.
- **Router Inclusion Order & Wildcard Route Shadowing**: Registering routers with catch-all or single parameter paths (`/{workspace_id}`) before specific domain routers (`/api/github`, `/api/timeline`) in `main.py` causes Starlette to shadow specific endpoints with 404s. Register specific domain routers first.
- **Unhandled Unauthorized Tokens in Fixture Fallback**: When local environment tokens (e.g. `GH_TOKEN`) are present but unauthorized/expired, transport calls return 401. Intercept `unauthorized` errors and return mock fixture data when `allow_fixture_fallback=True` or `FIXTURE_MODE=true` is requested.

## Supporting Documentation

- See `references/reduce_split_protocol.md` for rejection/superseding steps, transport error mapping details (401/403, 404, 429, 5xx, timeouts), and stale cache fallback behavior.
- See `references/fastapi_routing_and_auth_pitfalls.md` for FastAPI route ordering, security middleware exclusions, and fixture fallback handling under invalid environment credentials.


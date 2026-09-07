# REDUCE/SPLIT Protocol & Network Transport Specifications

Detailed reference protocol for executing clean server-side adapter refactoring on rejected or scope-contaminated PRs.

## 1. Rejection & Superseding Protocol
- **Trigger**: Mentor review or CI audit flags mixed scope (e.g. `apps/web/**` UI files inside an API adapter PR) or security middleware regressions (`apps/api/middleware/security.py`).
- **Action**: Do not attempt inline cleanups on the dirty branch.
  1. Record rejection status on the existing PR.
  2. Create a clean worktree / feature branch baselined directly on `main`:
     ```bash
     git fetch origin
     git checkout -b feature/<task-id>-clean origin/main
     ```
  3. Re-implement strictly allowed server-side files.
  4. Push clean commit and open a superseding PR.

## 2. Network Transport Error Mapping Table
When implementing `BaseGitHubTransport` or similar HTTP abstractions:

| HTTP Status / Exception | Mapped Error Code | Internal Handling |
|---|---|---|
| `HTTPError 401`, `403` | `unauthorized` | Log security warning, fail closed |
| `HTTPError 404` | `not_found` | Return empty envelope or raises `NotFoundError` |
| `HTTPError 429` | `rate_limit` | Log rate limit, serve stale cache if available |
| `HTTPError 500..599` | `upstream_5xx` | Serves stale cache if available, else raise exception |
| `socket.timeout`, `TimeoutError` | `timeout` | 10s default threshold, fallback to stale cache |
| `URLError` | `connection_error` | Handle connection failure gracefully |

## 3. Caching, FIXTURE_MODE & Fallback Hierarchy
- **Primary In-Memory Cache**: Local dictionary with timestamp TTL checking (default 60s for listings, 300s for static assets). Avoid premature distributed cache (Redis) until M1 scale metrics prove necessity.
- **FIXTURE_MODE Contract**: If `FIXTURE_MODE=true` is set in the environment, bypass all network calls and return deterministic fixture data with `data_source: "fixture"`, guaranteeing zero outbound network egress.
- **Uniform Adapter Result Envelope**:
  ```python
  class AdapterResult(BaseModel):
      data: Optional[Any] = None
      data_source: Literal["live", "cache", "fixture"]
      stale: bool = False
      fetched_at: str
      expires_at: str
      error_code: Optional[str] = None
  ```
- **Fallback Hierarchy**: `live -> cache (valid/stale) -> fixture (if allow_fixture_fallback=True) -> controlled error`.
- **Rate-Limit Governance**: Track rate limit headers (e.g. `X-Shopify-Shop-Api-Call-Limit` or GitHub rate limits). On 429 or threshold saturation, perform backoff, return stale cache if available, or populate `error_code: "rate_limit"`.


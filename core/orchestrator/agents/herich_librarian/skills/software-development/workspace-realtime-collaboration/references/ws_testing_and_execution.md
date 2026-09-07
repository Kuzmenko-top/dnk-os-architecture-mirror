# WebSocket Testing & Execution Best Practices for Workspace Real-Time Collaboration

## 1. Virtual Environment & Test Execution Trap
- **Issue:** Running bare `pytest` in terminal can invoke the system Python interpreter instead of the workspace virtualenv, causing missing dependencies like `ModuleNotFoundError: No module named 'asyncpg'`.
- **Solution:** Always invoke test runs using `uv run pytest tests/workspace/...` or explicitly source `.venv/bin/activate` before test invocation.

## 2. Testing WebSockets with Starlette TestClient
- Use `TestClient.websocket_connect(f"/ws/workspaces/{id}?token={token}") as ws:` to simulate real-time client connections.
- When multiple clients connect concurrently, manage nested `with` blocks:
  ```python
  with client.websocket_connect(f"/ws/workspaces/{ws_id}?token={token_a}") as ws_a:
      with client.websocket_connect(f"/ws/workspaces/{ws_id}?token={token_b}") as ws_b:
          # ws_a receives join event for user B
          join_event = ws_a.receive_json()
          assert join_event["type"] == "presence:join"
  ```
- Clear locks and collaboration hubs between test cases via `pytest.fixture(autouse=True)` to prevent cross-test contamination.

## 3. E2E Integration Testing & Security Gate Fixtures
- **User Pre-Registration:** When using `generate_test_token(user_id=..., tenant_id=..., roles=...)`, ensure the user is actively registered in the `auth_provider` (e.g. `auth_provider.register_user(...)`), otherwise `get_current_active_user` or RBAC dependencies reject requests with 401/403.
- **Security Header Consistency:** When hitting workspace REST routes under security gates, pass matching headers:
  ```python
  headers = {
      "Authorization": f"Bearer {token}",
      "X-Tenant-Id": tenant_id,
      "X-Workspace-Id": workspace_id,
  }
  ```
  Mismatch between `X-Workspace-Id` and URL path `/{workspace_id}/...` triggers security tampering rejections (403 Forbidden).
- **OCC Graph State Invariants:** Test OCC auto-merge and conflict resolution scenarios with standardized dictionary states:
  ```python
  {"nodes": [...], "edges": [...], "version": N}
  ```


# Monorepo Import Isolation & Zero-Network Egress Testing

## 1. Pytest PYTHONPATH Isolation in Monorepos

When executing test suites inside a sub-project of a monorepo (e.g. `DNK_HUB/` inside `DNK_HUB/`), `pyproject.toml` or `pytest.ini` must restrict `pythonpath` to `["."]` rather than `[".", ".."]`.

If `"..."` is present in `pythonpath`, `sys.path` will resolve module imports from parent folders (e.g., `DNK_HUB/apps/`) instead of the active sub-project (e.g., `apps/`), causing subtle import mismatches and test failures.

### Recommended `pyproject.toml` configuration:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

When executing `pytest` via CLI:
```bash
PYTHONPATH=. .venv/bin/pytest tests/
```

## 3. Dynamic Relative Root Hygiene

When verifying paths in monorepo test suites (e.g., `test_no_raw_user_absolute_paths`):

- Never hardcode user home directories (e.g. `/Users/username/...` or `/home/username/...`) in source code or untracked test scripts.
- Use dynamic root resolution via `Path(__file__).resolve().parents[N]` or `Path.home()` relative paths to ensure tests pass across different developer environments and CI runners.


## 2. Zero-Network Egress & Fixture Isolation

To ensure unit/integration tests do not execute live network requests against external APIs or infrastructure (GitHub REST API, Vault, PostgreSQL, Redis):

1. **Assert Network Call Count in Tests**:
   Monkeypatch socket creation to verify zero outbound network calls:
   ```python
   def test_zero_network_egress(monkeypatch):
       monkeypatch.setenv("FIXTURE_MODE", "true")
       network_calls = 0

       def fail_on_socket(*args, **kwargs):
           nonlocal network_calls
           network_calls += 1
           raise RuntimeError("Outbound network call detected during fixture mode execution")

       monkeypatch.setattr(socket, "create_connection", fail_on_socket)
       monkeypatch.setattr(socket.socket, "connect", fail_on_socket)

       # Run requests through TestClient
       res = client.get("/api/endpoint")
       assert network_calls == 0
   ```

2. **Short-Circuit Transports & Clients on `FIXTURE_MODE`**:
   In low-level HTTP transports and service clients (e.g. `github_transport.py`, `vault_client.py`, `database.py`), check `FIXTURE_MODE` env flag to return offline mocks or skip live connection attempts:
   ```python
   if os.getenv("FIXTURE_MODE", "false").lower() == "true":
       return None, 503, "fixture_mode_offline"
   ```

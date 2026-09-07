# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_workspace_runtime_integration.py"
# purpose: "Runtime integration simulation test suite for Workspace Auth, Tenant Isolation, Abort, and Health Polling"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-VISUAL-OS-001"]
# status: "Approved"
# version: "2.4.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import re
import uuid
import pytest

UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
ZERO_UUID = "00000000-0000-0000-0000-000000000000"


def is_valid_workspace_uuid(val: str | None) -> bool:
    if not val or not isinstance(val, str):
        return False
    trimmed = val.strip()
    if trimmed == ZERO_UUID:
        return False
    return bool(UUID_REGEX.match(trimmed))


def sanitize_and_inject_headers(
    base_headers: dict | None,
    canonical_ws_id: str,
    auth_token: str | None = None,
) -> dict:
    if not is_valid_workspace_uuid(canonical_ws_id):
        raise ValueError(f"Invalid UUID: {canonical_ws_id}")

    headers = {k: v for k, v in (base_headers or {}).items()}
    for k in list(headers.keys()):
        if k.lower() in ("x-workspace-id", "x-workspace-uuid"):
            del headers[k]

    headers["X-Workspace-Id"] = canonical_ws_id

    if auth_token and isinstance(auth_token, str) and auth_token.strip():
        clean_token = auth_token.strip()
        bearer_val = clean_token if clean_token.startswith("Bearer ") else f"Bearer {clean_token}"
        headers["Authorization"] = bearer_val

    return headers


def map_discovery_response_status(status_code: int, payload: list | dict | None) -> tuple[str, str]:
    if status_code == 401:
        return "unauthorized", "401 Unauthorized: Session expired or authentication token missing."
    if status_code == 403:
        return "forbidden", "403 Forbidden: Access denied to workspace directory."
    if status_code >= 500 or status_code != 200:
        return "degraded", f"Workspace discovery error: HTTP {status_code}"
    if not isinstance(payload, list):
        return "degraded", "Malformed workspace discovery response."

    valid_items = [
        item for item in payload if isinstance(item, dict) and is_valid_workspace_uuid(item.get("id"))
    ]
    if not valid_items:
        return "missing_context", "No authorized workspaces available for this account."

    return "authenticated", "Success"


class MockWorkspaceRuntimeClient:
    """Simulates runtime client behavior of apiClient.js and workspaceContext.js."""

    def __init__(self, initial_token: str | None = None, initial_workspace_id: str | None = None):
        self.auth_token = initial_token
        self.active_workspace_id = initial_workspace_id
        self.auth_status = "initializing"
        self.auth_error: str | None = None
        self.workspaces: list = []
        self.scoped_data: dict = {}
        self.telemetry = {"dnkApi": "unknown", "postgres": "unknown", "redis": "unknown"}
        self.aborted_requests = 0

    def bootstrap(self, server_workspaces_response: list | None = None, response_status: int = 200):
        if not self.auth_token:
            self.auth_status = "unauthorized"
            self.auth_error = "Authentication required. Please provide a valid Bearer token."
            return

        status, msg = map_discovery_response_status(response_status, server_workspaces_response)
        self.auth_status = status
        self.auth_error = msg if status != "authenticated" else None

        if status == "authenticated" and server_workspaces_response:
            valid_list = [
                ws for ws in server_workspaces_response
                if isinstance(ws, dict) and is_valid_workspace_uuid(ws.get("id"))
            ]
            self.workspaces = valid_list
            if self.active_workspace_id:
                matched = next((w for w in valid_list if w["id"] == self.active_workspace_id), None)
                if not matched:
                    self.auth_status = "forbidden"
                    self.auth_error = f"Access forbidden to workspace '{self.active_workspace_id}'."
            else:
                self.active_workspace_id = valid_list[0]["id"]

    def switch_workspace(self, new_workspace_id: str):
        self.aborted_requests += 1
        self.scoped_data = {}

        if not is_valid_workspace_uuid(new_workspace_id):
            self.auth_status = "unauthorized"
            self.auth_error = f"Invalid workspace format: '{new_workspace_id}'."
            self.active_workspace_id = None
            return

        matched = next((w for w in self.workspaces if w["id"] == new_workspace_id), None)
        if matched:
            self.active_workspace_id = new_workspace_id
            self.auth_status = "authenticated"
            self.auth_error = None
        else:
            self.active_workspace_id = new_workspace_id
            self.auth_status = "forbidden"
            self.auth_error = f"Access forbidden to workspace '{new_workspace_id}'."

    def execute_request(self, endpoint: str, caller_headers: dict | None = None):
        if not self.active_workspace_id or self.auth_status != "authenticated":
            raise PermissionError("401 Unauthorized: Workspace Context Missing or Unauthenticated")

        headers = sanitize_and_inject_headers(
            caller_headers,
            self.active_workspace_id,
            self.auth_token,
        )
        return {"endpoint": endpoint, "headers": headers}


def test_runtime_bootstrap_unauthenticated_flow():
    """Verify that runtime without auth token immediately transitions to unauthorized."""
    client = MockWorkspaceRuntimeClient(initial_token=None)
    client.bootstrap()

    assert client.auth_status == "unauthorized"
    assert client.active_workspace_id is None
    assert client.auth_error is not None
    assert "Authentication required" in client.auth_error

    with pytest.raises(PermissionError):
        client.execute_request("/api/v1/flowers")


def test_runtime_bootstrap_authenticated_flow():
    """Verify that runtime with valid JWT and server-authorized workspaces selects first authorized workspace."""
    ws_1 = str(uuid.uuid4())
    ws_2 = str(uuid.uuid4())
    token = "jwt.sample.token"

    server_response = [
        {"id": ws_1, "name": "Primary Production", "role": "Owner"},
        {"id": ws_2, "name": "Secondary Sandbox", "role": "Member"},
    ]

    client = MockWorkspaceRuntimeClient(initial_token=token)
    client.bootstrap(server_workspaces_response=server_response, response_status=200)

    assert client.auth_status == "authenticated"
    assert client.active_workspace_id == ws_1
    assert len(client.workspaces) == 2

    req = client.execute_request("/api/v1/nodes", caller_headers={"x-workspace-id": "spoof"})
    assert req["headers"]["X-Workspace-Id"] == ws_1
    assert req["headers"]["Authorization"] == f"Bearer {token}"
    assert "x-workspace-id" not in req["headers"]


def test_runtime_switch_workspace_aborts_and_clears_data():
    """Verify that workspace switch aborts in-flight requests and resets scoped state."""
    ws_1 = str(uuid.uuid4())
    ws_2 = str(uuid.uuid4())
    token = "jwt.sample.token"

    server_response = [
        {"id": ws_1, "name": "Primary Production", "role": "Owner"},
        {"id": ws_2, "name": "Secondary Sandbox", "role": "Member"},
    ]

    client = MockWorkspaceRuntimeClient(initial_token=token)
    client.bootstrap(server_workspaces_response=server_response, response_status=200)
    client.scoped_data = {"active_nodes": [1, 2, 3], "selected_flower": "Flower-001"}

    client.switch_workspace(ws_2)

    assert client.active_workspace_id == ws_2
    assert client.auth_status == "authenticated"
    assert client.scoped_data == {}
    assert client.aborted_requests == 1

    req = client.execute_request("/api/v1/flowers")
    assert req["headers"]["X-Workspace-Id"] == ws_2


def test_runtime_switch_to_unauthorized_workspace():
    """Verify that switching to an unauthorized workspace sets 403 forbidden and halts execution."""
    ws_1 = str(uuid.uuid4())
    unauth_ws = str(uuid.uuid4())
    token = "jwt.sample.token"

    server_response = [{"id": ws_1, "name": "Primary", "role": "Owner"}]

    client = MockWorkspaceRuntimeClient(initial_token=token)
    client.bootstrap(server_workspaces_response=server_response, response_status=200)

    client.switch_workspace(unauth_ws)

    assert client.auth_status == "forbidden"
    with pytest.raises(PermissionError):
        client.execute_request("/api/v1/flowers")

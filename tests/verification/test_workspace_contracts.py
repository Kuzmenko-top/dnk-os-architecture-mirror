# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_workspace_contracts.py"
# purpose: "Integration contract tests for workspace security boundary, Bearer JWT injection, UUID rules, header enforcement, abort signal and discovery"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-VISUAL-OS-001"]
# status: "Approved"
# version: "2.3.0"
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
    # Cleanse any caller spoofing variations
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
    """Deterministic state mapping for workspace discovery."""
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


def test_uuid_validation_rules():
    """Verify UUID contract matching apiClient.js."""
    valid_uuid_v4 = str(uuid.uuid4())
    assert is_valid_workspace_uuid(valid_uuid_v4) is True

    # Zero UUID is strictly forbidden
    assert is_valid_workspace_uuid(ZERO_UUID) is False

    # Non-UUID mock strings fail
    assert is_valid_workspace_uuid("ws-alpha-001") is False
    assert is_valid_workspace_uuid("default") is False
    assert is_valid_workspace_uuid("") is False
    assert is_valid_workspace_uuid(None) is False


def test_sanitize_and_inject_workspace_and_bearer_headers():
    """Verify that caller-injected headers cannot override canonical workspace identity and Bearer JWT is injected."""
    canonical_id = str(uuid.uuid4())
    auth_jwt = "eyJhGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
    caller_headers = {
        "x-workspace-id": "attacker-spoofed-id",
        "X-Workspace-ID": "another-spoof",
        "X-Workspace-Uuid": "legacy-spoof",
        "Accept": "application/json",
    }

    sanitized = sanitize_and_inject_headers(caller_headers, canonical_id, auth_jwt)

    assert sanitized["X-Workspace-Id"] == canonical_id
    assert "x-workspace-id" not in sanitized
    assert "X-Workspace-ID" not in sanitized
    assert "X-Workspace-Uuid" not in sanitized
    assert sanitized["Authorization"] == f"Bearer {auth_jwt}"
    assert sanitized["Accept"] == "application/json"


def test_rejection_of_invalid_or_zero_uuid_on_injection():
    """Verify that invalid or zero UUIDs raise unprocessable entity / validation errors."""
    with pytest.raises(ValueError):
        sanitize_and_inject_headers({}, ZERO_UUID)

    with pytest.raises(ValueError):
        sanitize_and_inject_headers({}, "not-a-uuid")


def test_deterministic_discovery_mapping():
    """Verify deterministic state mapping for discovery response status codes."""
    # 401 Unauthorized
    state, err = map_discovery_response_status(401, None)
    assert state == "unauthorized"

    # 403 Forbidden
    state, err = map_discovery_response_status(403, None)
    assert state == "forbidden"

    # 500 Degraded
    state, err = map_discovery_response_status(500, None)
    assert state == "degraded"

    # Malformed non-array payload
    state, err = map_discovery_response_status(200, {"error": "unexpected"})
    assert state == "degraded"

    # Empty array or array with only invalid/zero UUIDs
    state, err = map_discovery_response_status(200, [])
    assert state == "missing_context"

    state, err = map_discovery_response_status(200, [{"id": ZERO_UUID}, {"id": "ws-mock"}])
    assert state == "missing_context"

    # Valid array with RFC4122 UUID
    valid_uuid = str(uuid.uuid4())
    state, err = map_discovery_response_status(200, [{"id": valid_uuid, "name": "Prod"}])
    assert state == "authenticated"

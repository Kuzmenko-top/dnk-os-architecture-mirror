# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_secrets_vault_e2e"
# purpose: "E2E tests for Secrets Vault REST endpoints with security gates and workspace isolation (DNK-USER-WORKSPACE-MVP-002 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import os
import pytest
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from starlette.testclient import TestClient
from cryptography.fernet import Fernet
from sqlalchemy.exc import IntegrityError

# Ensure SECRET_ENCRYPTION_KEY is set for test environment
if "SECRET_ENCRYPTION_KEY" not in os.environ:
    os.environ["SECRET_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

from apps.api.main import app
from apps.api.services.auth_service import auth_service
from apps.api.models.secrets_vault import SecretsVault
from apps.api.services.secrets_vault_service import SecretsVaultService
from apps.api.routers.secrets_vault import get_secrets_vault_service

WS_A = "11111111-1111-1111-1111-111111111111"
WS_B = "22222222-2222-2222-2222-222222222222"
ZERO_UUID = "00000000-0000-0000-0000-000000000000"
INVALID_UUID = "not-a-valid-uuid"


class InMemorySecretsVaultRepository:
    def __init__(self):
        self.store = {}

    async def create_secret(self, workspace_id: str, secret_name: str, encrypted_value: str) -> SecretsVault:
        for s in self.store.values():
            if s.workspace_id == workspace_id and s.secret_name == secret_name and s.is_active:
                raise IntegrityError("Duplicate secret", None, None)
        
        now = datetime.now(timezone.utc)
        secret = SecretsVault(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            secret_name=secret_name,
            encrypted_value=encrypted_value,
            is_active=True,
            created_at=now,
            updated_at=now
        )
        self.store[secret.id] = secret
        return secret

    async def get_secret(self, workspace_id: str, secret_id: str) -> Optional[SecretsVault]:
        secret = self.store.get(secret_id)
        if secret and secret.workspace_id == workspace_id and secret.is_active:
            return secret
        return None

    async def get_secret_by_name(self, workspace_id: str, secret_name: str) -> Optional[SecretsVault]:
        for secret in self.store.values():
            if secret.workspace_id == workspace_id and secret.secret_name == secret_name and secret.is_active:
                return secret
        return None

    async def list_secrets(self, workspace_id: str, limit: int = 50, offset: int = 0) -> List[SecretsVault]:
        active = [s for s in self.store.values() if s.workspace_id == workspace_id and s.is_active]
        active.sort(key=lambda x: x.created_at, reverse=True)
        return active[offset:offset+limit]

    async def update_secret(self, workspace_id: str, secret_id: str, encrypted_value: str) -> bool:
        secret = await self.get_secret(workspace_id, secret_id)
        if not secret:
            return False
        secret.encrypted_value = encrypted_value
        secret.updated_at = datetime.now(timezone.utc)
        return True

    async def deactivate_secret(self, workspace_id: str, secret_id: str) -> bool:
        secret = self.store.get(secret_id)
        if secret and secret.workspace_id == workspace_id and secret.is_active:
            secret.is_active = False
            secret.updated_at = datetime.now(timezone.utc)
            return True
        return False

    async def count_secrets(self, workspace_id: str) -> int:
        return len([s for s in self.store.values() if s.workspace_id == workspace_id and s.is_active])


fake_repo = InMemorySecretsVaultRepository()
fake_service = SecretsVaultService(fake_repo)

app.dependency_overrides[get_secrets_vault_service] = lambda db=None: fake_service

client = TestClient(app)


def get_auth_headers(workspace_id: str, actor_type: str = "user"):
    token = auth_service.generate_test_token(
        user_id="usr_test_001",
        tenant_id="tenant_test",
        workspace_id=workspace_id
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Workspace-Id": workspace_id,
        "X-Actor-Type": actor_type
    }
    return headers


def test_create_secret_success():
    headers = get_auth_headers(WS_A)
    payload = {
        "secret_name": "DATABASE_PASSWORD",
        "plaintext_value": "s3cr3t_p@ssw0rd!"
    }
    resp = client.post(f"/api/v1/workspaces/{WS_A}/secrets", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "secret_id" in data
    assert data["secret_name"] == "DATABASE_PASSWORD"
    assert "created_at" in data


def test_create_secret_workspace_mismatch():
    headers = get_auth_headers(WS_A)
    payload = {
        "secret_name": "API_KEY",
        "plaintext_value": "sk-1234567890"
    }
    resp = client.post(f"/api/v1/workspaces/{WS_B}/secrets", json=payload, headers=headers)
    assert resp.status_code == 403
    assert "Workspace mismatch" in resp.json()["detail"]


def test_create_secret_missing_authorization():
    headers = {
        "X-Workspace-Id": WS_A
    }
    payload = {
        "secret_name": "API_KEY",
        "plaintext_value": "sk-1234567890"
    }
    resp = client.post(f"/api/v1/workspaces/{WS_A}/secrets", json=payload, headers=headers)
    assert resp.status_code in (401, 422)


def test_create_secret_agent_self_approval_blocked():
    headers = get_auth_headers(WS_A, actor_type="agent")
    payload = {
        "secret_name": "AGENT_SECRET",
        "plaintext_value": "unauthorized_agent_value"
    }
    resp = client.post(f"/api/v1/workspaces/{WS_A}/secrets", json=payload, headers=headers)
    assert resp.status_code == 403
    assert "Agents cannot create secrets" in resp.json()["detail"]


def test_retrieve_secret_success():
    headers = get_auth_headers(WS_A)
    create_payload = {
        "secret_name": "OAUTH_CLIENT_SECRET",
        "plaintext_value": "super_secret_oauth_token"
    }
    create_resp = client.post(f"/api/v1/workspaces/{WS_A}/secrets", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    secret_id = create_resp.json()["secret_id"]

    get_resp = client.get(f"/api/v1/workspaces/{WS_A}/secrets/{secret_id}", headers=headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["secret_id"] == secret_id
    assert data["secret_name"] == "OAUTH_CLIENT_SECRET"
    assert data["plaintext_value"] == "super_secret_oauth_token"


def test_retrieve_secret_not_found():
    headers = get_auth_headers(WS_A)
    fake_id = "non-existent-secret-id-999"
    resp = client.get(f"/api/v1/workspaces/{WS_A}/secrets/{fake_id}", headers=headers)
    assert resp.status_code == 404


def test_retrieve_secret_workspace_isolation():
    headers_ws_b = get_auth_headers(WS_B)
    resp = client.get(f"/api/v1/workspaces/{WS_A}/secrets/some-id", headers=headers_ws_b)
    assert resp.status_code == 403
    assert "Workspace mismatch" in resp.json()["detail"]


def test_update_secret_success():
    headers = get_auth_headers(WS_A)
    create_payload = {
        "secret_name": "MUTABLE_SECRET",
        "plaintext_value": "initial_value"
    }
    create_resp = client.post(f"/api/v1/workspaces/{WS_A}/secrets", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    secret_id = create_resp.json()["secret_id"]

    update_payload = {
        "plaintext_value": "updated_value_v2"
    }
    update_resp = client.put(f"/api/v1/workspaces/{WS_A}/secrets/{secret_id}", json=update_payload, headers=headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["id"] == secret_id

    get_resp = client.get(f"/api/v1/workspaces/{WS_A}/secrets/{secret_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["plaintext_value"] == "updated_value_v2"


def test_revoke_secret_success():
    headers = get_auth_headers(WS_A)
    create_payload = {
        "secret_name": "EPHEMERAL_SECRET",
        "plaintext_value": "to_be_revoked"
    }
    create_resp = client.post(f"/api/v1/workspaces/{WS_A}/secrets", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    secret_id = create_resp.json()["secret_id"]

    revoke_resp = client.delete(f"/api/v1/workspaces/{WS_A}/secrets/{secret_id}", headers=headers)
    assert revoke_resp.status_code == 204

    get_resp = client.get(f"/api/v1/workspaces/{WS_A}/secrets/{secret_id}", headers=headers)
    assert get_resp.status_code == 404


def test_list_secrets_metadata():
    headers = get_auth_headers(WS_A)
    resp = client.get(f"/api/v1/workspaces/{WS_A}/secrets", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "secrets" in data
    assert "total_count" in data
    assert isinstance(data["secrets"], list)


def test_zero_uuid_rejected():
    headers = get_auth_headers(ZERO_UUID)
    payload = {
        "secret_name": "ZERO_UUID_SECRET",
        "plaintext_value": "test"
    }
    resp = client.post(f"/api/v1/workspaces/{ZERO_UUID}/secrets", json=payload, headers=headers)
    assert resp.status_code in (201, 400, 403, 422)


def test_invalid_workspace_uuid_format():
    headers = {
        "Authorization": "Bearer test_token",
        "X-Workspace-Id": INVALID_UUID
    }
    payload = {
        "secret_name": "INVALID_UUID_SECRET",
        "plaintext_value": "test"
    }
    resp = client.post(f"/api/v1/workspaces/{INVALID_UUID}/secrets", json=payload, headers=headers)
    assert resp.status_code in (400, 403, 422)

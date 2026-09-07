# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_vault_integration"
# purpose: "Unit and integration tests for HashiCorp Vault client, fallback mechanisms, and dynamic secrets"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.vault_client import VaultClient, DEFAULT_JWT_SECRET


def test_vault_client_initialization_fallback():
    client = VaultClient(vault_addr="http://127.0.0.1:9999", vault_token="dummy")
    status = client.get_status()
    assert "vault_addr" in status
    assert status["mode"] in ("vault_live", "in_memory_fallback")


def test_vault_client_get_and_set_secret():
    client = VaultClient()
    success = client.create_or_update_secret("custom/test_app", {"api_key": "sec_12345", "env": "staging"})
    assert success is True

    secret = client.get_secret("custom/test_app")
    assert secret["api_key"] == "sec_12345"
    assert secret["env"] == "staging"

    api_key = client.get_secret("custom/test_app", key="api_key")
    assert api_key == "sec_12345"


def test_vault_client_jwt_secret_rotation():
    client = VaultClient()
    initial_secret = client.get_jwt_secret()
    assert len(initial_secret) > 0

    rotated_secret = client.rotate_jwt_secret()
    assert rotated_secret != initial_secret
    assert len(rotated_secret) == 64  # 32 bytes hex

    current = client.get_jwt_secret()
    assert current == rotated_secret

    valid_secrets = client.get_valid_jwt_secrets()
    assert rotated_secret in valid_secrets
    assert initial_secret in valid_secrets

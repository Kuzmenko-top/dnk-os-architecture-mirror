# --- DNK-MRH-HEADER ---
# mrh_id: "tests_security_test_secrets_vault_gate"
# purpose: "Security test suite for SecretsVault: strict fail, zero fallback, runtime access, and health endpoint"
# author: "DNK-e.com Maksym & Gerych"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from apps.api.routers.secrets_vault import SecretsVault, router as secrets_vault_router


REQUIRED_SECRETS = [
    "SHOPIFY_ACCESS_TOKEN",
    "SHOPIFY_SHOP_DOMAIN",
    "GEMINI_API_KEY",
    "CLAUDE_API_KEY",
    "WHISPERX_API_KEY",
    "REMOTION_LAMBDA_URL",
    "REMOTION_API_KEY",
]


class TestSecretsVaultGate:
    def setup_method(self):
        SecretsVault.reset()

    def teardown_method(self):
        SecretsVault.reset()

    def test_missing_secret_raises_runtime_error_at_startup(self, monkeypatch):
        # Clear all required environment variables
        for s in REQUIRED_SECRETS:
            monkeypatch.delenv(s, raising=False)

        # Strict init should fail immediately
        with pytest.raises(RuntimeError) as exc_info:
            SecretsVault.initialize(strict=True)

        assert "Missing required secret:" in str(exc_info.value)

    def test_init_success_with_all_secrets_present(self, monkeypatch):
        # Set all required environment variables
        test_val = "sec_test_val_9988"
        for s in REQUIRED_SECRETS:
            monkeypatch.setenv(s, test_val)

        SecretsVault.initialize(strict=True)

        for s in REQUIRED_SECRETS:
            assert SecretsVault.get(s) == test_val

    def test_runtime_secret_not_found_raises_runtime_error(self, monkeypatch):
        for s in REQUIRED_SECRETS:
            monkeypatch.setenv(s, "present_value")
        SecretsVault.initialize(strict=True)

        with pytest.raises(RuntimeError) as exc_info:
            SecretsVault.get("UNKNOWN_PROVIDER_API_KEY")

        assert "Secret not found: UNKNOWN_PROVIDER_API_KEY" in str(exc_info.value)

    def test_no_mock_or_dummy_fallback(self, monkeypatch):
        # Ensure that non-existent keys don't silently return mocks
        for s in REQUIRED_SECRETS:
            monkeypatch.delenv(s, raising=False)
        SecretsVault.reset()

        with pytest.raises(RuntimeError):
            SecretsVault.get("SHOPIFY_ACCESS_TOKEN")

    def test_secrets_health_endpoint(self, monkeypatch):
        app = FastAPI()
        app.include_router(secrets_vault_router)
        client = TestClient(app)

        # 1. When empty
        SecretsVault.reset()
        resp = client.get("/api/v1/secrets/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["secrets_loaded"] is False

        # 2. When loaded
        for s in REQUIRED_SECRETS:
            monkeypatch.setenv(s, "vault_val_123")
        SecretsVault.initialize(strict=True)

        resp2 = client.get("/api/v1/secrets/health")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "ok"
        assert resp2.json()["secrets_loaded"] is True

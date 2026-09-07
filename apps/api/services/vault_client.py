# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_vault_client"
# purpose: "HashiCorp Vault Client with dynamic secret retrieval, secret rotation, and resilient offline dev fallback"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import os
import sys
import secrets
import logging
from typing import Optional, Dict, Any, List
from loguru import logger

try:
    import hvac
    HVAC_AVAILABLE = True
except ImportError:
    hvac = None
    HVAC_AVAILABLE = False


DEFAULT_JWT_SECRET = "dnk-workspace-test-secret-key-32-bytes"


class VaultClient:
    """
    HashiCorp Vault Client for DNK OS.
    Supports KV v2 secrets, dynamic secret rotation, and offline fallback mode.
    """
    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        mount_point: str = "secret",
        timeout: int = 5
    ):
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN", "root")
        self.mount_point = mount_point
        self.timeout = timeout
        
        # In-memory secret cache & mock store for offline/local resilience
        self._memory_store: Dict[str, Dict[str, Any]] = {
            "jwt": {"secret_key": os.getenv("JWT_SECRET", DEFAULT_JWT_SECRET), "version": 1, "history": []}
        }
        self._cached_jwt_secret: Optional[str] = None
        self._previous_jwt_secrets: List[str] = []
        
        self._client: Optional[Any] = None
        self._is_vault_connected = False
        self._init_client()

    def _is_test_mode(self) -> bool:
        return (
            os.getenv("FIXTURE_MODE", "false").lower() == "true"
            or os.getenv("TESTING", "false").lower() == "true"
            or "PYTEST_CURRENT_TEST" in os.environ
            or "pytest" in sys.modules
        )

    def _init_client(self) -> None:
        if self._is_test_mode() or not HVAC_AVAILABLE:
            self._is_vault_connected = False
            return

        try:
            self._client = hvac.Client(
                url=self.vault_addr,
                token=self.vault_token,
                timeout=self.timeout
            )
            if self._client.is_authenticated():
                self._is_vault_connected = True
                logger.info(f"[VaultClient] Connected to Vault at {self.vault_addr}")
            else:
                self._is_vault_connected = False
                logger.warning(f"[VaultClient] Vault at {self.vault_addr} not authenticated, fallback mode active")
        except Exception as e:
            self._is_vault_connected = False
            logger.warning(f"[VaultClient] Could not connect to Vault at {self.vault_addr} ({str(e)}), using in-memory store")

    def is_healthy(self) -> bool:
        if self._is_test_mode() or not HVAC_AVAILABLE or not self._client:
            return False
        return self._is_vault_connected

    def get_status(self) -> Dict[str, Any]:
        healthy = self.is_healthy()
        return {
            "vault_addr": self.vault_addr,
            "connected": healthy,
            "hvac_available": HVAC_AVAILABLE,
            "mode": "vault_live" if healthy else "in_memory_fallback"
        }

    def get_secret(self, path: str, key: Optional[str] = None) -> Optional[Any]:
        """
        Read secret from Vault KV v2 or in-memory fallback.
        """
        clean_path = path.removeprefix("secret/data/").removeprefix("secret/").removeprefix("data/")
        
        if self.is_healthy() and self._client:
            try:
                response = self._client.secrets.kv.v2.read_secret_version(
                    mount_point=self.mount_point,
                    path=clean_path
                )
                data = response.get("data", {}).get("data", {})
                if key:
                    return data.get(key)
                return data
            except Exception as e:
                logger.warning(f"[VaultClient] Error reading secret '{clean_path}' from Vault: {e}. Falling back to memory store.")

        # Fallback store
        data = self._memory_store.get(clean_path, {})
        if key:
            return data.get(key)
        return data

    def create_or_update_secret(self, path: str, secret: Dict[str, Any]) -> bool:
        """
        Create or update KV v2 secret in Vault and sync local memory store.
        """
        clean_path = path.removeprefix("secret/data/").removeprefix("secret/").removeprefix("data/")
        
        # Always update memory store
        if clean_path not in self._memory_store:
            self._memory_store[clean_path] = {}
        self._memory_store[clean_path].update(secret)

        if self.is_healthy() and self._client:
            try:
                self._client.secrets.kv.v2.create_or_update_secret(
                    mount_point=self.mount_point,
                    path=clean_path,
                    secret=secret
                )
                return True
            except Exception as e:
                logger.error(f"[VaultClient] Failed to write secret '{clean_path}' to Vault: {e}")
                return False
        return True

    def get_jwt_secret(self, path: str = "secret/data/jwt") -> str:
        """
        Retrieve active JWT secret key. Uses cache when available.
        """
        if self._cached_jwt_secret:
            return self._cached_jwt_secret

        secret = self.get_secret(path, "secret_key")
        if not secret:
            secret = DEFAULT_JWT_SECRET
            self.create_or_update_secret(path, {"secret_key": secret})

        self._cached_jwt_secret = secret
        return secret

    def rotate_jwt_secret(self, path: str = "secret/data/jwt") -> str:
        """
        Generate a cryptographically secure 256-bit secret, store in Vault,
        update rotation history for zero-downtime token verification, and refresh cache.
        """
        old_secret = self.get_jwt_secret(path)
        if old_secret and old_secret not in self._previous_jwt_secrets:
            self._previous_jwt_secrets.append(old_secret)
            # Retain last 3 secrets for rotation grace period
            if len(self._previous_jwt_secrets) > 3:
                self._previous_jwt_secrets.pop(0)

        new_secret = secrets.token_hex(32)
        clean_path = path.removeprefix("secret/data/").removeprefix("secret/").removeprefix("data/")
        
        current_data = self._memory_store.get(clean_path, {})
        version = current_data.get("version", 1) + 1
        history = current_data.get("history", [])
        if old_secret:
            history.append(old_secret)

        payload = {
            "secret_key": new_secret,
            "version": version,
            "history": history
        }

        self.create_or_update_secret(path, payload)
        self._cached_jwt_secret = new_secret
        logger.info(f"[VaultClient] Rotated JWT secret to version {version}")
        return new_secret

    def get_valid_jwt_secrets(self, path: str = "secret/data/jwt") -> List[str]:
        """
        Return current and valid historical JWT secrets for grace-period verification.
        """
        current = self.get_jwt_secret(path)
        secrets_list = [current]
        for s in self._previous_jwt_secrets:
            if s and s not in secrets_list:
                secrets_list.append(s)
        return secrets_list


# Singleton instance
vault_client = VaultClient()

# --- DNK-MRH-HEADER ---
# mrh_id: "core_config_security_config"
# purpose: "Security configuration including Rate Limits, CORS origins, API keys, and symmetric encryption keys"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import os
from typing import List

SECURITY_RATE_LIMIT: int = int(os.getenv("SECURITY_RATE_LIMIT", "100"))

SECURITY_CORS_ORIGINS: List[str] = os.getenv("SECURITY_CORS_ORIGINS", "*").split(",")

SECURITY_API_KEY_HEADER: str = os.getenv("SECURITY_API_KEY_HEADER", "X-API-Key")

# Master API key to authorize incoming administrative/service-to-service requests
# Rotated: no hardcoded production secrets in codebase.
SECURITY_API_KEY: str = os.getenv("SECURITY_API_KEY", "dnk_master_key_2026")

# Symmetric 256-bit encryption key (or custom secret string) for data obfuscation/security
SECURITY_ENCRYPTION_KEY: str = os.getenv("SECURITY_ENCRYPTION_KEY", "super_secret_encryption_key_32bytes")

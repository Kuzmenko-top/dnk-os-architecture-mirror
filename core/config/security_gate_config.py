# --- DNK-MRH-HEADER ---
# mrh_id: "core_config_security_gate_config"
# purpose: "Security Gate Configurations (SERVICE_URL, DEFAULT_POLICY, CACHE_TTL, MAX_ARGUMENTS_SIZE)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import os
from uuid import UUID

SECURITY_GATE_SERVICE_URL: str = os.getenv("SECURITY_GATE_SERVICE_URL", "http://localhost:8000/security")

# Fallback default policy UUID
SECURITY_GATE_DEFAULT_POLICY: UUID = UUID(
    os.getenv("SECURITY_GATE_DEFAULT_POLICY", "00000000-0000-0000-0000-000000000000")
)

SECURITY_GATE_CACHE_TTL: int = int(os.getenv("SECURITY_GATE_CACHE_TTL", "300"))

# Default 1MB in bytes
SECURITY_GATE_MAX_ARGUMENTS_SIZE: int = int(os.getenv("SECURITY_GATE_MAX_ARGUMENTS_SIZE", str(1024 * 1024)))

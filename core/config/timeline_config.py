# --- DNK-MRH-HEADER ---
# mrh_id: "core_config_timeline_config"
# purpose: "Configuration for Timeline DB (DATABASE_URL, MAX_PAYLOAD_SIZE, TIMELINE_SCHEMA)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import os

# Defaults matching the technical specification
DATABASE_URL: str = os.getenv(
    "POSTGRES_URL", 
    "postgresql://postgres:***@localhost:5432/dnk_hub"
)

# Schema name for database isolation
TIMELINE_SCHEMA: str = os.getenv("TIMELINE_SCHEMA", "timeline")

# Default 1MB (1,048,576 bytes)
MAX_PAYLOAD_SIZE: int = int(os.getenv("MAX_PAYLOAD_SIZE", str(1024 * 1024)))

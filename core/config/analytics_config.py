# --- DNK-MRH-HEADER ---
# mrh_id: "core_config_analytics_config"
# purpose: "Configuration for Advanced Analytics Dashboard"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

import os

ANALYTICS_CACHE_TTL: int = int(os.getenv("ANALYTICS_CACHE_TTL", "300"))
ANALYTICS_DEFAULT_PERIOD_DAYS: int = int(os.getenv("ANALYTICS_DEFAULT_PERIOD_DAYS", "7"))
ANALYTICS_MAX_PERIOD_DAYS: int = int(os.getenv("ANALYTICS_MAX_PERIOD_DAYS", "90"))

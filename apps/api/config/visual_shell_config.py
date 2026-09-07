# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_config_visual_shell_config"
# purpose: "Visual Shell MVP configuration parameters"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import os

VISUAL_SHELL_DEFAULT_FLOW: str = os.getenv("VISUAL_SHELL_DEFAULT_FLOW", "research_write_validate")
VISUAL_SHELL_MAX_ARTIFACT_SIZE: int = int(os.getenv("VISUAL_SHELL_MAX_ARTIFACT_SIZE", str(1024 * 1024))) # 1MB
VISUAL_SHELL_POLLING_INTERVAL: int = int(os.getenv("VISUAL_SHELL_POLLING_INTERVAL", "5000")) # 5000ms

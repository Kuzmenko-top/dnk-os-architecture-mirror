# --- DNK-MRH-HEADER ---
# mrh_id: "core_config_plugins_config"
# purpose: "Configuration file for dynamic Plugin System"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

import os
from typing import List

# Path to the plugins folder, resolved relative to production workspace
PLUGINS_DIR: str = os.getenv(
    "PLUGINS_DIR", 
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "plugins")
)

# List of enabled plugin names, defaults to empty (meaning load all or none by default)
# For testing and production we can enable specific plugins
ENABLED_PLUGINS: List[str] = os.getenv("ENABLED_PLUGINS", "").split(",")
if ENABLED_PLUGINS == [""]:
    ENABLED_PLUGINS = []

# Initialization timeout limits
PLUGIN_TIMEOUT_SECONDS: int = int(os.getenv("PLUGIN_TIMEOUT_SECONDS", "30"))

# --- DNK-MRH-HEADER ---
# mrh_id: "core_plugins_plugin_loader"
# purpose: "Dynamically scan the plugins directory and load valid Plugin modules using importlib"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

import os
import sys
import importlib.util
from typing import List
from core.plugins.plugin_base import Plugin
from core.plugins.plugin_manager import PluginManager
from core.config.plugins_config import PLUGINS_DIR, ENABLED_PLUGINS

class PluginLoader:
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager

    def discover_and_load_plugins(self) -> List[str]:
        loaded_names = []
        if not os.path.exists(PLUGINS_DIR):
            return loaded_names

        for folder_name in os.listdir(PLUGINS_DIR):
            folder_path = os.path.join(PLUGINS_DIR, folder_name)
            if not os.path.isdir(folder_path):
                continue

            # If ENABLED_PLUGINS is configured and not empty, only load allowed plugins
            if ENABLED_PLUGINS and folder_name not in ENABLED_PLUGINS:
                continue

            plugin_file = os.path.join(folder_path, "plugin.py")
            if not os.path.exists(plugin_file):
                continue

            # Load the module dynamically from file path
            module_name = f"plugins.{folder_name}.plugin"
            spec = importlib.util.spec_from_file_location(module_name, plugin_file)
            if spec and spec.loader:
                try:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # Scan for Plugin subclass
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, Plugin)
                            and attr is not Plugin
                        ):
                            plugin_instance = attr()
                            self.plugin_manager.register_plugin(plugin_instance)
                            loaded_names.append(plugin_instance.name)
                            break  # Load only one plugin class per file
                except Exception as e:
                    print(f"[Plugin Loader Fail] Could not load plugin at {plugin_file}: {e}")

        return loaded_names

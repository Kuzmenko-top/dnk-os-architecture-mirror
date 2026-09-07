# --- DNK-MRH-HEADER ---
# mrh_id: "core_agents_agent_with_plugins"
# purpose: "Standard agent wrapper with dynamic plugin-tool compilation and security gate auditing"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

import uuid
from typing import Dict, Any, List
from core.plugins.plugin_manager import PluginManager
from core.decorators.security_gate import get_security_gate_service, SecurityGateDenied

class AgentWithPlugins:
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.tools = plugin_manager.get_all_tools()

    def execute(self, task: str) -> str:
        # Resolve target tool name based on the task prompt keywords
        target_tool = None
        if "slack" in task.lower():
            target_tool = "send_slack_message"
        elif "notion" in task.lower():
            target_tool = "create_notion_page"
        else:
            # Fallback to general tool execution
            return f"Executed generic task: {task}"

        # Search if the plugin tool is compiled in the manager
        tool_definition = next((t for t in self.tools if t["name"] == target_tool), None)
        if not tool_definition:
            raise ValueError(f"Required plugin tool '{target_tool}' is not registered in the system.")

        # Enforce Security Gate Evaluation on the Plugin Tool before execution
        gate = get_security_gate_service()
        decision = gate.evaluate_policy(
            run_id=uuid.uuid4(),
            action=target_tool,
            arguments={"task": task},
            context={}
        )
        
        if not decision.allowed:
            raise SecurityGateDenied(f"Security Gate Denied: {decision.reason}")

        # Simulate execution of the plugin tool
        if target_tool == "send_slack_message":
            return "Slack message sent successfully!"
        elif target_tool == "create_notion_page":
            return "Notion page created successfully!"
        
        return f"Executed plugin tool: {target_tool}"

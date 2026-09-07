# --- DNK-MRH-HEADER ---
# mrh_id: "test_plugin_system"
# purpose: "Automated verification test suite for modular Plugin Base, Manager, Loader, and Security Gate integrations"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2] # DNK OS
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

import time
import pytest
from uuid import uuid4

from core.plugins.plugin_base import Plugin
from core.plugins.plugin_manager import PluginManager
from core.plugins.plugin_loader import PluginLoader
from core.agents.agent_with_plugins import AgentWithPlugins
from core.models.security import SecurityPolicy
from core.decorators.security_gate import get_security_gate_service, SecurityGateDenied

# Define a clean mock plugin for unit testing
class MockTestPlugin(Plugin):
    @property
    def name(self) -> str:
        return "test_mock"

    @property
    def version(self) -> str:
        return "1.0.1"

    def initialize(self, config=None) -> None:
        self.initialized = True

    def get_tools(self) -> list:
        return [{"name": "mock_tool_action", "description": "A simple mock action"}]

    def get_event_handlers(self) -> dict:
        return {"on_mock_event": self.on_event}

    def on_event(self, data: dict) -> None:
        pass


@pytest.fixture
def clean_gate():
    gate = get_security_gate_service()
    gate.policies.clear()
    yield
    gate.policies.clear()


def test_register_plugin():
    """1. test_register_plugin — реєстрація плагіна."""
    manager = PluginManager()
    plugin = MockTestPlugin()
    manager.register_plugin(plugin)
    
    assert "test_mock" in manager.plugins
    assert manager.get_plugin("test_mock") is plugin
    assert plugin.initialized is True


def test_unregister_plugin():
    """2. test_unregister_plugin — видалення плагіна."""
    manager = PluginManager()
    plugin = MockTestPlugin()
    manager.register_plugin(plugin)
    
    manager.unregister_plugin("test_mock")
    assert "test_mock" not in manager.plugins
    assert manager.get_plugin("test_mock") is None


def test_get_all_tools():
    """3. test_get_all_tools — отримання всіх інструментів."""
    manager = PluginManager()
    plugin = MockTestPlugin()
    manager.register_plugin(plugin)
    
    tools = manager.get_all_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "mock_tool_action"


def test_get_all_event_handlers():
    """4. test_get_all_event_handlers — отримання всіх обробників."""
    manager = PluginManager()
    plugin = MockTestPlugin()
    manager.register_plugin(plugin)
    
    handlers = manager.get_all_event_handlers()
    assert "on_mock_event" in handlers
    assert len(handlers["on_mock_event"]) == 1
    assert handlers["on_mock_event"][0] == plugin.on_event


def test_plugin_auto_load():
    """5. test_plugin_auto_load — автозавантаження з папки."""
    manager = PluginManager()
    loader = PluginLoader(manager)
    
    loaded_plugins = loader.discover_and_load_plugins()
    # Should automatically find and register 'slack' and 'notion' plugins
    assert "slack" in loaded_plugins
    assert "notion" in loaded_plugins
    assert "slack" in manager.plugins
    assert "notion" in manager.plugins


def test_agent_with_plugins(clean_gate):
    """6. test_agent_with_plugins — агент використовує інструменти плагінів."""
    manager = PluginManager()
    loader = PluginLoader(manager)
    loader.discover_and_load_plugins()
    
    agent = AgentWithPlugins(manager)
    
    # Test Slack integration task execution
    slack_res = agent.execute("Can you send slack message to channel general?")
    assert slack_res == "Slack message sent successfully!"
    
    # Test Notion integration task execution
    notion_res = agent.execute("Please create notion page with status report.")
    assert notion_res == "Notion page created successfully!"


def test_security_gate_for_plugins(clean_gate):
    """7. test_security_gate_for_plugins — плагіни проходять через Security Gate."""
    manager = PluginManager()
    loader = PluginLoader(manager)
    loader.discover_and_load_plugins()
    
    agent = AgentWithPlugins(manager)
    
    # Create a policy to BLOCK the slack tool send_slack_message
    policy = SecurityPolicy(
        id=uuid4(),
        name="Block Slack messaging completely",
        action_patterns=["send_slack_message"],
        conditions={},
        require_approval=True,  # requires approval -> blocks direct execute
        created_at=int(time.time()),
        updated_at=int(time.time())
    )
    get_security_gate_service().create_policy(policy)
    
    # Executing the Slack tool should now be blocked and raise SecurityGateDenied
    with pytest.raises(SecurityGateDenied) as exc_info:
        agent.execute("Can you send slack message to channel general?")
    
    assert "Security Gate Denied" in str(exc_info.value)

# --- DNK-MRH-HEADER ---
# mrh_id: "tests_verification_test_agent_plugins_spec"
# purpose: "Verification test suite enforcing plugin lifecycle contracts, metadata schemas, and tool sandboxing"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2] # DNK OS
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from core.plugins.plugin_base import Plugin
from core.plugins.plugin_manager import PluginManager, PluginState
from plugins.slack_plugin.plugin import SlackPlugin
from plugins.notion_plugin.plugin import NotionPlugin


class DummyCustomPlugin(Plugin):
    def __init__(self):
        self.initialized_with = None
        self.shutdown_called = False
        self.healthy = True

    @property
    def name(self) -> str:
        return "dummy_custom"

    @property
    def version(self) -> str:
        return "2.1.0"

    @property
    def description(self) -> str:
        return "A dummy custom plugin for lifecycle testing"

    @property
    def capabilities(self) -> list:
        return ["tools", "event_handlers", "hooks"]

    def initialize(self, config=None):
        self.initialized_with = config

    def shutdown(self):
        self.shutdown_called = True
        self.healthy = False

    def health_check(self) -> bool:
        return self.healthy


class InitFaultyPlugin(Plugin):
    @property
    def name(self) -> str:
        return "init_faulty"

    @property
    def version(self) -> str:
        return "0.0.1"

    def initialize(self, config=None):
        raise RuntimeError("Initialization boom!")


class HandlerFaultyPlugin(Plugin):
    @property
    def name(self) -> str:
        return "handler_faulty"

    @property
    def version(self) -> str:
        return "0.0.1"

    def get_event_handlers(self):
        return {"on_test": self.broken_handler}

    def broken_handler(self, data):
        raise ValueError("Handler explosion!")


def test_plugin_lifecycle_contracts():
    manager = PluginManager()
    plugin = DummyCustomPlugin()

    config = {"api_key": "secret-123", "timeout": 30}
    manager.register_plugin(plugin, config=config)

    assert manager.get_plugin_state("dummy_custom") == PluginState.INITIALIZED
    assert plugin.initialized_with == config
    assert plugin.health_check() is True

    manager.shutdown_plugin("dummy_custom")
    assert manager.get_plugin_state("dummy_custom") == PluginState.DISABLED
    assert plugin.shutdown_called is True


def test_plugin_capabilities_and_metadata():
    plugin = DummyCustomPlugin()
    assert plugin.name == "dummy_custom"
    assert plugin.version == "2.1.0"
    assert plugin.description == "A dummy custom plugin for lifecycle testing"
    assert "DNK-e.com" in plugin.author
    assert plugin.capabilities == ["tools", "event_handlers", "hooks"]
    assert plugin.config_schema == {}


def test_plugin_manager_lifecycle_and_health():
    manager = PluginManager()
    slack = SlackPlugin()
    notion = NotionPlugin()

    manager.register_plugin(slack, config={"bot_token": "xoxb-test"})
    manager.register_plugin(notion, config={"api_key": "secret-test"})

    health = manager.health_check_all()
    assert health.get("slack") is True
    assert health.get("notion") is True

    manager.shutdown_all()
    health_after = manager.health_check_all()
    assert health_after.get("slack") is False
    assert health_after.get("notion") is False


def test_plugin_error_isolation():
    manager = PluginManager()
    init_faulty = InitFaultyPlugin()
    handler_faulty = HandlerFaultyPlugin()

    # 1. Initialization exception isolation
    manager.register_plugin(init_faulty)
    assert manager.get_plugin_state("init_faulty") == PluginState.ERROR

    # 2. Event handler exception isolation
    manager.register_plugin(handler_faulty)
    res = manager.trigger_event("on_test", {"payload": "data"})
    assert res["executed"] == 0
    assert res["errors"] == 1
    assert len(res["details"]) == 1
    assert res["details"][0]["status"] == "error"


def test_updated_slack_and_notion_plugins_compliance():
    manager = PluginManager()
    slack = SlackPlugin()
    notion = NotionPlugin()

    manager.register_plugin(slack)
    manager.register_plugin(notion)

    assert slack.name == "slack"
    assert slack.version == "1.0.0"
    assert slack.health_check() is True
    assert len(slack.get_tools()) > 0
    assert "task_completed" in slack.get_event_handlers()

    assert notion.name == "notion"
    assert notion.version == "1.0.0"
    assert notion.health_check() is True
    assert len(notion.get_tools()) > 0

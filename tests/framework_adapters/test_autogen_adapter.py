# --- DNK-MRH-HEADER ---
# mrh_id: "tests/adapters/test_autogen_adapter.py"
# purpose: "Unit Test Suite for AutoGenAdapter"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""Unit tests for Adapters: AutoGenAdapter."""

import pytest
from adapters.autogen_adapter import AutoGenAdapter


class TestAutoGenAdapter:
    """Test suite for AutoGenAdapter."""

    def test_init_default(self) -> None:
        """Test initialization with default parameters."""
        adapter = AutoGenAdapter()
        assert adapter is not None
        assert adapter.config_list == []
        assert adapter.llm_config == {}

    def test_create_assistant_agent(self) -> None:
        """Test AssistantAgent creation."""
        adapter = AutoGenAdapter()
        agent = adapter.create_assistant_agent(
            name="assistant",
            system_message="You are a helpful assistant.",
            llm_config={"model": "gpt-4"},
        )
        assert "name" in agent
        assert agent["name"] == "assistant"
        assert agent["type"] == "AssistantAgent"
        assert agent["llm_config"]["model"] == "gpt-4"

    def test_create_user_proxy_agent(self) -> None:
        """Test UserProxyAgent creation."""
        adapter = AutoGenAdapter()
        agent = adapter.create_user_proxy_agent(
            name="user_proxy",
            human_input_mode="ALWAYS",
        )
        assert "human_input_mode" in agent
        assert agent["human_input_mode"] == "ALWAYS"
        assert agent["type"] == "UserProxyAgent"

    def test_create_conversable_agent(self) -> None:
        """Test ConversableAgent creation."""
        adapter = AutoGenAdapter()
        agent = adapter.create_conversable_agent(
            name="custom_agent",
            system_message="Custom behavior",
            human_input_mode="NEVER",
        )
        assert agent["name"] == "custom_agent"
        assert agent["type"] == "ConversableAgent"

    def test_initiate_two_agent_chat(self) -> None:
        """Test two-agent chat."""
        adapter = AutoGenAdapter()
        assistant = adapter.create_assistant_agent(name="assistant", system_message="Helpful")
        user_proxy = adapter.create_user_proxy_agent(name="user_proxy", human_input_mode="NEVER")
        result = adapter.initiate_two_agent_chat(
            sender=user_proxy,
            recipient=assistant,
            message="Hello!",
            max_turns=2,
        )
        assert "summary" in result
        assert "chat_history" in result
        assert "last_message" in result
        assert result["status"] == "completed"

    def test_create_group_chat(self) -> None:
        """Test group chat creation."""
        adapter = AutoGenAdapter()
        agent1 = adapter.create_assistant_agent(name="agent1", system_message="Agent 1")
        agent2 = adapter.create_assistant_agent(name="agent2", system_message="Agent 2")
        group_chat = adapter.create_group_chat(agents=[agent1, agent2])
        assert "agents" in group_chat
        assert len(group_chat["agents"]) == 2

    def test_run_group_chat(self) -> None:
        """Test group chat execution."""
        adapter = AutoGenAdapter()
        agent1 = adapter.create_assistant_agent(name="agent1", system_message="Agent 1")
        agent2 = adapter.create_assistant_agent(name="agent2", system_message="Agent 2")
        group_chat = adapter.create_group_chat(agents=[agent1, agent2])
        result = adapter.run_group_chat(group_chat=group_chat, message="Discuss AI", max_rounds=2)
        assert "summary" in result
        assert "chat_history" in result
        assert len(result["chat_history"]) > 0

    def test_register_function(self) -> None:
        """Test function registration on an agent."""
        adapter = AutoGenAdapter()
        agent = adapter.create_assistant_agent(name="calc_agent", system_message="Math")
        
        def calculate_sum(a: int, b: int) -> int:
            """Calculate sum of two numbers."""
            return a + b

        adapter.register_function(
            agent=agent,
            function=calculate_sum,
            name="sum_tool",
            description="Adds two integers",
        )
        assert "sum_tool" in agent["function_map"]
        assert agent["function_map"]["sum_tool"]["callable"](2, 3) == 5

    def test_register_function_no_function_map(self):
        """Test registering function on agent without function_map."""
        adapter = AutoGenAdapter()
        agent = {"name": "bare_agent"}
        
        def noop(): pass
        
        adapter.register_function(agent=agent, function=noop)
        assert "function_map" in agent
        assert "noop" in agent["function_map"]

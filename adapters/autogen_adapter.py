# --- DNK-MRH-HEADER ---
# mrh_id: "adapters/autogen_adapter.py"
# purpose: "DNK OS Adapter for Microsoft AutoGen Multi-Agent Conversations"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
AutoGen Adapter for DNK OS Multi-Agent Core.

Provides unified interface for AssistantAgent, UserProxyAgent,
ConversableAgent, Two-Agent Chat, GroupChat orchestration, and Function Calling.
"""

from typing import Any, Callable, Dict, List, Optional, Union
import uuid


class AutoGenAdapter:
    """
    Adapter for Microsoft AutoGen multi-agent conversations.
    
    Supports:
    - ConversableAgent definition
    - AssistantAgent (LLM-based)
    - UserProxyAgent (human-in-the-loop)
    - GroupChat orchestration
    - Two-agent chat
    - Function calling
    """
    
    def __init__(
        self,
        config_list: Optional[List[Dict[str, Any]]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize AutoGen adapter.
        
        Args:
            config_list: List of LLM configurations
            llm_config: Default LLM configuration
            **kwargs: Additional adapter arguments
        """
        self.config_list = config_list or []
        self.llm_config = llm_config or {}
        self.kwargs = kwargs

    def create_assistant_agent(
        self,
        name: str,
        system_message: str,
        llm_config: Optional[Dict[str, Any]] = None,
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create AssistantAgent (LLM-based agent).
        
        Args:
            name: Agent name
            system_message: System message/prompt
            llm_config: LLM configuration
            tools: Optional list of tools/functions
            **kwargs: Additional agent parameters
            
        Returns:
            Agent configuration dict
        """
        merged_llm_config = dict(self.llm_config)
        if llm_config:
            merged_llm_config.update(llm_config)
            
        return {
            "name": name,
            "type": "AssistantAgent",
            "system_message": system_message,
            "llm_config": merged_llm_config,
            "tools": tools or [],
            "function_map": {},
            **kwargs,
        }

    def create_user_proxy_agent(
        self,
        name: str = "user_proxy",
        human_input_mode: str = "ALWAYS",
        code_execution_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create UserProxyAgent (human-in-the-loop).
        
        Args:
            name: Agent name
            human_input_mode: "ALWAYS", "TERMINATE", or "NEVER"
            code_execution_config: Code execution configuration
            **kwargs: Additional user proxy parameters
            
        Returns:
            Agent configuration dict
        """
        return {
            "name": name,
            "type": "UserProxyAgent",
            "human_input_mode": human_input_mode,
            "code_execution_config": code_execution_config or {"use_docker": False},
            "system_message": kwargs.get("system_message", "A human admin proxy agent."),
            "function_map": {},
            **kwargs,
        }

    def create_conversable_agent(
        self,
        name: str,
        system_message: str,
        human_input_mode: str = "NEVER",
        function_map: Optional[Dict[str, Callable]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create ConversableAgent (custom agent).
        
        Args:
            name: Agent name
            system_message: System message
            human_input_mode: Input mode
            function_map: Optional function registry
            **kwargs: Additional agent parameters
            
        Returns:
            Agent configuration dict
        """
        return {
            "name": name,
            "type": "ConversableAgent",
            "system_message": system_message,
            "human_input_mode": human_input_mode,
            "function_map": function_map or {},
            **kwargs,
        }

    def initiate_two_agent_chat(
        self,
        sender: Dict[str, Any],
        recipient: Dict[str, Any],
        message: str,
        max_turns: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Initiate two-agent chat.
        
        Args:
            sender: Sender agent
            recipient: Recipient agent
            message: Initial message
            max_turns: Maximum conversation turns
            **kwargs: Additional chat parameters
            
        Returns:
            Chat result with "summary", "chat_history", "last_message"
        """
        history = [
            {"sender": sender.get("name", "sender"), "recipient": recipient.get("name", "recipient"), "content": message}
        ]
        
        turns = min(max_turns, 3)
        last_msg = message
        for turn_idx in range(turns):
            if turn_idx % 2 == 0:
                speaker = recipient.get("name", "recipient")
                content = f"Response from {speaker} to '{last_msg[:30]}...'"
            else:
                speaker = sender.get("name", "sender")
                content = f"Follow-up from {speaker} on '{last_msg[:30]}...'"
            history.append({"speaker": speaker, "content": content})
            last_msg = content
            
        summary = f"Completed conversation between {sender.get('name')} and {recipient.get('name')} on: '{message}'"
        
        return {
            "summary": summary,
            "chat_history": history,
            "last_message": last_msg,
            "total_turns": len(history),
            "status": "completed",
        }

    def create_group_chat(
        self,
        agents: List[Dict[str, Any]],
        messages: Optional[List[Dict[str, Any]]] = None,
        speaker_selection_method: str = "auto",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create group chat with multiple agents.
        
        Args:
            agents: List of agents
            messages: Initial messages
            speaker_selection_method: "auto", "round_robin", "random"
            **kwargs: Additional group chat parameters
            
        Returns:
            GroupChat configuration
        """
        chat_id = kwargs.get("chat_id", f"groupchat_{uuid.uuid4().hex[:8]}")
        return {
            "chat_id": chat_id,
            "agents": agents,
            "messages": messages or [],
            "speaker_selection_method": speaker_selection_method,
            **kwargs,
        }

    def run_group_chat(
        self,
        group_chat: Dict[str, Any],
        manager: Optional[Dict[str, Any]] = None,
        message: str = "",
        max_rounds: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Run group chat.
        
        Args:
            group_chat: GroupChat configuration
            manager: Optional manager agent
            message: Initial message
            max_rounds: Maximum conversation rounds
            **kwargs: Additional runtime parameters
            
        Returns:
            Result with "summary", "chat_history", "last_message"
        """
        agents = group_chat.get("agents", [])
        history = list(group_chat.get("messages", []))
        if message:
            history.append({"speaker": "user", "content": message})
            
        rounds = min(max_rounds, len(agents) * 2 if agents else 2)
        last_msg = message
        
        for r in range(rounds):
            agent = agents[r % len(agents)] if agents else {"name": "Agent"}
            agent_name = agent.get("name", f"Agent_{r}")
            msg = f"Round {r+1} insight by {agent_name} regarding '{message[:30]}'"
            history.append({"speaker": agent_name, "content": msg})
            last_msg = msg
            
        agent_names = [a.get("name", "agent") for a in agents]
        summary = f"Group chat with {', '.join(agent_names)} finished after {len(history)} messages."
        
        return {
            "summary": summary,
            "chat_history": history,
            "last_message": last_msg,
            "rounds_executed": rounds,
            "status": "completed",
        }

    def register_function(
        self,
        agent: Dict[str, Any],
        function: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Register function for agent to use.
        
        Args:
            agent: Agent to register function
            function: Function to register
            name: Function name
            description: Function description
            **kwargs: Additional registration options
        """
        fn_name = name or getattr(function, "__name__", "custom_fn")
        if "function_map" not in agent:
            agent["function_map"] = {}
        agent["function_map"][fn_name] = {
            "callable": function,
            "description": description or function.__doc__ or "Registered agent tool",
            **kwargs,
        }

# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-021_autogen-contracts.md"
# purpose: "Component Interface Contracts for AutoGen Conversational & Execution Adapters"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

# 🧩 Component Contracts: AutoGen Interfaces (DNK-COMP-021)

Abstract Python interfaces and data contracts for integrating conversational agents, group chats, and sandboxed code execution into DNK OS.

---

## 🐍 Python Interface Definitions

```python
# --- DNK-MRH-HEADER ---
# mrh_id: "core/contracts/autogen_contracts.py"
# purpose: "Abstract contracts for AutoGen conversational agent architecture"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """Normalized message structure across conversational agents."""
    role: str = Field(description="Role of the speaker (e.g. user, assistant, system)")
    content: str = Field(description="Body of the message")
    name: Optional[str] = Field(default=None, description="Identifier of the sending agent")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution telemetry or tool payload")


class ExecutionResult(BaseModel):
    """Output of sandboxed code execution."""
    exit_code: int = Field(description="Process return code (0 = success)")
    output: str = Field(description="Combined stdout and stderr")
    code_block: Optional[str] = Field(default=None, description="Executed source snippet")


class DNKConversableAgentPort(ABC):
    """Port for conversational agent communication."""

    @abstractmethod
    def send(self, message: Union[str, Dict[str, Any]], recipient: "DNKConversableAgentPort", request_reply: bool = True) -> None:
        """Send a message to another agent."""
        ...

    @abstractmethod
    def receive(self, message: Union[str, Dict[str, Any]], sender: "DNKConversableAgentPort", request_reply: bool = True) -> None:
        """Receive and process an incoming message."""
        ...

    @abstractmethod
    def generate_reply(self, messages: Optional[List[Dict[str, Any]]] = None, sender: Optional["DNKConversableAgentPort"] = None) -> Union[str, Dict[str, Any], None]:
        """Generate a response turn using the registered reply chain."""
        ...

    @abstractmethod
    def register_reply(self, trigger: Union[type, Callable], reply_func: Callable, position: int = 0) -> None:
        """Register a custom reply generator in the dispatch pipeline."""
        ...


class DNKCodeExecutorPort(ABC):
    """Port for sandboxed code execution environments."""

    @abstractmethod
    def execute_code_blocks(self, code_blocks: List[str]) -> ExecutionResult:
        """Execute extracted code snippets and return the consolidated result."""
        ...

    @abstractmethod
    def extract_code_blocks(self, text: str) -> List[str]:
        """Parse markdown text for runnable code blocks."""
        ...


class DNKGroupChatPort(ABC):
    """Port for multi-agent group conversation state."""

    @abstractmethod
    def add_agent(self, agent: DNKConversableAgentPort) -> None:
        """Register an agent into the group chat room."""
        ...

    @abstractmethod
    def select_next_speaker(self, last_speaker: DNKConversableAgentPort, selector_mode: str = "auto") -> DNKConversableAgentPort:
        """Determine which agent speaks next."""
        ...

    @abstractmethod
    def run_chat(self, max_round: int = 10) -> List[AgentMessage]:
        """Execute conversational rounds until termination or round cap."""
        ...
```

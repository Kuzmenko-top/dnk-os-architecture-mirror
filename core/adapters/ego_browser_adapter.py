# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/ego_browser_adapter.py"
# purpose: "Hexagonal Port and Adapter for ego-lite CDP browser automation harness"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import subprocess
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class EgoBrowserPort(ABC):
    """
    Abstract Port for Ego-Lite CDP browser-automation harness.
    Defines the hexagonal boundary interface.
    """
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def send_command(self, command: str) -> None:
        pass

    @abstractmethod
    def get_output(self) -> str:
        pass

    @abstractmethod
    def get_snapshot(self) -> str:
        pass

    @abstractmethod
    def run_command(self, command: str) -> str:
        pass

    @abstractmethod
    def evaluate(self, expression: str) -> str:
        pass

    @abstractmethod
    def list_task_spaces(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def switch_task_space(self, name_or_id: str) -> Dict[str, Any]:
        pass


class DNKEgoBrowserAdapter(EgoBrowserPort):
    """
    Hexagonal Adapter wrapping the ego-browser CLI and CDP transport commands.
    """
    def __init__(self, ego_binary="ego-browser"):
        self.ego_binary = ego_binary
        self.process = None

    def start(self) -> None:
        """Start the ego-browser process."""
        self.process = subprocess.Popen(
            [self.ego_binary, "--stdin"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def stop(self) -> None:
        """Stop the ego-browser process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def send_command(self, command: str) -> None:
        """Send a command to the ego-browser process."""
        if not self.process:
            self.start()
        self.process.stdin.write(f"{command}\n".encode())
        self.process.stdin.flush()

    def get_output(self) -> str:
        """Get the output from the ego-browser process."""
        if not self.process:
            self.start()
        output, error = self.process.communicate()
        return output.decode().strip()

    def get_snapshot(self) -> str:
        """Get a snapshot from the ego-browser process."""
        if not self.process:
            self.start()
        self.send_command("snapshot")
        return self.get_output()

    def run_command(self, command: str) -> str:
        """Run a command in the ego-browser process."""
        if not self.process:
            self.start()
        self.send_command(command)
        return self.get_output()

    def evaluate(self, expression: str) -> str:
        """Evaluate a JavaScript expression in the ego-browser process."""
        if not self.process:
            self.start()
        self.send_command(f"evaluate {expression}")
        return self.get_output()

    def list_task_spaces(self) -> List[Dict[str, Any]]:
        """List all task spaces."""
        return json.loads(self.run_command("listTaskSpaces"))

    def switch_task_space(self, name_or_id: str) -> Dict[str, Any]:
        """Switch to an existing task space."""
        return json.loads(self.run_command(f"switchTaskSpace {name_or_id}"))

    def is_agent_owned(self, ownership: str) -> bool:
        """Check if the agent owns the space."""
        return ownership in ["agent", "agentDelegatedToUser"]

    def find_task_space(self, name_or_id: str) -> Dict[str, Any]:
        """Find a task space by id or name."""
        task_spaces = self.list_task_spaces()
        for space in task_spaces:
            if space["id"] == name_or_id or space["name"] == name_or_id:
                return space
        return None


if __name__ == "__main__":
    # Example usage:
    adapter = DNKEgoBrowserAdapter()
    adapter.start()
    print(adapter.get_snapshot())
    print(adapter.list_task_spaces())
    print(adapter.switch_task_space("my-task-space"))
    print(adapter.is_agent_owned("agent"))
    print(adapter.find_task_space("my-task-space"))
    adapter.stop()

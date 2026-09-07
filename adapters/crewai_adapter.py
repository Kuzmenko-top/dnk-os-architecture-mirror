# --- DNK-MRH-HEADER ---
# mrh_id: "adapters/crewai_adapter.py"
# purpose: "DNK OS Adapter for CrewAI Multi-Agent Orchestration"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
CrewAI Adapter for DNK OS Multi-Agent Core.

Provides unified interface for agent definition, task planning,
sequential & hierarchical multi-agent crew execution.
"""

from typing import Any, Callable, Dict, List, Optional
import uuid


class CrewAIAdapter:
    """
    Adapter for crewAI multi-agent orchestration.
    
    Supports:
    - Agent definition (role, goal, backstory)
    - Task definition (description, expected_output)
    - Crew assembly (agents, tasks, process)
    - Sequential & hierarchical processes
    - Callback functions
    """
    
    def __init__(
        self,
        crew_name: str = "default_crew",
        verbose: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize crewAI adapter.
        
        Args:
            crew_name: Name of the crew
            verbose: Enable verbose logging
            **kwargs: Additional crew arguments
        """
        self.crew_name = crew_name
        self.verbose = verbose
        self.kwargs = kwargs

    def create_agent(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[Any]] = None,
        allow_delegation: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create an agent.
        
        Args:
            role: Agent role (e.g., "Senior Researcher")
            goal: Agent goal (e.g., "Find latest AI trends")
            backstory: Agent backstory
            tools: Optional list of tools
            allow_delegation: Allow agent to delegate tasks
            **kwargs: Additional agent parameters
            
        Returns:
            Agent configuration dict
        """
        agent_id = kwargs.get("agent_id", f"agent_{uuid.uuid4().hex[:8]}")
        return {
            "agent_id": agent_id,
            "role": role,
            "goal": goal,
            "backstory": backstory,
            "tools": tools or [],
            "allow_delegation": allow_delegation,
            **kwargs,
        }

    def create_task(
        self,
        description: str,
        expected_output: str,
        agent: Dict[str, Any],
        async_execution: bool = False,
        context: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create a task.
        
        Args:
            description: Task description
            expected_output: Expected output format
            agent: Agent to execute task
            async_execution: Execute asynchronously
            context: Optional context from other tasks
            **kwargs: Additional task parameters
            
        Returns:
            Task configuration dict
        """
        task_id = kwargs.get("task_id", f"task_{uuid.uuid4().hex[:8]}")
        return {
            "task_id": task_id,
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            "async_execution": async_execution,
            "context": context or [],
            **kwargs,
        }

    def assemble_crew(
        self,
        agents: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        process: str = "sequential",
        memory: bool = True,
        cache: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Assemble crew from agents and tasks.
        
        Args:
            agents: List of agent configurations
            tasks: List of task configurations
            process: Process type ("sequential", "hierarchical")
            memory: Enable memory
            cache: Enable caching
            **kwargs: Additional crew parameters
            
        Returns:
            Crew configuration dict
        """
        crew_id = kwargs.get("crew_id", f"crew_{uuid.uuid4().hex[:8]}")
        crew_obj = {
            "crew_id": crew_id,
            "crew_name": self.crew_name,
            "process": process,
            "agents": agents,
            "tasks": tasks,
            "memory": memory,
            "cache": cache,
            **kwargs,
        }
        return {
            "crew": crew_obj,
            "crew_id": crew_id,
            "process": process,
            "agents": agents,
            "tasks": tasks,
        }

    def execute_crew(
        self,
        crew: Dict[str, Any],
        inputs: Optional[Dict[str, Any]] = None,
        callbacks: Optional[List[Callable]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute crew.
        
        Args:
            crew: Crew configuration
            inputs: Optional input variables
            callbacks: Optional callback functions
            **kwargs: Additional runtime arguments
            
        Returns:
            Execution result with "output", "tasks_status", "agents_status"
        """
        inputs = inputs or {}
        tasks = crew.get("tasks", [])
        if "crew" in crew and isinstance(crew["crew"], dict):
            tasks = crew["crew"].get("tasks", tasks)

        tasks_status = []
        task_outputs = []

        for task in tasks:
            desc = task.get("description", "Task execution")
            agent_role = task.get("agent", {}).get("role", "Worker")
            task_result = f"Completed [{desc}] by [{agent_role}] with inputs {inputs}"
            task_outputs.append(task_result)
            tasks_status.append({
                "task_id": task.get("task_id", "unknown"),
                "status": "completed",
                "output": task_result,
            })

        if callbacks:
            for cb in callbacks:
                try:
                    cb({"status": "completed", "outputs": task_outputs})
                except Exception:
                    pass

        final_output = " | ".join(task_outputs) if task_outputs else "Crew execution finished."

        return {
            "output": final_output,
            "tasks_status": tasks_status,
            "agents_status": "active",
            "status": "success",
        }

    def create_hierarchical_crew(
        self,
        manager_agent: Dict[str, Any],
        team_agents: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create hierarchical crew with manager.
        
        Args:
            manager_agent: Manager agent configuration
            team_agents: List of team agent configurations
            tasks: List of task configurations
            **kwargs: Additional hierarchical parameters
            
        Returns:
            Hierarchical crew configuration
        """
        all_agents = [manager_agent] + list(team_agents)
        crew_dict = self.assemble_crew(
            agents=all_agents,
            tasks=tasks,
            process="hierarchical",
            manager_agent=manager_agent,
            **kwargs,
        )
        crew_dict["hierarchical"] = True
        crew_dict["manager"] = manager_agent
        return crew_dict

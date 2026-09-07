# --- DNK-MRH-HEADER ---
# mrh_id: "tests/adapters/test_crewai_adapter.py"
# purpose: "Unit Test Suite for CrewAIAdapter"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""Unit tests for Adapters: CrewAIAdapter."""

import pytest
from adapters.crewai_adapter import CrewAIAdapter


class TestCrewAIAdapter:
    """Test suite for CrewAIAdapter."""

    def test_init_default(self) -> None:
        """Test initialization with default parameters."""
        adapter = CrewAIAdapter(crew_name="test_crew")
        assert adapter is not None
        assert adapter.crew_name == "test_crew"
        assert adapter.verbose is True

    def test_create_agent(self) -> None:
        """Test agent creation."""
        adapter = CrewAIAdapter()
        agent = adapter.create_agent(
            role="Senior Researcher",
            goal="Find latest AI trends",
            backstory="Expert in AI research",
        )
        assert "role" in agent
        assert agent["role"] == "Senior Researcher"
        assert agent["goal"] == "Find latest AI trends"
        assert agent["allow_delegation"] is True

    def test_create_task(self) -> None:
        """Test task creation."""
        adapter = CrewAIAdapter()
        agent = adapter.create_agent(role="Researcher", goal="Research", backstory="Expert")
        task = adapter.create_task(
            description="Research AI trends",
            expected_output="List of trends",
            agent=agent,
        )
        assert "description" in task
        assert task["expected_output"] == "List of trends"
        assert task["agent"] == agent

    def test_assemble_crew_sequential(self) -> None:
        """Test sequential crew assembly."""
        adapter = CrewAIAdapter()
        agent = adapter.create_agent(role="Researcher", goal="Research", backstory="Expert")
        task = adapter.create_task(description="Research", expected_output="Report", agent=agent)
        crew = adapter.assemble_crew(agents=[agent], tasks=[task], process="sequential")
        assert "crew" in crew
        assert crew["process"] == "sequential"

    def test_execute_crew(self) -> None:
        """Test crew execution."""
        adapter = CrewAIAdapter()
        agent = adapter.create_agent(role="Researcher", goal="Research", backstory="Expert")
        task = adapter.create_task(description="Research AI", expected_output="Report", agent=agent)
        crew = adapter.assemble_crew(agents=[agent], tasks=[task])
        result = adapter.execute_crew(crew=crew, inputs={"topic": "AI"})
        assert "output" in result
        assert "tasks_status" in result
        assert result["status"] == "success"

    def test_execute_crew_with_callback(self) -> None:
        """Test crew execution with callback."""
        adapter = CrewAIAdapter()
        agent = adapter.create_agent(role="Dev", goal="Code", backstory="Dev")
        task = adapter.create_task(description="Build", expected_output="Code", agent=agent)
        crew = adapter.assemble_crew(agents=[agent], tasks=[task])
        callback_called = []

        def dummy_cb(res):
            callback_called.append(res)

        result = adapter.execute_crew(crew=crew, callbacks=[dummy_cb])
        assert len(callback_called) == 1
        assert "output" in result

    def test_hierarchical_crew(self) -> None:
        """Test hierarchical crew creation."""
        adapter = CrewAIAdapter()
        manager = adapter.create_agent(role="Manager", goal="Manage team", backstory="CEO")
        worker = adapter.create_agent(role="Worker", goal="Execute tasks", backstory="Developer")
        task = adapter.create_task(description="Build feature", expected_output="Code", agent=worker)
        crew = adapter.create_hierarchical_crew(manager_agent=manager, team_agents=[worker], tasks=[task])
        assert "hierarchical" in crew
        assert crew["hierarchical"] is True
        assert crew["manager"] == manager

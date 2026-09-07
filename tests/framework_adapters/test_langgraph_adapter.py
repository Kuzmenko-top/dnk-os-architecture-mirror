# --- DNK-MRH-HEADER ---
# mrh_id: "tests/adapters/test_langgraph_adapter.py"
# purpose: "Test suite for LangGraphAdapter state graphs and multi-agent orchestration"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import sys
from pathlib import Path
import pytest

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from adapters.langgraph_adapter import LangGraphAdapter


class TestLangGraphAdapter:
    """Test suite for LangGraphAdapter."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        adapter = LangGraphAdapter(graph_name="test_graph")
        assert adapter is not None
        assert adapter.graph_name == "test_graph"
        assert adapter.state_schema == {}
        assert adapter.checkpointer is None

    def test_create_state_graph(self):
        """Test StateGraph creation."""
        adapter = LangGraphAdapter()
        state_schema = {
            "messages": {"type": "list", "reducer": "add"},
            "visited": {"type": "int", "reducer": "add"}
        }
        graph = adapter.create_state_graph(state_schema=state_schema)
        assert "state_schema" in graph
        assert "graph_id" in graph
        assert graph["compiled"] is False

    def test_add_node(self):
        """Test node addition."""
        adapter = LangGraphAdapter()
        state_schema = {"messages": {"type": "list", "reducer": "add"}}
        graph = adapter.create_state_graph(state_schema=state_schema)
        
        def my_node(state):
            return {"messages": ["Hello"]}
        
        updated_graph = adapter.add_node(graph=graph, node_name="my_node", node_function=my_node)
        assert "nodes" in updated_graph
        assert "my_node" in updated_graph["nodes"]

    def test_add_edge(self):
        """Test edge addition."""
        adapter = LangGraphAdapter()
        state_schema = {"messages": {"type": "list", "reducer": "add"}}
        graph = adapter.create_state_graph(state_schema=state_schema)
        graph = adapter.add_node(graph=graph, node_name="node_a", node_function=lambda s: s)
        graph = adapter.add_node(graph=graph, node_name="node_b", node_function=lambda s: s)
        updated_graph = adapter.add_edge(graph=graph, source="node_a", target="node_b")
        assert "edges" in updated_graph
        assert len(updated_graph["edges"]) == 1
        assert updated_graph["edges"][0]["source"] == "node_a"
        assert updated_graph["edges"][0]["target"] == "node_b"

    def test_add_conditional_edge(self):
        """Test conditional edge addition."""
        adapter = LangGraphAdapter()
        state_schema = {"messages": {"type": "list"}}
        graph = adapter.create_state_graph(state_schema=state_schema)
        
        def routing_fn(state):
            return "continue" if state.get("messages") else "end"
            
        mapping = {"continue": "node_b", "end": "end_node"}
        updated_graph = adapter.add_conditional_edge(
            graph=graph,
            source="node_a",
            condition_function=routing_fn,
            mapping=mapping
        )
        assert "conditional_edges" in updated_graph
        assert len(updated_graph["conditional_edges"]) == 1
        assert updated_graph["conditional_edges"][0]["source"] == "node_a"

    def test_compile_graph(self):
        """Test graph compilation."""
        adapter = LangGraphAdapter()
        state_schema = {"messages": {"type": "list", "reducer": "add"}}
        graph = adapter.create_state_graph(state_schema=state_schema)
        graph = adapter.add_node(graph=graph, node_name="node_a", node_function=lambda s: s)
        compiled = adapter.compile_graph(graph=graph, checkpointer="memory")
        assert "compiled" in compiled
        assert compiled["compiled"] is True
        assert compiled["checkpointer"] == "memory"

    def test_invoke_graph(self):
        """Test graph invocation."""
        adapter = LangGraphAdapter()
        state_schema = {"messages": {"type": "list", "reducer": "add"}}
        graph = adapter.create_state_graph(state_schema=state_schema)
        
        def my_node(state):
            return {"messages": state["messages"] + ["Hello"]}
        
        graph = adapter.add_node(graph=graph, node_name="my_node", node_function=my_node)
        compiled = adapter.compile_graph(graph=graph)
        result = adapter.invoke(compiled_graph=compiled, input_state={"messages": []})
        assert "messages" in result
        assert len(result["messages"]) > 0
        assert result["messages"][0] == "Hello"
        assert "output" in result

    def test_invoke_graph_with_task(self):
        """Test graph invocation with fallback task output."""
        adapter = LangGraphAdapter()
        graph = adapter.create_state_graph(state_schema={})
        compiled = adapter.compile_graph(graph=graph)
        result = adapter.invoke(compiled_graph=compiled, input_state={"task": "process data"})
        assert result["output"] == "Processed task: process data"

    def test_invoke_graph_default_output(self):
        """Test graph invocation with empty fallback."""
        adapter = LangGraphAdapter()
        graph = adapter.create_state_graph(state_schema={})
        compiled = adapter.compile_graph(graph=graph)
        result = adapter.invoke(compiled_graph=compiled, input_state={})
        assert result["output"] == "Graph execution finished."

    def test_stream_graph(self):
        """Test graph streaming."""
        adapter = LangGraphAdapter()
        state_schema = {"messages": {"type": "list", "reducer": "add"}}
        graph = adapter.create_state_graph(state_schema=state_schema)
        
        def my_node(state):
            return {"messages": state["messages"] + ["Hello"]}
        
        graph = adapter.add_node(graph=graph, node_name="my_node", node_function=my_node)
        compiled = adapter.compile_graph(graph=graph)
        
        # Test values mode
        stream_values = adapter.stream(compiled_graph=compiled, input_state={"messages": []}, stream_mode="values")
        assert isinstance(stream_values, list)
        assert len(stream_values) >= 2
        
        # Test updates mode
        stream_updates = adapter.stream(compiled_graph=compiled, input_state={"messages": []}, stream_mode="updates")
        assert isinstance(stream_updates, list)
        
        # Test tokens mode
        stream_tokens = adapter.stream(compiled_graph=compiled, input_state={"messages": []}, stream_mode="tokens")
        assert isinstance(stream_tokens, list)

    def test_supervisor_graph(self):
        """Test supervisor-worker graph creation."""
        adapter = LangGraphAdapter()
        supervisor = {"name": "supervisor", "role": "Manager"}
        workers = [{"name": "worker1", "role": "Developer"}]
        tasks = [{"description": "Build feature"}]
        graph = adapter.create_supervisor_graph(supervisor_agent=supervisor, worker_agents=workers, tasks=tasks)
        assert "supervisor" in graph
        assert len(graph["nodes"]) >= 2
        assert len(graph["edges"]) >= 1

    def test_hitle_graph(self):
        """Test HITL graph creation."""
        adapter = LangGraphAdapter()
        agent = {"name": "agent", "role": "Assistant"}
        
        def approval_function(state):
            return True
        
        tasks = [{"description": "Deploy"}]
        graph = adapter.create_hitle_graph(agent=agent, approval_function=approval_function, tasks=tasks)
        assert "hitle" in graph
        assert "hitl" in graph
        assert "approval_gate" in graph["nodes"]

    def test_dnk_agent_integration(self):
        """Test DNK OS Agent integration pattern."""
        class DNKAgent:
            def __init__(self):
                self.langgraph = LangGraphAdapter(graph_name="dnk_core")
            
            def create_supervisor_worker_graph(self):
                supervisor = {"name": "Antigravity", "role": "Supervisor"}
                workers = [{"name": "Герич", "role": "Worker"}]
                tasks = [{"description": "Execute task"}]
                return self.langgraph.create_supervisor_graph(
                    supervisor_agent=supervisor,
                    worker_agents=workers,
                    tasks=tasks
                )
            
            def execute_task(self, task: str) -> str:
                graph = self.create_supervisor_worker_graph()
                compiled = self.langgraph.compile_graph(graph=graph["graph"], checkpointer="memory")
                result = self.langgraph.invoke(compiled_graph=compiled, input_state={"task": task, "messages": []})
                return result["output"]

        agent = DNKAgent()
        out = agent.execute_task("Run Multi-Agent pipeline")
        assert isinstance(out, str)
        assert len(out) > 0

    def test_edge_cases_coverage(self):
        """Test edge cases to achieve 100% coverage."""
        adapter = LangGraphAdapter()
        
        # Test add_node/edge/conditional_edge on bare dict
        bare_graph = {}
        adapter.add_node(bare_graph, "n1", lambda s: s)
        adapter.add_edge(bare_graph, "n1", "n2")
        adapter.add_conditional_edge(bare_graph, "n1", lambda s: "ok", {"ok": "n2"})
        assert "nodes" in bare_graph
        assert "edges" in bare_graph
        assert "conditional_edges" in bare_graph
        
        # Test exception handling in node function during invoke
        def buggy_node(s):
            raise ValueError("Intentional error")
            
        buggy_graph = adapter.create_state_graph(state_schema={})
        adapter.add_node(buggy_graph, "bug", buggy_node)
        compiled_bug = adapter.compile_graph(buggy_graph)
        res = adapter.invoke(compiled_bug, {"task": "test"})
        assert "output" in res
        
        # Test stream with exception and with graph-nested nodes
        nested_compiled = {"graph": buggy_graph}
        stream_res = adapter.stream(nested_compiled, {"task": "test"}, stream_mode="values")
        assert len(stream_res) >= 1
        
        # Test empty messages output fallback
        empty_msg_graph = adapter.create_state_graph(state_schema={})
        compiled_empty = adapter.compile_graph(empty_msg_graph)
        empty_res = adapter.invoke(compiled_empty, {"messages": []})
        assert empty_res["output"] == "Completed"

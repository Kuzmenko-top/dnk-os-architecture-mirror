# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_supervisor.py"
# purpose: "Test suite for DNKSupervisor state graph orchestration"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from dnk_os.core.supervisor import DNKSupervisor
from dnk_os.core.checkpointer import MemoryCheckpointer, SQLiteCheckpointer


class TestDNKSupervisor:
    """Test suite for DNKSupervisor."""
    
    def test_init_default(self):
        """Test initialization with default parameters."""
        supervisor = DNKSupervisor(name="Antigravity")
        assert supervisor is not None
        assert supervisor.name == "Antigravity"
        assert supervisor.checkpointer is not None
        assert len(supervisor.workers) == 0
    
    def test_register_worker(self):
        """Test worker registration."""
        supervisor = DNKSupervisor()
        worker_config = {"name": "Герич", "role": "Worker"}
        capabilities = ["code", "research"]
        result = supervisor.register_worker(
            worker_name="Герич",
            worker_config=worker_config,
            capabilities=capabilities,
            extra="meta"
        )
        assert result is True
        assert len(supervisor.workers) == 1
        assert supervisor.workers["Герич"]["capabilities"] == ["code", "research"]
        assert supervisor.workers["Герич"]["extra"] == "meta"
    
    def test_create_state_graph(self):
        """Test state graph creation with default and custom schema."""
        supervisor = DNKSupervisor()
        supervisor.register_worker(
            worker_name="Герич",
            worker_config={"role": "Worker"},
            capabilities=["code"]
        )
        graph = supervisor.create_state_graph()
        assert graph is not None
        assert "state_schema" in graph
        assert "supervisor" in graph["nodes"]
        assert "Герич" in graph["nodes"]
        
        # Test with custom schema
        custom_schema = {"custom_field": "str"}
        graph2 = supervisor.create_state_graph(state_schema=custom_schema)
        assert graph2["state_schema"] == custom_schema
    
    def test_add_supervisor_node_custom_fn(self):
        """Test adding supervisor node with custom decision function."""
        supervisor = DNKSupervisor()
        graph = supervisor.langgraph.create_state_graph(state_schema={})
        
        def custom_decision(state):
            return {"current_worker": "CustomWorker"}
            
        graph = supervisor.add_supervisor_node(graph, supervisor_function=custom_decision)
        assert "supervisor" in graph["nodes"]
        assert graph["nodes"]["supervisor"]["function"]({}) == {"current_worker": "CustomWorker"}
        
        # Test default supervisor function routing
        supervisor.register_worker("CodeWorker", {}, ["code"])
        supervisor.register_worker("ResearchWorker", {}, ["research"])
        graph_def = supervisor.langgraph.create_state_graph(state_schema={})
        graph_def = supervisor.add_supervisor_node(graph_def)
        default_fn = graph_def["nodes"]["supervisor"]["function"]
        
        res1 = default_fn({"task": "Please code something"})
        assert res1["current_worker"] == "CodeWorker"
        
        res2 = default_fn({"task": "Do some research"})
        assert res2["current_worker"] == "ResearchWorker"
        
        res3 = default_fn({"task": "Random task without keywords"})
        assert res3["current_worker"] in ["CodeWorker", "ResearchWorker"]
    
    def test_add_worker_nodes_custom_fn(self):
        """Test adding worker nodes with custom worker functions."""
        supervisor = DNKSupervisor()
        supervisor.register_worker("WorkerA", {}, ["a"])
        supervisor.register_worker("WorkerB", {}, ["b"])
        graph = supervisor.langgraph.create_state_graph(state_schema={})
        
        custom_funcs = {
            "WorkerA": lambda state: {"custom": "outputA"}
        }
        graph = supervisor.add_worker_nodes(graph, worker_functions=custom_funcs)
        assert graph["nodes"]["WorkerA"]["function"]({}) == {"custom": "outputA"}
        assert graph["nodes"]["WorkerB"]["function"]({"task": "run"})["worker"] == "WorkerB"
    
    def test_add_conditional_routing_custom_fn(self):
        """Test conditional routing with custom router function."""
        supervisor = DNKSupervisor()
        supervisor.register_worker("WorkerA", {}, ["a"])
        graph = supervisor.langgraph.create_state_graph(state_schema={})
        graph = supervisor.add_supervisor_node(graph)
        graph = supervisor.add_worker_nodes(graph)
        
        def custom_router(state):
            return "WorkerA"
            
        graph = supervisor.add_conditional_routing(graph, routing_function=custom_router)
        assert len(graph["conditional_edges"]) == 1
        assert graph["conditional_edges"][0]["condition"]({}) == "WorkerA"
        
        # Test default router
        graph2 = supervisor.langgraph.create_state_graph(state_schema={})
        graph2 = supervisor.add_supervisor_node(graph2)
        graph2 = supervisor.add_worker_nodes(graph2)
        graph2 = supervisor.add_conditional_routing(graph2)
        assert graph2["conditional_edges"][0]["condition"]({"current_worker": "WorkerA"}) == "WorkerA"
        assert graph2["conditional_edges"][0]["condition"]({}) == "end"
    
    def test_compile_graph(self):
        """Test graph compilation."""
        supervisor = DNKSupervisor()
        worker_config = {"name": "Герич", "role": "Worker"}
        supervisor.register_worker(worker_name="Герич", worker_config=worker_config, capabilities=["code"])
        result = supervisor.compile()
        assert result is True
        assert supervisor.compiled_graph is not None
        
        # Test compile with checkpointer override
        mem_chk = MemoryCheckpointer()
        result2 = supervisor.compile(checkpointer=mem_chk)
        assert result2 is True
        assert supervisor.checkpointer is mem_chk
    
    def test_delegate_task(self):
        """Test task delegation with explicit worker selection and automatic routing."""
        supervisor = DNKSupervisor()
        supervisor.register_worker(worker_name="Герич", worker_config={"role": "Worker"}, capabilities=["code"])
        supervisor.register_worker(worker_name="Researcher", worker_config={"role": "Worker"}, capabilities=["research"])
        
        # Selected worker
        result = supervisor.delegate_task(task="Write code", selected_worker="Герич")
        assert result["worker"] == "Герич"
        assert result["status"] == "completed"
        
        # Auto route by capability
        result_auto = supervisor.delegate_task(task="Conduct scientific research")
        assert result_auto["worker"] == "Researcher"
        
        # Fallback to first worker when no keyword matches
        result_fallback = supervisor.delegate_task(task="General unknown topic")
        assert result_fallback["worker"] in ["Герич", "Researcher"]
        
        # When no workers registered
        empty_supervisor = DNKSupervisor()
        res_empty = empty_supervisor.delegate_task(task="Solo task")
        assert res_empty["worker"] == "supervisor"
    
    def test_get_state(self):
        """Test state persistence and retrieval."""
        supervisor = DNKSupervisor(checkpointer_backend="memory")
        worker_config = {"name": "Герич", "role": "Worker"}
        supervisor.register_worker(worker_name="Герич", worker_config=worker_config, capabilities=["code"])
        
        supervisor.delegate_task(task="Test task", thread_id="thread_1", selected_worker="Герич")
        state = supervisor.get_state(thread_id="thread_1")
        assert state is not None
        assert state["worker"] == "Герич"
        assert state["task"] == "Test task"
        
        # Test without checkpointer
        supervisor.checkpointer = None
        assert supervisor.get_state(thread_id="thread_1") is None
    
    def test_list_workers(self):
        """Test worker listing."""
        supervisor = DNKSupervisor()
        worker1 = {"name": "Worker1", "role": "Coder"}
        worker2 = {"name": "Worker2", "role": "Researcher"}
        supervisor.register_worker(worker_name="Worker1", worker_config=worker1, capabilities=["code"])
        supervisor.register_worker(worker_name="Worker2", worker_config=worker2, capabilities=["research"])
        workers = supervisor.list_workers()
        assert len(workers) == 2
        assert any(w["name"] == "Worker1" for w in workers)
        assert any(w["name"] == "Worker2" for w in workers)
    
    def test_supervisor_with_sqlite_checkpointer(self, tmp_path):
        """Test supervisor with SQLite checkpointer."""
        db_path = tmp_path / "test.db"
        checkpointer = SQLiteCheckpointer(db_path=str(db_path))
        supervisor = DNKSupervisor(checkpointer=checkpointer)
        assert supervisor.checkpointer is checkpointer
        
        supervisor.register_worker("Герич", {}, ["code"])
        supervisor.delegate_task("Write SQL", thread_id="t_sql")
        saved = supervisor.get_state("t_sql")
        assert saved is not None
        assert saved["task"] == "Write SQL"

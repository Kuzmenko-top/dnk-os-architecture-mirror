# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_worker.py"
# purpose: "Test suite for DNKWorker agent and adapter integrations"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from dnk_os.core.worker import DNKWorker
from adapters.transformers_adapter import TransformersAdapter
from adapters.llamaindex_adapter import LlamaIndexAdapter
from adapters.crewai_adapter import CrewAIAdapter
from adapters.autogen_adapter import AutoGenAdapter
from adapters.langgraph_adapter import LangGraphAdapter


class TestDNKWorker:
    """Test suite for DNKWorker."""
    
    def test_init_default(self):
        """Test initialization with default parameters."""
        worker = DNKWorker(name="Герич")
        assert worker is not None
        assert worker.name == "Герич"
        assert "code" in worker.capabilities
        assert worker.transformers is not None
        assert worker.llamaindex is not None
        assert worker.crewai is not None
        assert worker.autogen is not None
        assert worker.langgraph is not None

    def test_init_custom_adapters(self):
        """Test initialization with custom adapter injection."""
        tr = TransformersAdapter(model_name="gpt2")
        li = LlamaIndexAdapter()
        cr = CrewAIAdapter()
        ag = AutoGenAdapter()
        lg = LangGraphAdapter()
        worker = DNKWorker(
            name="CustomWorker",
            capabilities=["all"],
            transformers_adapter=tr,
            llamaindex_adapter=li,
            crewai_adapter=cr,
            autogen_adapter=ag,
            langgraph_adapter=lg,
        )
        assert worker.transformers is tr
        assert worker.llamaindex is li
        assert worker.crewai is cr
        assert worker.autogen is ag
        assert worker.langgraph is lg
    
    def test_execute_generation(self):
        """Test text generation task."""
        worker = DNKWorker()
        result = worker.execute_generation(prompt="Hello, how are", max_tokens=50)
        assert "output" in result
        assert isinstance(result["output"], str)
        assert result["tokens_used"] > 0
        assert result["status"] == "completed"
    
    def test_execute_rag(self):
        """Test RAG query task."""
        worker = DNKWorker()
        documents = ["Paris is the capital of France.", "Berlin is the capital of Germany."]
        result = worker.execute_rag(query="What is the capital of France?", documents=documents)
        assert "answer" in result
        assert "output" in result
        assert "sources" in result
        assert "confidence" in result
        assert result["status"] == "completed"
    
    def test_execute_crew(self):
        """Test crew orchestration task with default and custom agents."""
        worker = DNKWorker()
        # Default agents
        result = worker.execute_crew(task_description="Research AI trends")
        assert "output" in result
        assert "crew_status" in result
        assert result["status"] == "completed"
        
        # Custom agents
        agent_custom = worker.crewai.create_agent(
            name="Lead", 
            role="Lead", 
            goal="Lead team",
            backstory="Lead bio"
        )
        result_custom = worker.execute_crew(task_description="Build system", agents=[agent_custom])
        assert "output" in result_custom
    
    def test_execute_conversation_two_agents(self):
        """Test multi-agent conversation with 2 participants."""
        worker = DNKWorker()
        result = worker.execute_conversation(topic="AI discussion", participants=2)
        assert "summary" in result
        assert "chat_history" in result
        assert "output" in result
        assert result["status"] == "completed"
    
    def test_execute_conversation_multi_agents(self):
        """Test multi-agent conversation with >2 participants."""
        worker = DNKWorker()
        result = worker.execute_conversation(topic="Deep debate on AI ethics", participants=3)
        assert "summary" in result
        assert "chat_history" in result
        assert result["status"] == "completed"
    
    def test_execute_graph(self):
        """Test state graph execution task."""
        worker = DNKWorker()
        graph_config = {"type": "sequential", "nodes": ["node_a", "node_b"]}
        input_state = {"messages": []}
        result = worker.execute_graph(graph_config=graph_config, input_state=input_state)
        assert "output" in result
        assert "state_snapshots" in result
        assert result["status"] == "completed"
    
    def test_load_knowledge_base(self):
        """Test knowledge base loading."""
        worker = DNKWorker()
        documents = ["Document 1", "Document 2"]
        count = worker.load_knowledge_base(documents=documents)
        assert count == 2
    
    def test_get_capabilities(self):
        """Test capability listing."""
        worker = DNKWorker(capabilities=["code", "research", "translation"])
        caps = worker.get_capabilities()
        assert len(caps) == 3
        assert "code" in caps
        assert "research" in caps
        assert "translation" in caps
    
    def test_execute_task_auto_detect(self):
        """Test auto-detection of task type from keywords."""
        worker = DNKWorker()
        
        # Generation
        res_gen = worker.execute_task(task="Generate text about AI")
        assert "output" in res_gen
        
        # RAG
        res_rag = worker.execute_task(task="Find capital of France in knowledge base")
        assert "answer" in res_rag
        
        # Crew
        res_crew = worker.execute_task(task="Assemble crew team to write report")
        assert "crew_status" in res_crew
        
        # Conversation
        res_chat = worker.execute_task(task="Start chat debate on technology")
        assert "summary" in res_chat
        
        # Graph
        res_graph = worker.execute_task(task="Run state workflow pipeline")
        assert "state_snapshots" in res_graph
    
    def test_execute_task_explicit_types(self):
        """Test explicit task type specification."""
        worker = DNKWorker()
        
        res_rag = worker.execute_task(task="What is ML?", task_type="rag")
        assert "answer" in res_rag
        
        res_crew = worker.execute_task(task="Run team", task_type="crew")
        assert "crew_status" in res_crew
        
        res_chat = worker.execute_task(task="Chat about ML", task_type="conversation")
        assert "summary" in res_chat
        
        res_graph = worker.execute_task(task="Graph task", task_type="graph")
        assert "state_snapshots" in res_graph
        
        res_gen = worker.execute_task(task="Write story", task_type="generation")
        assert "output" in res_gen

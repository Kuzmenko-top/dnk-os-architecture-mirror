# --- DNK-MRH-HEADER ---
# mrh_id: "tests/test_dnk_agentswarms_adapter.py"
# purpose: "Unit & Integration Tests for DNKAgentSwarmsAdapter, Multi-Agent Swarm DAG & Lakehouse BI."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Antigravity (Mentor) & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import unittest
import asyncio
from core.adapters.dnk_agentswarms_adapter import (
    DNKAgentSwarmsAdapter,
    SwarmNodeType,
    SwarmWorkflowNode,
    SwarmWorkflowEdge,
    SwarmWorkflowDAG,
    SemanticMetricSpec
)


class TestDNKAgentSwarmsAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = DNKAgentSwarmsAdapter()

    def test_lakehouse_query_execution(self):
        """Tests executing SQL against embedded Lakehouse engine."""
        res = self.adapter.query_lakehouse("SELECT COUNT(*) as total_orders FROM shopify_orders")
        self.assertEqual(len(res.rows), 1)
        self.assertEqual(res.rows[0][0], 3)
        self.assertIn("total_orders", res.columns)
        self.assertGreater(res.execution_time_ms, 0.0)

    def test_ai_analyst_nl2sql_reasoning(self):
        """Tests AI Analyst natural language to SQL translation."""
        analysis = self.adapter.analyze_nl2sql("What is our total revenue by customer?")
        self.assertIn("shopify_orders", analysis["generated_sql"])
        self.assertEqual(analysis["chart_type"], "bar")
        self.assertEqual(len(analysis["reasoning_plan"]), 4)
        self.assertGreater(analysis["result"]["row_count"], 0)

    def test_swarm_workflow_dag_creation_and_execution(self):
        """Tests creating and executing a 6-node multi-agent workflow DAG."""
        nodes = [
            SwarmWorkflowNode(id="n1", node_type=SwarmNodeType.AGENT, name="Chief Planner", config={"agent": "gerych_prime"}),
            SwarmWorkflowNode(id="n2", node_type=SwarmNodeType.ROUTER, name="Task Router", config={"routing_key": "target_domain"}),
            SwarmWorkflowNode(id="n3", node_type=SwarmNodeType.TOOL, name="Shopify Generator", config={"tool_name": "dnk_shopify_compiler"}),
            SwarmWorkflowNode(id="n4", node_type=SwarmNodeType.CONDITION, name="WCAG Quality Gate", config={"expression": "contrast >= 4.5"}),
            SwarmWorkflowNode(id="n5", node_type=SwarmNodeType.APPROVAL, name="Human-in-Loop Approval", config={}),
            SwarmWorkflowNode(id="n6", node_type=SwarmNodeType.LOOP, name="Self-Healing Loop", config={}),
        ]
        edges = [
            SwarmWorkflowEdge(id="e1", source_node_id="n1", target_node_id="n2"),
            SwarmWorkflowEdge(id="e2", source_node_id="n2", target_node_id="n3"),
            SwarmWorkflowEdge(id="e3", source_node_id="n3", target_node_id="n4"),
            SwarmWorkflowEdge(id="e4", source_node_id="n4", target_node_id="n5"),
            SwarmWorkflowEdge(id="e5", source_node_id="n5", target_node_id="n6"),
        ]

        dag = self.adapter.create_workflow(title="Autonomous E-Com Synthesis DAG", nodes=nodes, edges=edges)
        self.assertEqual(dag.workflow_id, "wf-001")
        self.assertEqual(len(dag.nodes), 6)

        async def run_exec():
            res = await self.adapter.execute_workflow("wf-001", inputs={"target_domain": "shopify_checkout"})
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["steps_executed"], 6)
            self.assertIn("n1_out", res["final_context"])

        asyncio.run(run_exec())


if __name__ == "__main__":
    unittest.main()

# --- DNK-MRH-HEADER ---
# mrh_id: "core/agent_factory/prime_engine/prime_orchestrator.py"
# purpose: "Gerych Prime Orchestrator Loop (Hermes 3.0) inspired by PrimeAgent framework: orchestrating Swarm team, evaluating execution quality, and reflecting on cycle results."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

from typing import List, Dict, Any
from core.agent_factory.prime_engine.swarm_dispatcher import SwarmDispatcher, SwarmTaskResult
from services.dnk_obsidian_task_forest.src.obsidian_task_forest import ObsidianTaskForestParser
from services.dnk_obsidian_task_forest.src.task_graph_reporter import TaskGraphReporter


class GerychPrimeOrchestrator:
    """
    Gerych (Hermes 3.0) Prime Orchestrator Loop.
    Coordinates Swarm Team, evaluates execution, triggers task graph updates & cycle reports.
    """
    def __init__(self, vault_path: str = "docs/tasks") -> None:
        self.vault_path = vault_path
        self.dispatcher = SwarmDispatcher()
        self.reporter = TaskGraphReporter(vault_path=vault_path)

    def run_orchestration_cycle(self) -> Dict[str, Any]:
        """
        Executes complete orchestration cycle across task forest.
        """
        parser = ObsidianTaskForestParser(self.vault_path)
        nodes = parser.scan_vault()

        results: List[SwarmTaskResult] = []
        for node in nodes.values():
            if node.status != "completed":
                res = self.dispatcher.dispatch_task(
                    task_id=node.id,
                    task_title=node.title,
                    required_capability=node.plant_scale
                )
                results.append(res)

        # Check and generate cycle reports for 100% completed trees
        generated_reports = self.reporter.check_and_generate_cycle_reports()

        return {
            "status": "success",
            "scanned_nodes_count": len(nodes),
            "executed_tasks_count": len(results),
            "generated_reports_count": len(generated_reports),
            "generated_reports": generated_reports
        }

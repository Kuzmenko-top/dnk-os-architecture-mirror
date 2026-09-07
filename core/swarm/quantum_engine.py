# --- DNK-MRH-HEADER ---
# mrh_id: "core_swarm_quantum_engine"
# purpose: "Task Quantum Swarm Engine: Atomic Task Decomposition, Parallel Subagent Pipeline & Bounded Retry Self-Healing"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import asyncio
import logging
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field

from .subagents import BuilderSubagent, TesterSubagent, AuditorSubagent, SubagentResult

logger = logging.getLogger("dnk.swarm.quantum_engine")


class TaskQuantum(BaseModel):
    quantum_id: str
    title: str
    target_files: List[str] = Field(default_factory=list, max_length=3)
    test_files: List[str] = Field(default_factory=list)
    instructions: str = ""
    dependencies: List[str] = Field(default_factory=list)
    status: Literal["PENDING", "IN_PROGRESS", "VERIFIED", "FAILED", "ROLLED_BACK"] = "PENDING"
    max_turns: int = 12
    retry_count: int = 0
    max_retries: int = 2
    error_summary: Optional[str] = None
    artifacts: Dict[str, Any] = Field(default_factory=dict)


class QuantumExecutionResult(BaseModel):
    task_id: str
    total_quanta: int
    completed_quanta: int
    failed_quanta: int
    overall_status: Literal["SUCCESS", "FAILED", "PARTIAL"]
    execution_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    quanta_results: Dict[str, TaskQuantum] = Field(default_factory=dict)


class QuantumDecomposer:
    """Decomposes monolithic tasks into bounded, verified atomic task quanta (<= 3 files each)."""

    @staticmethod
    def decompose_task(
        task_id: str,
        title: str,
        file_specs: List[Dict[str, Any]]
    ) -> List[TaskQuantum]:
        """
        Groups file specifications into atomic units with auto-generated test mappings and dependency links.
        """
        quanta: List[TaskQuantum] = []
        chunk_size = 2  # Recommended 2-3 files per quantum

        for i in range(0, len(file_specs), chunk_size):
            chunk = file_specs[i:i + chunk_size]
            q_id = f"{task_id}_q{len(quanta) + 1:02d}"
            
            target_files = [f.get("file_path") for f in chunk if f.get("file_path")]
            test_files = [f.get("test_path") for f in chunk if f.get("test_path")]
            instructions_list = [f.get("instruction", "") for f in chunk if f.get("instruction")]

            # Compute prerequisites (previous quantum)
            dependencies = [quanta[-1].quantum_id] if quanta else []

            q = TaskQuantum(
                quantum_id=q_id,
                title=f"[{q_id}] {chunk[0].get('component', 'Quantum Unit')}",
                target_files=target_files[:3],
                test_files=test_files,
                instructions="; ".join(instructions_list),
                dependencies=dependencies
            )
            quanta.append(q)

        if not quanta:
            # Fallback for single abstract task
            quanta.append(
                TaskQuantum(
                    quantum_id=f"{task_id}_q01",
                    title=f"[{task_id}_q01] {title}",
                    target_files=[],
                    test_files=[],
                    instructions=title
                )
            )

        return quanta


class QuantumSwarmCoordinator:
    """
    Coordinates execution of Task Quanta across specialized subagents with early stopping and self-healing.
    """

    def __init__(
        self,
        builder: Optional[BuilderSubagent] = None,
        tester: Optional[TesterSubagent] = None,
        auditor: Optional[AuditorSubagent] = None
    ):
        self.builder = builder or BuilderSubagent()
        self.tester = tester or TesterSubagent()
        self.auditor = auditor or AuditorSubagent()

    async def execute_quantum(self, quantum: TaskQuantum) -> TaskQuantum:
        """Executes a single quantum through Builder -> Tester -> Auditor with self-healing retry."""
        quantum.status = "IN_PROGRESS"
        
        while quantum.retry_count <= quantum.max_retries:
            logger.info("Executing quantum %s (Attempt %s/%s)", quantum.quantum_id, quantum.retry_count + 1, quantum.max_retries + 1)

            # 1. Builder Phase
            build_res = self.builder.execute_quantum(
                quantum_name=quantum.title,
                target_files=quantum.target_files,
                instructions=quantum.instructions,
                context={"error_summary": quantum.error_summary}
            )
            if not build_res.success:
                quantum.retry_count += 1
                quantum.error_summary = f"Builder failed: {'; '.join(build_res.errors)}"
                continue

            # 2. Tester Phase
            test_res = self.tester.run_tests(test_files=quantum.test_files)
            if not test_res.success:
                quantum.retry_count += 1
                quantum.error_summary = f"Tester failed: {'; '.join(test_res.errors)}"
                continue

            # 3. Auditor Phase
            all_files = list(set(quantum.target_files + quantum.test_files))
            audit_res = self.auditor.audit_files(file_paths=all_files)
            if not audit_res.success:
                quantum.retry_count += 1
                quantum.error_summary = f"Auditor failed: {'; '.join(audit_res.errors)}"
                continue

            # All 3 subagent gates passed!
            quantum.status = "VERIFIED"
            quantum.error_summary = None
            quantum.artifacts = {
                "builder": build_res.output,
                "tester": test_res.output,
                "auditor": audit_res.output
            }
            return quantum

        # Exceeded retries
        quantum.status = "FAILED"
        return quantum

    async def execute_task_dag(
        self,
        task_id: str,
        quanta: List[TaskQuantum]
    ) -> QuantumExecutionResult:
        """
        Executes a sequence/DAG of quanta in dependency order.
        Halts immediately if any prerequisite quantum fails.
        """
        quanta_dict = {q.quantum_id: q for q in quanta}
        timeline = []
        completed = 0
        failed = 0

        for q in quanta:
            # Check prerequisites
            prereqs_met = all(
                quanta_dict[dep].status == "VERIFIED"
                for dep in q.dependencies
                if dep in quanta_dict
            )

            if not prereqs_met:
                q.status = "ROLLED_BACK"
                q.error_summary = "Blocked by prerequisite quantum failure."
                timeline.append({"quantum_id": q.quantum_id, "status": "ROLLED_BACK"})
                failed += 1
                continue

            executed_q = await self.execute_quantum(q)
            timeline.append({
                "quantum_id": executed_q.quantum_id,
                "status": executed_q.status,
                "error": executed_q.error_summary
            })

            if executed_q.status == "VERIFIED":
                completed += 1
            else:
                failed += 1
                # Fail-closed: mark all remaining dependent/pending quanta as ROLLED_BACK
                for rem_q in quanta:
                    if rem_q.status == "PENDING":
                        rem_q.status = "ROLLED_BACK"
                        rem_q.error_summary = f"Aborted due to upstream failure in {executed_q.quantum_id}."
                break

        overall = "SUCCESS" if failed == 0 else ("PARTIAL" if completed > 0 else "FAILED")


        return QuantumExecutionResult(
            task_id=task_id,
            total_quanta=len(quanta),
            completed_quanta=completed,
            failed_quanta=failed,
            overall_status=overall,
            execution_timeline=timeline,
            quanta_results=quanta_dict
        )

# --- DNK-MRH-HEADER ---
# mrh_id: "core_analyzers_run_analyzer"
# purpose: "Run Analyzer interface and concrete Postgres implementation to extract execution patterns and errors"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID
from collections import Counter

from core.models.improvement import RunAnalysis, ImprovementSuggestion
from core.ports.timeline_repository import ITimelineRepository

class RunAnalyzer(ABC):
    @abstractmethod
    async def analyze_runs(
        self,
        agent_id: UUID,
        limit: int = 100,
    ) -> RunAnalysis:
        pass

    @abstractmethod
    def detect_patterns(
        self,
        runs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        pass

class PostgresRunAnalyzer(RunAnalyzer):
    def __init__(self, repo: ITimelineRepository):
        self.repo = repo

    async def analyze_runs(
        self,
        agent_id: UUID,
        limit: int = 100,
    ) -> RunAnalysis:
        runs = await self.repo.get_runs_by_agent(agent_id, limit=limit)
        if not runs:
            return RunAnalysis(
                agent_id=str(agent_id),
                total_runs=0,
                success_rate=1.0,
                avg_duration_seconds=0.0,
                common_errors=[],
                bottlenecks=[],
                suggestions=[]
            )

        runs_data = []
        total_duration = 0.0
        completed_runs_count = 0
        successful_runs_count = 0

        for r in runs:
            # Fetch tasks associated with this run
            tasks = await self.repo.get_tasks_by_run(r.id)
            
            run_dict = {
                "id": str(r.id),
                "agent_id": str(r.agent_id),
                "run_type": r.run_type,
                "status": r.status,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "tasks": [
                    {
                        "id": str(t.id),
                        "task_type": t.task_type,
                        "status": t.status,
                        "error": t.error,
                        "started_at": t.started_at,
                        "completed_at": t.completed_at
                    }
                    for t in tasks
                ]
            }
            runs_data.append(run_dict)

            if r.status == "completed":
                successful_runs_count += 1
            
            if r.started_at and r.completed_at:
                duration = (r.completed_at - r.started_at).total_seconds()
                total_duration += duration
                completed_runs_count += 1

        # Success rate
        success_rate = successful_runs_count / len(runs)
        avg_duration = (total_duration / completed_runs_count) if completed_runs_count > 0 else 0.0

        patterns = self.detect_patterns(runs_data)

        # Map patterns to Pydantic Suggestions
        suggestions = []
        for sug in patterns.get("suggestions", []):
            suggestions.append(ImprovementSuggestion(**sug))

        return RunAnalysis(
            agent_id=str(agent_id),
            total_runs=len(runs),
            success_rate=success_rate,
            avg_duration_seconds=avg_duration,
            common_errors=patterns.get("common_errors", []),
            bottlenecks=patterns.get("bottlenecks", []),
            suggestions=suggestions
        )

    def detect_patterns(
        self,
        runs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        errors = []
        bottlenecks = []
        suggestions = []

        task_failures = Counter()
        task_counts = Counter()
        task_durations = {}

        for r in runs:
            for t in r.get("tasks", []):
                task_type = t["task_type"]
                task_counts[task_type] += 1
                
                if t.get("error"):
                    errors.append(t["error"])
                
                if t["status"] == "failed":
                    task_failures[task_type] += 1
                
                if t["started_at"] and t["completed_at"]:
                    dur = (t["completed_at"] - t["started_at"]).total_seconds()
                    if task_type not in task_durations:
                        task_durations[task_type] = []
                    task_durations[task_type].append(dur)

        # Deduplicate common errors
        common_errors = list(set(errors))

        # Check for bottlenecks based on failure rates and durations
        for task_type, total in task_counts.items():
            failed = task_failures[task_type]
            fail_rate = failed / total
            
            # If failure rate is high
            if fail_rate > 0.2:
                bottlenecks.append(f"task_type={task_type} часто фейлиться ({fail_rate*100:.1f}% failures)")
                
                # Suggest prompt refinement or retry policy
                suggestions.append({
                    "category": "prompt",
                    "description": f"High failure rate detected for task type: {task_type}.",
                    "priority": "high" if fail_rate > 0.5 else "medium",
                    "estimated_impact": "high",
                    "suggested_action": f"Оновити prompt для {task_type} для покращення точності"
                })
                
                suggestions.append({
                    "category": "retry_policy",
                    "description": f"Retry policy recommendation for failing task {task_type}.",
                    "priority": "medium",
                    "estimated_impact": "medium",
                    "suggested_action": f"Збільшити кількість повторів для {task_type} у retry_policy"
                })

            # Check durations
            durs = task_durations.get(task_type, [])
            if durs:
                avg_dur = sum(durs) / len(durs)
                if avg_dur > 30.0:  # arbitrary threshold for slow tasks
                    bottlenecks.append(f"task_type={task_type} виконується занадто довго (avg {avg_dur:.1f}s)")
                    
                    suggestions.append({
                        "category": "timeout",
                        "description": f"Task type {task_type} has a high execution duration.",
                        "priority": "low",
                        "estimated_impact": "medium",
                        "suggested_action": f"Збільшити timeout для {task_type} до {int(avg_dur * 1.5)}s"
                    })

        # General error pattern detection
        for err in common_errors:
            err_lower = err.lower()
            if "timeout" in err_lower or "timed out" in err_lower:
                suggestions.append({
                    "category": "timeout",
                    "description": f"Detected timeout error: '{err}'.",
                    "priority": "high",
                    "estimated_impact": "high",
                    "suggested_action": "Збільшити timeout у конфігурації виконання"
                })
            elif "rate limit" in err_lower or "429" in err_lower:
                suggestions.append({
                    "category": "retry_policy",
                    "description": f"Rate limit error detected: '{err}'.",
                    "priority": "high",
                    "estimated_impact": "high",
                    "suggested_action": "Впровадити експоненціальний бекофф у retry_policy"
                })
            elif "tool" in err_lower or "no tool found" in err_lower:
                suggestions.append({
                    "category": "tool_selection",
                    "description": f"Tool-related failure detected: '{err}'.",
                    "priority": "medium",
                    "estimated_impact": "medium",
                    "suggested_action": "Переглянути вибір інструментів (tool_selection) для цього агента"
                })

        return {
            "common_errors": common_errors[:10],  # cap at 10
            "bottlenecks": bottlenecks,
            "suggestions": suggestions
        }

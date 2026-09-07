# --- DNK-MRH-HEADER ---
# mrh_id: "core/task_engine.py"
# purpose: "Tree Task Graph & Trajectory Engine for DNK OS with Live PostgreSQL Synchronization."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "0.2.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class TaskEngine:
    """
    Tree-structured task graph manager & trajectory logger for DNK OS
    with live PostgreSQL task synchronization support.
    """
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {
            "ROOT": {
                "id": "ROOT",
                "label": "DNK OS 1.0.0",
                "type": "epic",
                "status": "in_progress",
                "phase": "P0",
            }
        }
        self._trajectories: Dict[str, List[Dict[str, Any]]] = {}

    def _get_db_connection(self):
        pg_url = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/dnk_hub")
        try:
            import psycopg2
            return psycopg2.connect(pg_url, connect_timeout=3)
        except Exception:
            return None

    def sync_with_db(self, project_id: Optional[str] = None) -> None:
        """Fetches live tasks from PostgreSQL and synchronizes the local task engine memory."""
        conn = self._get_db_connection()
        if not conn:
            return

        try:
            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                query = "SELECT id, title, status, progress, verification_status, project_id FROM tasks"
                if project_id:
                    cur.execute(query + " WHERE project_id = %s", (project_id,))
                else:
                    cur.execute(query)
                rows = cur.fetchall()
                for row in rows:
                    task_id = str(row["id"])
                    self._tasks[task_id] = {
                        "id": task_id,
                        "label": row["title"],
                        "type": "task",
                        "status": "done" if row["status"] == "completed" else row["status"],
                        "progress": row["progress"],
                        "verification_status": row["verification_status"],
                        "project_id": row["project_id"]
                    }
        except Exception:
            pass
        finally:
            conn.close()

    def add_task(self, task_id: str, label: str, task_type: str = "task", phase: str = "P1", status: str = "todo") -> Dict[str, Any]:
        task = {
            "id": task_id,
            "label": label,
            "type": task_type,
            "phase": phase,
            "status": status,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._tasks[task_id] = task
        return task

    def update_status(self, task_id: str, new_status: str) -> bool:
        # First try to update locally
        updated = False
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = new_status
            updated = True

        # Log to local telemetry engine
        try:
            from core.local_telemetry import local_telemetry
            local_telemetry.log_step("task_engine", f"Task {task_id} updated to {new_status}")
        except Exception:
            pass

        # Try to sync with PostgreSQL DB if task is numeric
        if task_id.isdigit():
            conn = self._get_db_connection()
            if conn:
                try:
                    db_status = "completed" if new_status == "done" else new_status
                    with conn.cursor() as cur:
                        cur.execute("UPDATE tasks SET status = %s WHERE id = %s", (db_status, int(task_id)))
                        conn.commit()
                        updated = True
                except Exception:
                    pass
                finally:
                    conn.close()

        return updated

    def log_step(self, task_id: str, action: str, result: str, tokens_used: int = 0) -> Dict[str, Any]:
        if task_id not in self._trajectories:
            self._trajectories[task_id] = []
        step = {
            "step_index": len(self._trajectories[task_id]) + 1,
            "action": action,
            "result": result,
            "tokens_used": tokens_used,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._trajectories[task_id].append(step)
        return step

    def get_victory_map(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        # Always run database synchronization before generating the victory map
        self.sync_with_db(project_id)

        total = len(self._tasks)
        done = sum(1 for t in self._tasks.values() if t["status"] in ["done", "completed"])
        return {
            "total_tasks": total,
            "completed_tasks": done,
            "victory_percentage": round((done / total) * 100, 2) if total > 0 else 0.0,
            "system": "DNK OS 1.0.0",
        }

task_engine = TaskEngine()

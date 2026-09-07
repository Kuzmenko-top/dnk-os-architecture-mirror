# --- DNK-MRH-HEADER ---
# mrh_id: "supervisor/dispatcher.py"
# purpose: "Implement Task Dispatcher to push tasks to Redis queue or run local task thread fallback."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import json
import logging
from typing import Dict, Any

logger = logging.getLogger("supervisor_dispatcher")

class WorkerDispatcher:
    def __init__(self, r_client=None):
        self.r_client = r_client

    def dispatch_to_worker(self, run_id: str, skill_id: str, context: Dict[str, Any]):
        payload = {
            "run_id": run_id,
            "skill_id": skill_id,
            "context": context
        }
        payload_str = json.dumps(payload)
        
        if self.r_client:
            try:
                # Push task to Redis queue 'dnk_canvas_tasks'
                self.r_client.rpush("dnk_canvas_tasks", payload_str)
                # Also publish event
                self.r_client.publish("canvas.task_dispatched", payload_str)
                logger.info(f"Successfully dispatched run {run_id} to Redis queue 'dnk_canvas_tasks'")
                return True
            except Exception as e:
                logger.warning(f"Failed to dispatch to Redis: {e}. Falling back to local/in-memory queue simulation.")
        
        # Local simulated dispatch or background run (handled in supervisor/worker loop)
        logger.info(f"Local queue dispatcher: run {run_id} scheduled.")
        return False

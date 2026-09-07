# --- DNK-MRH-HEADER ---
# mrh_id: "dnk_canvas_worker/main.py"
# purpose: "Main execution daemon for Redis-backed background worker queues."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import os
import sys
import json
import time
import logging
import redis

# Add canvas_api to python path so we can import main db models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dnk_canvas_api.main import SessionLocal, DATABASE_URL, REDIS_URL
from workers.design_workspace_worker import DesignWorkspaceWorker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dnk_canvas_worker")

def main():
    logger.info("Starting DNK Canvas Background Worker...")
    logger.info(f"Database URL: {DATABASE_URL}")
    logger.info(f"Redis URL: {REDIS_URL}")

    # Connect to Redis
    r_client = None
    try:
        r_client = redis.from_url(REDIS_URL)
        r_client.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}. Worker entering simulated mode.")

    if not r_client:
        logger.info("Worker will run in simulation / poll-based mode for test suite harness.")
        # Sleeping to keep process alive or exiting based on env
        if os.getenv("WORKER_ONESHOT_SIMULATION", "false").lower() == "true":
            return
        while True:
            time.sleep(5)

    # Redis loop
    logger.info("Waiting for tasks in 'dnk_canvas_tasks' queue...")
    while True:
        try:
            # Block pop from queue
            task_data = r_client.blpop("dnk_canvas_tasks", timeout=5)
            if task_data:
                # task_data is tuple: (queue_name, payload)
                payload_str = task_data[1]
                logger.info(f"Received task: {payload_str}")
                payload = json.loads(payload_str)
                
                run_id = payload.get("run_id")
                skill_id = payload.get("skill_id")
                context = payload.get("context")

                db = SessionLocal()
                try:
                    DesignWorkspaceWorker.process_task(db, run_id, skill_id, context)
                except Exception as process_err:
                    logger.error(f"Error processing task {run_id}: {process_err}")
                finally:
                    db.close()
        except redis.ConnectionError:
            logger.warning("Lost connection to Redis. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Worker shutting down gracefully.")
            break
        except Exception as e:
            logger.error(f"Unexpected worker error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()

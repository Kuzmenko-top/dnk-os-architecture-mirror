# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_resilience_engine"
# purpose: "Resilience Engine: Circuit Breaker, DLQ & Exponential Backoff Retry (DNK-PLATFORM-SCALE-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from apps.api.db.models.task_dlq import TaskDLQModel


class CircuitBreaker:
    """
    Circuit Breaker State Machine:
    - CLOSED: Normal operation. Errors recorded.
    - OPEN: Service tripped due to high failure rate. Requests fail fast.
    - HALF_OPEN: Testing if downstream has recovered.
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold: int = 5, recovery_timeout_seconds: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()

    def allow_execution(self) -> bool:
        now = time.time()
        if self.state == self.OPEN:
            if now - self.last_state_change >= self.recovery_timeout_seconds:
                self.state = self.HALF_OPEN
                self.last_state_change = now
                return True
            return False
        return True

    def record_success(self):
        if self.state == self.HALF_OPEN:
            self.state = self.CLOSED
            self.failure_count = 0
            self.last_state_change = time.time()
        elif self.state == self.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold or self.state == self.HALF_OPEN:
            self.state = self.OPEN
            self.last_state_change = time.time()


class ResilienceEngine:
    """
    Resilience Engine providing Circuit Breaker protection, Dead Letter Queue (DLQ)
    persistence, and Exponential Backoff with Jitter calculation.
    """

    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

    def get_circuit_breaker(self, key: str) -> CircuitBreaker:
        if key not in self._circuit_breakers:
            self._circuit_breakers[key] = CircuitBreaker()
        return self._circuit_breakers[key]

    @staticmethod
    def calculate_exponential_backoff(
        attempt: int, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True
    ) -> float:
        delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
        if jitter:
            delay = delay * random.uniform(0.8, 1.2)
        return round(delay, 2)

    def send_to_dlq(
        self,
        db: Session,
        original_task_id: str,
        error_message: str,
        payload: Dict[str, Any],
        queue_id: Optional[str] = None,
        max_retries: int = 3,
    ) -> TaskDLQModel:
        dlq_entry = TaskDLQModel(
            original_task_id=original_task_id,
            queue_id=queue_id,
            error_message=error_message,
            retry_count=0,
            max_retries=max_retries,
            payload=payload,
            status="failed",
            created_at=datetime.now(timezone.utc),
        )
        db.add(dlq_entry)
        db.commit()
        db.refresh(dlq_entry)
        return dlq_entry

    def retry_dlq_task(self, db: Session, dlq_id: str) -> Optional[TaskDLQModel]:
        entry = db.query(TaskDLQModel).filter(TaskDLQModel.id == dlq_id).first()
        if not entry:
            return None

        if entry.retry_count >= entry.max_retries:
            entry.status = "abandoned"
            db.commit()
            return entry

        entry.retry_count += 1
        entry.status = "retrying"
        delay_sec = self.calculate_exponential_backoff(entry.retry_count)
        entry.next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_sec)
        db.commit()
        db.refresh(entry)
        return entry

    def purge_dlq_task(self, db: Session, dlq_id: str) -> bool:
        entry = db.query(TaskDLQModel).filter(TaskDLQModel.id == dlq_id).first()
        if entry:
            db.delete(entry)
            db.commit()
            return True
        return False

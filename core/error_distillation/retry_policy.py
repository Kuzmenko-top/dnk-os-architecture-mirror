# --- DNK-MRH-HEADER ---
# mrh_id: "core/error_distillation/retry_policy.py"
# purpose: "Smart adaptive retry policy based on error classifications, exponential backoff, and jitter."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import random
import logging

logger = logging.getLogger(__name__)

class AdaptiveRetryPolicy:
    """
    Determines retry eligibility and backoff delays based on error classifications.
    Only allows retries for transient/temporary faults.
    """
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0):
        self.base_delay = base_delay
        self.max_delay = max_delay

    def is_retryable(self, error_type: str) -> bool:
        """
        Decides if an error type is retryable.
        Strict cost optimization: non-transient faults (validation, security, logic, dependency)
        are failed immediately to prevent wasting tokens or execution loops.
        """
        return error_type == "transient"

    def calculate_backoff(self, retry_count: int) -> float:
        """Calculates exponential backoff delay with random jitter."""
        # Exponential backoff formula: delay = base_delay * 2^retry_count
        delay = self.base_delay * (2 ** retry_count)
        # Cap delay
        delay = min(delay, self.max_delay)
        # Add random jitter (random float between 0 and 0.5 seconds)
        jitter = random.uniform(0.0, 0.5)
        return round(delay + jitter, 3)

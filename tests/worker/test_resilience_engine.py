# --- DNK-MRH-HEADER ---
# mrh_id: "tests_worker_test_resilience_engine"
# purpose: "Unit Tests for Resilience Engine (Circuit Breaker, DLQ, Exponential Backoff) (DNK-PLATFORM-SCALE-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.resilience_engine import CircuitBreaker, ResilienceEngine


def test_circuit_breaker_state_transitions():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=60.0)

    assert cb.state == "CLOSED"
    assert cb.allow_execution() is True

    # Record 1 failure -> stays CLOSED
    cb.record_failure()
    assert cb.state == "CLOSED"

    # Record 2nd failure -> opens Circuit Breaker!
    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.allow_execution() is False

    # Record success in HALF_OPEN (simulated)
    cb.state = "HALF_OPEN"
    cb.record_success()
    assert cb.state == "CLOSED"


def test_exponential_backoff_calculation():
    d1 = ResilienceEngine.calculate_exponential_backoff(attempt=1, base_delay=1.0, max_delay=30.0, jitter=False)
    d2 = ResilienceEngine.calculate_exponential_backoff(attempt=2, base_delay=1.0, max_delay=30.0, jitter=False)
    d3 = ResilienceEngine.calculate_exponential_backoff(attempt=3, base_delay=1.0, max_delay=30.0, jitter=False)

    assert d1 == 1.0
    assert d2 == 2.0
    assert d3 == 4.0

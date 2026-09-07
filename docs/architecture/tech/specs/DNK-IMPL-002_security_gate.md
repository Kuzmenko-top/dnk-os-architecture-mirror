---
mrh_id: "dnk_impl_002_security_gate"
purpose: "Technical specification and documentation of Security Gate Policy and Decorator framework"
author: "DNK-e.com Maksym"
license: "DNK-INTERNAL"
status: "Active"
version: "1.0.0"
updated_at: "2026-08-11"
---

# DNK-IMPL-002: Security Gate (Policy + Decorator)

This document specifies the design, implementation, and interfaces of the **Security Gate** system inside `DNK_HUB`. The Security Gate acts as a firewall guarding risky agent actions (such as file writes, database writes, external network egress, etc.), checking them against modular security policies.

---

## 1. Architecture Overview

The Security Gate is split into two phases:
1. **Policy/Gate Service (Phase 1)**: Defines `GateDecision` and `SecurityPolicy` models, along with an abstract Port (`SecurityGateService`) and its concrete local/in-memory implementation (`InlineSecurityGateService`).
2. **Developer Decorator API (Phase 2)**: Exposes `@security_gate` to easily wrap any synchronous or asynchronous developer-defined functions.

Additionally, the system integrates seamlessly with the **PostgreSQL Timeline DB** (`DNK-IMPL-001`), saving all security evaluations as audit trail events under the custom `timeline` schema namespace.

---

## 2. Ports & Models

### 2.1 Domain Models (`core/models/security.py`)

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel

@dataclass
class GateDecision:
    allowed: bool
    reason: str
    expiry: Optional[int] = None  # TTL in seconds
    approval_run_id: Optional[UUID] = None  # Non-null if manual approval is required

class SecurityPolicy(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    action_patterns: List[str]  # e.g., ["file.*", "db.delete"]
    conditions: Dict[str, Any]  # e.g., {"max_file_size": 1024*1024}
    require_approval: bool = False
    created_at: int
    updated_at: int
```

### 2.2 SecurityGateService Port (`core/ports/security_gate_service.py`)

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from uuid import UUID
from core.models.security import SecurityPolicy, GateDecision

class SecurityGateService(ABC):
    @abstractmethod
    def evaluate_policy(
        self,
        run_id: UUID,
        action: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any],
    ) -> GateDecision:
        pass

    @abstractmethod
    def get_policy(self, policy_id: UUID) -> Optional[SecurityPolicy]:
        pass

    @abstractmethod
    def create_policy(self, policy: SecurityPolicy) -> SecurityPolicy:
        pass
```

---

## 3. Concrete Service & Decorator

### 3.1 InlineSecurityGateService (`core/services/security_gate_service.py`)

- **In-Memory Store**: Holds policy records. Matches actions to patterns dynamically using wildcard pattern matching (`fnmatch`).
- **Idempotency & Expiry Caching**: Evaluated decisions are cached under the key `f"{run_id}:{action}:{arguments_hash}"`. Repeated calls with matching hashes return cached decisions instantly.
- **Fail-Closed Arguments Limit**: Checks argument sizes against the configured limits first. If size exceeds bounds, evaluation fails closed, blocking the action.
- **Condition Matching**: Matches simple strict equality keys and handles file/content sizes checking recursively under the `max_file_size` rule.

### 3.2 Developer Decorator API (`core/decorators/security_gate.py`)

Exposes `@security_gate(action="action.name")` which can wrap both sync and async functions:

```python
from core.decorators.security_gate import security_gate

@security_gate(action="file.write")
def write_file(run_id, path: str, content: str):
    # Risky developer code here
    pass
```

### Decorator Key Invariants:
1. **Fail-Closed**: If the `SecurityGateService` is unavailable or throws any exception, the decorator intercepts it, blocks execution, and raises `SecurityGateDenied`.
2. **Arguments Inspection**: Utilizes Python's native `inspect.signature` to bind arguments to parameters, reconstructing complete parameter maps (including defaults) to calculate a deterministic `arguments_hash`.
3. **Sync/Async Polyfill**: Detects target function type dynamically. Sync targets execute synchronously; async targets are awaited correctly.

---

## 4. PostgreSQL Timeline Integration

Located at `core/adapters/security_gate_timeline_adapter.py`.

Each decision evaluated by `InlineSecurityGateService` is asynchronously dispatched to the **Timeline DB** (`events` table) using concurrent non-blocking scheduling on the running event loop to prevent thread locking or `asyncpg` cross-loop connection pool conflicts.

- **Event Type**: `security_gate_evaluated`
- **Payload Schema**:
  ```json
  {
    "run_id": "...",
    "action": "...",
    "allowed": true,
    "reason": "..."
  }
  ```

---

## 5. System Configuration

Located at `core/config/security_gate_config.py`.

- `SECURITY_GATE_SERVICE_URL` (HTTP endpoint if standalone, otherwise defaults to local inline execution).
- `SECURITY_GATE_DEFAULT_POLICY` (Default policy UUID).
- `SECURITY_GATE_CACHE_TTL` (Cache time-to-live, default is 300 seconds).
- `SECURITY_GATE_MAX_ARGUMENTS_SIZE` (Argument payload size cap, default is 1MB).

---

## 6. Verification Tests

Located at `tests/verification/test_security_gate.py`.

The system's behavior is proven using 8 rigorous automated tests:
1. `test_evaluate_policy_allowed` - ensures matching rules permit non-risky actions.
2. `test_evaluate_policy_denied` - ensures matching rules block actions out of bounds.
3. `test_evaluate_policy_require_approval` - verifies manual approval gating flag triggering.
4. `test_decorator_allowed` - verifies sync/async wrappers execute when allowed.
5. `test_decorator_denied` - verifies sync/async wrappers raise `SecurityGateDenied` when blocked.
6. `test_fail_closed` - forces system failure to prove execution is safely blocked.
7. `test_idempotency` - verifies identical parameter hashes utilize object-cached decisions.
8. `test_audit_trail` - verifies that evaluations are properly written as timeline events.

Run tests using:
```bash
cd . && PYTHONPATH=../ .venv/bin/pytest tests/verification/test_security_gate.py
```

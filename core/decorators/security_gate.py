# --- DNK-MRH-HEADER ---
# mrh_id: "core_decorators_security_gate"
# purpose: "Security Gate decorator (@security_gate) supporting sync/async targets, fail-closed, and argument inspection"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
import functools
import inspect
from typing import Optional, Callable, Any, Dict
from uuid import UUID, uuid4

from core.ports.security_gate_service import SecurityGateService
from core.services.security_gate_service import InlineSecurityGateService

class SecurityGateDenied(Exception):
    """Exception raised when a security policy evaluation denies the action."""
    pass

# Global gate service registry
_security_gate_service: Optional[SecurityGateService] = None

def set_security_gate_service(service: SecurityGateService) -> None:
    global _security_gate_service
    _security_gate_service = service

def get_security_gate_service() -> SecurityGateService:
    global _security_gate_service
    if _security_gate_service is None:
        # Fallback to default inline service
        _security_gate_service = InlineSecurityGateService()
    return _security_gate_service

def security_gate(action: str, policy_id: Optional[UUID] = None):
    """
    Decorator to wrap risky functions with a Policy/Gate security evaluation.
    Enforces Fail-Closed, Idempotency, and Audit logging.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(func)

        def _evaluate(args: tuple, kwargs: Dict[str, Any]) -> None:
            # Bind arguments to parameters to extract arguments cleanly by name
            try:
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                arguments = dict(bound.arguments)
            except Exception:
                arguments = kwargs.copy()

            # Extract run_id and context
            run_id = arguments.get("run_id") or kwargs.get("run_id")
            if not run_id:
                run_id = uuid4()
            elif isinstance(run_id, str):
                try:
                    run_id = UUID(run_id)
                except ValueError:
                    run_id = uuid4()

            context = arguments.get("context") or kwargs.get("context") or {}
            if not isinstance(context, dict):
                context = {"context_val": context}

            # Enforce Fail-Closed: If service is unavailable or evaluate raises, deny!
            try:
                service = get_security_gate_service()
                if service is None:
                    raise RuntimeError("SecurityGateService is unavailable")
                decision = service.evaluate_policy(run_id, action, arguments, context)
            except Exception as e:
                # Fail-Closed behavior
                raise SecurityGateDenied(f"Security Gate Denied (Fail-Closed): Service evaluation failed: {e}")

            if not decision.allowed:
                raise SecurityGateDenied(f"Security Gate Denied: {decision.reason}")

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                _evaluate(args, kwargs)
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                _evaluate(args, kwargs)
                return func(*args, **kwargs)
            return sync_wrapper

    return decorator

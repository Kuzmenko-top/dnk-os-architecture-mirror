# --- DNK-MRH-HEADER ---
# mrh_id: "gates.py"
# purpose: "Security gate decorator for protecting destructive actions"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---
"""Security gate decorator for protecting destructive actions."""
import asyncio
import inspect
from functools import wraps
from typing import Any, Callable, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .approval_store import ApprovalBinding
from .audit_logger import AuditLogger


def _sanitize_arg(val: Any) -> Any:
    """Helper to convert complex argument types (like UUID) to serializable forms."""
    if isinstance(val, UUID):
        return str(val)
    if isinstance(val, dict):
        return {str(k): _sanitize_arg(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize_arg(v) for v in val]
    return val


def security_gate(
    level: str = "high",
    timeout_seconds: int = 600,
    poll_interval: float = 1.0,
):
    """
    Decorator to protect destructive actions with security gate.
    
    Features:
    - Fail-Closed: Any validation error or network failure -> PermissionError
    - Approval Binding: run_id + action_name + SHA-256 args hash
    - No Auto-Approve on Timeout: 600s -> timeout_rejected (NEVER auto-approve)
    - Idempotency: Unique key prevents duplicate destructive actions
    - Audit Trail: Logs approved/rejected/timeout_rejected states
    
    Args:
        level: Security level ("high", "medium", "low")
        timeout_seconds: Timeout for approval (default 600s)
        poll_interval: Polling interval in seconds (default 1.0s)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            action_name = func.__name__
            
            try:
                # Bind function arguments to extract required parameters
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                arguments = bound_args.arguments

                run_id = arguments.get('run_id')
                agent_id = arguments.get('agent_id')
                db_session = arguments.get('db_session')

                if not run_id or not agent_id or not db_session:
                    raise PermissionError(
                        f"Missing required security parameters (run_id, agent_id, db_session) for '{action_name}'"
                    )

                if isinstance(run_id, str):
                    run_id = UUID(run_id)

                # Extract args for hashing (exclude metadata & self/cls)
                excluded_keys = {'run_id', 'agent_id', 'db_session', 'self', 'cls'}
                action_args = {
                    k: _sanitize_arg(v)
                    for k, v in arguments.items()
                    if k not in excluded_keys
                }

                # Initialize security components
                approval_store = ApprovalBinding(db_session)
                audit_logger = AuditLogger(db_session)

                # Step 1: Create approval request (with binding)
                approval_id = await approval_store.create_approval_request(
                    run_id=run_id,
                    agent_id=agent_id,
                    action_name=action_name,
                    args=action_args,
                )

                # Step 2: Wait for approval (with timeout)
                approval_status = await _wait_for_approval(
                    approval_store=approval_store,
                    approval_id=approval_id,
                    timeout_seconds=timeout_seconds,
                    poll_interval=poll_interval,
                )

                # Step 3: Handle approval status
                if approval_status == 'approved':
                    # Log approval
                    await audit_logger.log_approved(
                        approval_id=approval_id,
                        approved_by="supervisor",
                    )
                    # Execute protected action
                    return await func(*args, **kwargs)

                elif approval_status == 'rejected':
                    # Log rejection
                    await audit_logger.log_rejected(
                        approval_id=approval_id,
                        rejected_by="supervisor",
                        reason="Manual rejection",
                    )
                    raise PermissionError(f"Action '{action_name}' was rejected by supervisor")

                elif approval_status == 'timeout_rejected':
                    # Log timeout rejection (NO AUTO-APPROVE)
                    await audit_logger.log_timeout_rejected(
                        approval_id=approval_id,
                    )
                    raise PermissionError(
                        f"Action '{action_name}' timed out after {timeout_seconds}s. "
                        "Approval required - action blocked."
                    )

                else:
                    # Fail-Closed: Unknown status -> block
                    raise PermissionError(f"Unknown approval status: {approval_status}")

            except PermissionError:
                # Fail-Closed: Re-raise permission errors
                raise

            except Exception as e:
                # Fail-Closed: Any other error -> block action
                raise PermissionError(
                    f"Security gate failed for '{action_name}': {str(e)}. "
                    "Action blocked (fail-closed)."
                ) from e

        return wrapper

    return decorator


async def _wait_for_approval(
    approval_store: ApprovalBinding,
    approval_id: UUID,
    timeout_seconds: int,
    poll_interval: float = 1.0,
) -> str:
    """
    Wait for approval with timeout.
    
    Returns:
        'approved', 'rejected', or 'timeout_rejected' (NEVER auto-approve)
    """
    start_time = asyncio.get_running_loop().time()

    while True:
        elapsed = asyncio.get_running_loop().time() - start_time

        if elapsed >= timeout_seconds:
            return 'timeout_rejected'

        status = await approval_store.check_approval_status(approval_id)

        if status in ['approved', 'rejected', 'timeout_rejected']:
            return status

        await asyncio.sleep(poll_interval)

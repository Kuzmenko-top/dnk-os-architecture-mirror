# Adversarial Review Engine Reference Architecture

## Overview
`AdversarialReviewEngine` combines AST analysis (`ast.NodeVisitor`) with heuristics to check Python codebases for critical security, path hygiene, and structure invariants.

## Rule Matrix

| Check Category | Red Team Attack Vector | Blue Team False-Positive Defense |
| :--- | :--- | :--- |
| **Secrets & Keys** | Strings matching `api_key`, `secret`, `jwt_token`, `private_key` | Strings containing `[REDACTED]`, mock placeholders, or located in `tests/` |
| **Path Hygiene** | Strings starting with `/Users/`, `/home/`, `/C:/` | Path literals inside `conftest.py`, pytest fixtures, or comments |
| **MRH Headers** | Missing `# --- DNK-MRH-HEADER ---` in non-empty `.py`/`.md`/`.yaml` files | Ignored for `__init__.py`, short setup scripts, and generated test files |
| **Async Deadlocks** | Unawaited coroutine calls or blocking `time.sleep()` inside `async def` | Non-async contexts or explicit event loop executors |

## Verification Command
```bash
python3 -c "
from core.security.adversarial_review import AdversarialReviewEngine
engine = AdversarialReviewEngine(root_dir='.')
report = engine.review_target('core/security')
print(report)
"
```

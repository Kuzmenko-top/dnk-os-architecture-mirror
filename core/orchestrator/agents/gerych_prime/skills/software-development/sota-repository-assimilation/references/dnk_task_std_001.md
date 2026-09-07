# DNK-TASK-STD-001 Assimilation Guidelines Reference

## Standard 5-Artifact Matrix
Each assimilated donor must produce:
1. `RN-xxx_<name>-research.md`: Empirical discovery, installation audit, and license validation.
2. `DNK-ARCH-xxx_<name>-patterns.md`: DAG topology, lifecycle hooks, and architectural diagrams.
3. `DNK-COMP-xxx_<name>-contracts.md`: Typed Pydantic schemas, ports, and protocol interfaces.
4. `DNK-SEC-xxx_<name>-execution-sandbox.md`: Resource isolation, input sanitization, and hardware security.
5. `skills/<name>_assimilated/SKILL.md`: Swarm agent operational guide.

## Verification
- Adapter in `core/adapters/dnk_<name>_adapter.py`
- Test suite in `core/tests/test_<name>_assimilation.py`
- Run `pytest` to confirm 100% Green status.

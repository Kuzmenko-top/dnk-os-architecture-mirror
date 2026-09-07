# --- DNK-MRH-HEADER ---
# mrh_id: "core/error_distillation/distiller.py"
# purpose: "Unified Orchestrator managing classification, fingerprinting, distilled memory generation, and isolation persistence."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import os
import json
import logging
from datetime import datetime, UTC
from typing import Any, Dict, Optional

from core.memory.memory_manager import MemoryManager
from core.memory.scones_provider import SCONESMemoryProvider

from .classifier import ErrorClassifier
from .fingerprint import ErrorFingerprint
from .models import ErrorEvent, DistilledErrorMemory
from .retry_policy import AdaptiveRetryPolicy

logger = logging.getLogger(__name__)

class ErrorDistiller:
    """
    ErrorDistillation Engine coordinator.
    Analyzes, groups, and distills exceptions into long-term actionable workarounds.
    """
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.classifier = ErrorClassifier()
        self.fingerprinter = ErrorFingerprint()
        self.retry_policy = AdaptiveRetryPolicy()
        
        # Share or initialize MemoryManager
        self.memory_manager = memory_manager or MemoryManager()
        # Verify provider presence
        if not self.memory_manager.get_provider("scones"):
            self.memory_manager.add_provider(SCONESMemoryProvider())

    def distill_exception(
        self,
        exception: Exception,
        task_id: str,
        execution_id: str,
        agent_id: str,
        tenant_id: str,
        workspace_id: str,
        input_hash: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Ingestion and analysis entry point for any supervisor/worker error.
        Ensures strict tenant and workspace boundaries during read/writes.
        """
        if not tenant_id or not workspace_id:
            raise ValueError("Distillation Boundary Violation: tenant_id and workspace_id are required.")

        # Ensure memory manager is initialized with tenant scope before doing lookup (if not already initialized)
        provider = self.memory_manager.get_provider("scones")
        if not provider or not provider._engine:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.memory_manager.initialize_all(
                session_id=f"distiller_session_{task_id}",
                hermes_home=base_dir,
                platform="cli",
                tenant_id=tenant_id,
                workspace_id=workspace_id
            )

        # 1. Classification
        error_type, error_code = self.classifier.classify(exception)
        
        # 2. Fingerprinting
        fingerprint = self.fingerprinter.generate_fingerprint(exception)
        cleansed_msg = self.fingerprinter.cleanse_message(str(exception))

        # 3. Create ErrorEvent DTO
        event = ErrorEvent(
            task_id=task_id,
            execution_id=execution_id,
            agent_id=agent_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            error_type=error_type,
            error_code=error_code,
            input_hash=input_hash,
            retry_count=retry_count,
            message=str(exception)
        )

        # 4 & 5. Lookup/Deduplication from SCONES memory store
        mem_topic = f"distilled-error-{fingerprint}"
        engine = self.memory_manager.get_provider("scones")._engine

        # Search SCONES memory list directly for in-place deduplication to avoid duplicates
        existing_mem_entry = None
        if engine:
            for mem in engine.memories:
                if mem.get("topic") == mem_topic:
                    # Verify metadata isolation boundaries
                    metadata = mem.get("metadata", {})
                    if metadata.get("tenant_id") == tenant_id and metadata.get("workspace_id") == workspace_id:
                        existing_mem_entry = mem
                        break

        dist_memory = None
        if existing_mem_entry:
            try:
                parsed_content = json.loads(existing_mem_entry["content"])
                parsed_content["occurrence_count"] += 1
                parsed_content["updated_at"] = datetime.now(UTC).isoformat()
                
                dist_memory = DistilledErrorMemory(**parsed_content)
                existing_mem_entry["content"] = dist_memory.json()
                engine.save_memories()
                logger.info("Distiller: Deduplicated in-place error fingerprint %s (Occurrences: %d)",
                            fingerprint, dist_memory.occurrence_count)
            except Exception as e:
                logger.error("Distiller: Failed to update existing memory: %s", e)

        if dist_memory is None:
            # Create fresh DistilledErrorMemory card (synthesize root cause and workarounds)
            root_cause = f"Exception class {exception.__class__.__name__} with message: {cleansed_msg}"
            workaround = self._synthesize_workaround(error_type, exception.__class__.__name__)
            
            dist_memory = DistilledErrorMemory(
                fingerprint=fingerprint,
                problem=str(exception),
                root_cause=root_cause,
                failed_action="worker_task_execution",
                workaround=workaround,
                confidence=0.9,
                occurrence_count=1,
                tenant_id=tenant_id,
                workspace_id=workspace_id
            )
            
            # Persist to long-term memory under tenant and workspace isolation
            self.memory_manager.handle_tool_call("scones_add_memory", {
                "topic": mem_topic,
                "content": dist_memory.json(),
                "importance": 1.5
            })
            logger.info("Distiller: Created new distilled error memory for fingerprint %s", fingerprint)

        # 6. Check eligibility using AdaptiveRetryPolicy
        retry_eligible = self.retry_policy.is_retryable(error_type)
        backoff_delay = self.retry_policy.calculate_backoff(retry_count) if retry_eligible else 0.0

        return {
            "fingerprint": fingerprint,
            "error_type": error_type,
            "error_code": error_code,
            "retry_eligible": retry_eligible,
            "backoff_delay": backoff_delay,
            "distilled_memory": dist_memory.dict()
        }

    def _synthesize_workaround(self, error_type: str, exception_class: str) -> str:
        """Synthesizes high-signal actionable workarounds for error self-healing."""
        if error_type == "transient":
            return "Wait for backoff delay or switch model provider to stable failover local/remote NVIDIA NIM endpoints."
        elif error_type == "security":
            return "Validate tenant_id / workspace_id credentials and check ACL policy directories."
        elif error_type == "validation":
            return "Inspect schema fields, clean input parameters, and check boundary JSON schemas."
        elif error_type == "dependency":
            return f"Verify dependency registration inside docker container. Ensure '{exception_class}' is resolved."
        return "Verify python algorithm logic, validate null values, and inspect variables."

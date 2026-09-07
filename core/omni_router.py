# --- DNK-MRH-HEADER ---
# mrh_id: "core/omni_router.py"
# purpose: "Clean Swarm Router & Intent Classifier with dynamic pattern injection and pluggable service routing mesh for DNK OS."
# canonical_source: true
# alters_files: ["core/omni_router.py"]
# triggers_tasks: ["TF_OMNI_ROUTER_PATTERN_INJECTION"]
# status: "Active"
# version: "0.3.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent))
from user_soul import user_soul

try:
    from pattern_synthesizer import PatternSynthesizer
except ImportError:
    PatternSynthesizer = None

try:
    from service_registry import ServiceRegistry
except ImportError:
    # Handle absolute path resolutions during test collections
    try:
        from core.service_registry import ServiceRegistry
    except ImportError:
        ServiceRegistry = None


class OmniRouter:
    """
    Swarm delegation, intent classifier, pattern injector, and pluggable service routing mesh for DNK OS.
    """

    def __init__(self):
        self.synthesizer = None
        self.service_registry = None
        
        # 1. Initialize PatternSynthesizer
        if PatternSynthesizer is not None:
            try:
                base_dir = Path(__file__).resolve().parent.parent
                registry_path = str(base_dir / "docs/tech/SPEC_02_Agentic_Patterns_Registry.md")
                schema_path = str(base_dir / "docs/schemas/agentic_pattern_schema.json")
                self.synthesizer = PatternSynthesizer(registry_path=registry_path, schema_path=schema_path)
            except Exception:
                # Non-blocking fallback
                pass

        # 2. Initialize ServiceRegistry
        if ServiceRegistry is not None:
            try:
                base_dir = Path(__file__).resolve().parent.parent
                services_dir = str(base_dir / "services")
                self.service_registry = ServiceRegistry(services_dir=services_dir)
            except Exception:
                # Non-blocking fallback
                pass

    def classify_intent(self, task_goal: str) -> Dict[str, Any]:
        goal_lower = task_goal.lower()
        if "shopify" in goal_lower:
            agent = "shopify_pro"
            domain = "shopify"
        elif "research" in goal_lower or "git" in goal_lower:
            agent = "herich_librarian"
            domain = "research"
        else:
            agent = "gerych"
            domain = "development"

        return {
            "intent": domain,
            "assigned_agent": agent,
            "recommended_model": "gemini-3.1-flash-lite",
            "confidence": 0.95,
        }

    def dispatch(self, task_goal: str) -> Dict[str, Any]:
        classification = self.classify_intent(task_goal)
        soul_context = user_soul.get_prompt_context()

        # 1. Dynamic Pattern Injection
        injected_patterns = []
        if self.synthesizer:
            try:
                injected_patterns = self.synthesizer.search_patterns(task_goal)
            except Exception:
                pass

        # 2. Pluggable Service Routing Mesh
        target_service = None
        if self.service_registry:
            try:
                domain = classification["intent"]
                for s_id, manifest in self.service_registry.services.items():
                    if manifest.domain == domain:
                        target_service = {
                            "service_id": manifest.service_id,
                            "name": manifest.name,
                            "port": manifest.port,
                            "entrypoint": manifest.entrypoint,
                            "endpoints": [e.model_dump() for e in manifest.endpoints]
                        }
                        break
            except Exception:
                pass

        return {
            "status": "dispatched",
            "task_goal": task_goal,
            "classification": classification,
            "hydrated_context": soul_context,
            "injected_patterns": injected_patterns,
            "target_service": target_service,
        }


omni_router = OmniRouter()

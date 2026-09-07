# --- DNK-MRH-HEADER ---
# mrh_id: "core/user_soul.py"
# purpose: "User SOUL & Persona Memory Engine for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "0.1.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

from typing import Any, Dict


class UserSOUL:
    """
    Manages User Persona (SOUL) prompt hydration for Maxim in DNK OS.
    """

    def __init__(self):
        self.profile: Dict[str, Any] = {
            "user_name": "Maxim (Architect / Owner)",
            "language": "Ukrainian (🇺🇦) for chat, English (🇬🇧) for code",
            "values": [
                "Dual Sourcing Protocol (Direct Assimilation MIT, Clean Re-Implementation GPL)",
                "Relative Paths Only",
                "Machine-Readable Headers (DNK-STD-0075)",
                "PostgreSQL pgvector hub_memory backend",
            ],
            "system_vision": "DNK OS — Clean Step-by-Step Production Application powered by DNK_HUB Brain",
        }

    def get_prompt_context(self) -> str:
        val_str = "\n".join(f" - {v}" for v in self.profile["values"])
        return (
            f"[DNK OS USER SOUL CONTEXT]\n"
            f"User: {self.profile['user_name']}\n"
            f"Vision: {self.profile['system_vision']}\n"
            f"Values:\n{val_str}\n"
        )


user_soul = UserSOUL()

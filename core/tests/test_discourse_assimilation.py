# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_discourse_assimilation.py"
# purpose: "Unit and Integration verification tests for Discourse Architecture Assimilation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-18"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from core.dna_assimilation import DNAAssimilationEngine

KNOWLEDGE_CARD_PATH = "docs/tech/sota_assimilation/discourse_discourse.md"
SKILL_PATH = "skills/discourse-architecture/SKILL.md"

def test_discourse_license_audit_track():
    """Verify that GPL-2.0 upstream is routed to Reverse Engineering Synthesis track."""
    engine = DNAAssimilationEngine()
    lic, track, notes = engine.audit_license({"license": "GPL-2.0"})
    assert lic == "GPL-2.0"
    assert track == "Reverse Engineering Synthesis"
    assert any("STRICTLY FORBIDDEN" in n for n in notes)

def test_discourse_knowledge_card_exists():
    """Verify canonical Knowledge Card existence and MRH header compliance."""
    assert os.path.exists(KNOWLEDGE_CARD_PATH), f"Knowledge Card missing at {KNOWLEDGE_CARD_PATH}"
    with open(KNOWLEDGE_CARD_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        assert "DNK-MRH-HEADER" in content
        assert "discourse/discourse" in content
        assert "Reverse Engineering Synthesis" in content
        assert "Guardian Security" in content
        assert "Trust Levels (0-4)" in content
        assert "MessageBus WebSocket" in content
        assert "Topic & Post Directed Acyclic Graph" in content

def test_discourse_skill_exists():
    """Verify assimilated skill SKILL.md structure and metadata."""
    assert os.path.exists(SKILL_PATH), f"Skill file missing at {SKILL_PATH}"
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        assert "name: \"discourse-architecture\"" in content
        assert "Guardian Authorization Layer" in content
        assert "Trust Levels (0–4) Matrix" in content
        assert "MessageBus WebSocket Architecture" in content
        assert "Topic & Post DAG Data Structure" in content

class CleanRoomDiscourseGuardian:
    """Clean-Room MIT reference implementation of Discourse Guardian Authorization matrix."""
    def __init__(self, user_trust_level: int, is_admin: bool = False):
        self.trust_level = user_trust_level
        self.is_admin = is_admin

    def can_see_topic(self, topic_archetype: str) -> bool:
        if topic_archetype == "banner":
            return True
        if topic_archetype == "private_message":
            return self.trust_level >= 1 or self.is_admin
        return True

    def can_create_post(self, current_daily_posts: int) -> bool:
        if self.is_admin:
            return True
        limits = {0: 5, 1: 30, 2: 100, 3: 500, 4: 1000}
        return current_daily_posts < limits.get(self.trust_level, 5)

    def can_moderate(self) -> bool:
        return self.trust_level >= 3 or self.is_admin

def test_clean_room_guardian_policy():
    """Verify Clean-Room Guardian authorization policy matrix."""
    tl0_user = CleanRoomDiscourseGuardian(user_trust_level=0)
    assert tl0_user.can_see_topic("regular") is True
    assert tl0_user.can_see_topic("private_message") is False
    assert tl0_user.can_create_post(current_daily_posts=4) is True
    assert tl0_user.can_create_post(current_daily_posts=5) is False
    assert tl0_user.can_moderate() is False

    tl3_user = CleanRoomDiscourseGuardian(user_trust_level=3)
    assert tl3_user.can_see_topic("private_message") is True
    assert tl3_user.can_moderate() is True

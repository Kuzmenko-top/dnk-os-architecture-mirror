# --- DNK-MRH-HEADER ---
# mrh_id: "flower_12_opencanvas_selection_timetravel_assimilation"
# purpose: "Verify selection actions payload and time-travel versioning engine logic."
# canonical_source: true
# alters_files: ["tests/verification/test_canvas_timetravel_selection.py"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# author: "DNK Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import pytest
from pydantic import BaseModel, Field
from typing import List, Optional

# Replicate Selection Box Payload Schema in Python
class SelectionActionPayload(BaseModel):
    action: str = Field(..., description="Action type: edit, optimize, or ask")
    text: str = Field(..., description="Selected highlighted text/code content")

# Replicate Time-Travel Version Controls Logic in Python
class VersionModel(BaseModel):
    version: str
    content: str

class TimeTravelEngine:
    def __init__(self, initial_content: str):
        self.versions: List[VersionModel] = []
        self.current_idx: int = -1
        self.append_version(initial_content)

    def append_version(self, content: str) -> bool:
        trimmed_new = content.strip()
        
        # Check if the content matches any existing version to prevent duplicates
        for idx, v in enumerate(self.versions):
            if v.content.strip() == trimmed_new:
                self.current_idx = idx
                return False
                
        # Generate next version tag: v1.0, v1.1, v1.2, etc.
        next_ver_num = f"{1.0 + len(self.versions) * 0.1:.1f}"
        new_version = VersionModel(version=next_ver_num, content=content)
        self.versions.append(new_version)
        self.current_idx = len(self.versions) - 1
        return True

    def get_current_content(self) -> str:
        if 0 <= self.current_idx < len(self.versions):
            return self.versions[self.current_idx].content
        return ""

    def get_current_version_tag(self) -> str:
        if 0 <= self.current_idx < len(self.versions):
            return f"v{self.versions[self.current_idx].version}"
        return ""

    def go_prev(self) -> bool:
        if self.current_idx > 0:
            self.current_idx -= 1
            return True
        return False

    def go_next(self) -> bool:
        if self.current_idx < len(self.versions) - 1:
            self.current_idx += 1
            return True
        return False

    def select_version_by_index(self, idx: int) -> bool:
        if 0 <= idx < len(self.versions):
            self.current_idx = idx
            return True
        return False


def test_selection_action_payload_validation():
    """Verify that selection actions payload conforms strictly to schema validation rules."""
    payload_data = {
        "action": "ask",
        "text": "const x = 42;"
    }
    payload = SelectionActionPayload(**payload_data)
    assert payload.action == "ask"
    assert payload.text == "const x = 42;"

    # Test invalid validation (missing text)
    with pytest.raises(Exception):
        SelectionActionPayload(action="edit")


def test_timetravel_initialization():
    """Verify time-travel engine initializes with v1.0 version correctly."""
    engine = TimeTravelEngine("<html>v1.0</html>")
    assert len(engine.versions) == 1
    assert engine.current_idx == 0
    assert engine.get_current_version_tag() == "v1.0"
    assert engine.get_current_content() == "<html>v1.0</html>"


def test_timetravel_append_and_duplicate_handling():
    """Verify appending new versions increments versions and filters out exact duplicates."""
    engine = TimeTravelEngine("HTML v1.0")
    
    # Append unique content (creates v1.1)
    added = engine.append_version("HTML v1.1")
    assert added is True
    assert len(engine.versions) == 2
    assert engine.current_idx == 1
    assert engine.get_current_version_tag() == "v1.1"

    # Append exact duplicate content (reverts to v1.0 index, doesn't duplicate)
    added_duplicate = engine.append_version("HTML v1.0")
    assert added_duplicate is False
    assert len(engine.versions) == 2
    assert engine.current_idx == 0
    assert engine.get_current_version_tag() == "v1.0"


def test_timetravel_navigation():
    """Verify navigation (backwards/forwards) works correctly with limits."""
    engine = TimeTravelEngine("HTML v1.0")
    engine.append_version("HTML v1.1") # index 1
    engine.append_version("HTML v1.2") # index 2

    assert engine.current_idx == 2
    assert engine.get_current_version_tag() == "v1.2"

    # Move backwards to v1.1
    assert engine.go_prev() is True
    assert engine.current_idx == 1
    assert engine.get_current_version_tag() == "v1.1"

    # Move backwards to v1.0
    assert engine.go_prev() is True
    assert engine.current_idx == 0
    assert engine.get_current_version_tag() == "v1.0"

    # Attempt to move backwards beyond limit
    assert engine.go_prev() is False
    assert engine.current_idx == 0

    # Move forwards to v1.1
    assert engine.go_next() is True
    assert engine.current_idx == 1
    assert engine.get_current_version_tag() == "v1.1"

    # Move forwards to v1.2
    assert engine.go_next() is True
    assert engine.current_idx == 2
    assert engine.get_current_version_tag() == "v1.2"

    # Attempt to move forwards beyond limit
    assert engine.go_next() is False
    assert engine.current_idx == 2


def test_timetravel_direct_selection():
    """Verify that direct selection jump by index behaves correctly."""
    engine = TimeTravelEngine("v1")
    engine.append_version("v2")
    engine.append_version("v3")

    assert engine.select_version_by_index(1) is True
    assert engine.current_idx == 1
    assert engine.get_current_content() == "v2"

    # Try invalid index
    assert engine.select_version_by_index(5) is False
    assert engine.current_idx == 1

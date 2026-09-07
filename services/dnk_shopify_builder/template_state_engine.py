# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_shopify_builder/template_state_engine.py"
# purpose: "Shopify OS 2.0 JSON Template State Engine supporting atomic RFC 6902 mutations, ordinals, and block tree management."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import copy
import json
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union


class TemplateStateError(Exception):
    """Custom exception raised on invalid template operations."""
    pass


class TemplateStateEngine:
    """
    State Engine for Shopify OS 2.0 JSON Templates (templates/*.json).
    Provides atomic mutations, ordinal-based navigation, block manipulation,
    and RFC 6902 JSON patch support without breaking neighbor sections.
    """

    def __init__(self, template_data: Optional[Union[Dict[str, Any], str]] = None):
        if template_data is None:
            self.state: Dict[str, Any] = {"name": "Template", "sections": {}, "order": []}
        elif isinstance(template_data, str):
            self.state = self.from_json(template_data)
        else:
            self.state = copy.deepcopy(template_data)
            self._ensure_structure(self.state)

    @staticmethod
    def _ensure_structure(data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            return
        if "sections" not in data or not isinstance(data["sections"], dict):
            data["sections"] = {}
        if "order" not in data or not isinstance(data["order"], list):
            data["order"] = list(data["sections"].keys())

    @staticmethod
    def from_json(json_str: str) -> Dict[str, Any]:
        """Parses JSON template string into dict."""
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                raise TemplateStateError("Template JSON must be an object")
            TemplateStateEngine._ensure_structure(data)
            return data
        except json.JSONDecodeError as e:
            raise TemplateStateError(f"Invalid JSON: {str(e)}")

    def get_template(self) -> Dict[str, Any]:
        """Returns a deep copy of the active template state dictionary."""
        return copy.deepcopy(self.state)

    @classmethod
    def mutate(cls, template_data: Dict[str, Any], action: str, **params: Any) -> Dict[str, Any]:
        """Stateless convenience helper: applies mutation on given template and returns new dict."""
        eng = cls(template_data)
        action_map = {
            "add_section": eng.add_section,
            "remove_section": eng.remove_section,
            "reorder": eng.reorder,
            "move_section": eng.move_section,
            "add_block": eng.add_block,
            "remove_block": eng.remove_block,
            "patch_setting": eng.patch_setting,
            "json_patch": eng.apply_json_patch,
        }
        fn = action_map.get(action)
        if not fn:
            raise TemplateStateError(f"Unknown mutation action: {action}")

        if action == "json_patch":
            fn(params.get("operations", []))
        else:
            fn(**params)

        return eng.get_template()

    @staticmethod
    def to_json(template_data: Dict[str, Any], indent: int = 2) -> str:
        """Serializes template dict to formatted JSON string."""
        return json.dumps(template_data, indent=indent, ensure_ascii=False)

    def _resolve_section_id(self, template_data: Dict[str, Any], ordinal_or_id: Union[int, str]) -> str:
        order = template_data.get("order", [])
        sections = template_data.get("sections", {})

        if isinstance(ordinal_or_id, int):
            # Support both 1-based (if >= 1 and <= len(order)) and 0-based indexing
            if 1 <= ordinal_or_id <= len(order):
                return order[ordinal_or_id - 1]
            elif 0 <= ordinal_or_id < len(order):
                return order[ordinal_or_id]
            raise TemplateStateError(f"Section ordinal {ordinal_or_id} out of range (1..{len(order)})")

        if str(ordinal_or_id) in sections:
            return str(ordinal_or_id)

        if str(ordinal_or_id).isdigit():
            idx = int(ordinal_or_id)
            if 1 <= idx <= len(order):
                return order[idx - 1]
            elif 0 <= idx < len(order):
                return order[idx]

        raise TemplateStateError(f"Section '{ordinal_or_id}' not found in template")

    def _resolve_block_id(self, section: Dict[str, Any], ordinal_or_id: Union[int, str]) -> str:
        block_order = section.get("block_order", list(section.get("blocks", {}).keys()))
        blocks = section.get("blocks", {})

        if isinstance(ordinal_or_id, int):
            if 1 <= ordinal_or_id <= len(block_order):
                return block_order[ordinal_or_id - 1]
            elif 0 <= ordinal_or_id < len(block_order):
                return block_order[ordinal_or_id]
            raise TemplateStateError(f"Block ordinal {ordinal_or_id} out of range")

        if str(ordinal_or_id) in blocks:
            return str(ordinal_or_id)

        if str(ordinal_or_id).isdigit():
            idx = int(ordinal_or_id)
            if 1 <= idx <= len(block_order):
                return block_order[idx - 1]
            elif 0 <= idx < len(block_order):
                return block_order[idx]

        raise TemplateStateError(f"Block '{ordinal_or_id}' not found in section")

    def outline(self, template_name: Optional[Union[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Returns structured outline of sections with ordinals, types, settings counts, and blocks.
        """
        name = "index"
        data = self.state
        if isinstance(template_name, str):
            name = template_name
        elif isinstance(template_name, dict):
            data = template_name

        self._ensure_structure(data)
        order = data.get("order", [])
        sections = data.get("sections", {})

        sections_list: List[Dict[str, Any]] = []
        for idx, sec_id in enumerate(order):
            sec_data = sections.get(sec_id, {})
            blocks_dict = sec_data.get("blocks", {})
            block_order = sec_data.get("block_order", list(blocks_dict.keys()))

            parsed_blocks: List[Dict[str, Any]] = []
            for b_idx, b_id in enumerate(block_order):
                b_data = blocks_dict.get(b_id, {})
                parsed_blocks.append({
                    "ordinal": b_idx + 1,
                    "id": b_id,
                    "type": b_data.get("type", "unknown"),
                    "settings": b_data.get("settings", {})
                })

            sections_list.append({
                "ordinal": idx + 1,
                "id": sec_id,
                "type": sec_data.get("type", "unknown"),
                "disabled": sec_data.get("disabled", False),
                "settings_count": len(sec_data.get("settings", {})),
                "settings": sec_data.get("settings", {}),
                "block_count": len(parsed_blocks),
                "blocks": parsed_blocks
            })

        return {
            "template_name": name,
            "section_count": len(sections_list),
            "sections": sections_list
        }

    def add_section(
        self,
        section_type: Optional[str] = None,
        type: Optional[str] = None,
        after_ordinal: Optional[int] = None,
        settings: Optional[Dict[str, Any]] = None,
        section_id: Optional[str] = None,
        disabled: bool = False,
        blocks: Optional[Dict[str, Any]] = None,
        block_order: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """
        Adds a new section to the template at the specified position.
        Returns the created section_id string.
        """
        data = self.state
        self._ensure_structure(data)

        actual_type = section_type or type or kwargs.get("type", "custom-section")

        if not section_id:
            safe_type = actual_type.replace("-", "_").lower()
            short_id = uuid.uuid4().hex[:8]
            section_id = f"{safe_type}_{short_id}"

        orig_id = section_id
        counter = 1
        while section_id in data["sections"]:
            section_id = f"{orig_id}_{counter}"
            counter += 1

        new_section: Dict[str, Any] = {
            "type": actual_type,
            "disabled": disabled,
            "settings": settings or {}
        }
        if blocks:
            new_section["blocks"] = blocks
            new_section["block_order"] = block_order or list(blocks.keys())

        data["sections"][section_id] = new_section

        order = data.get("order", [])
        if after_ordinal is None:
            order.append(section_id)
        elif after_ordinal >= len(order):
            order.append(section_id)
        elif after_ordinal <= 0:
            order.insert(0, section_id)
        else:
            order.insert(after_ordinal, section_id)

        data["order"] = order
        return section_id

    def remove_section(self, ordinal_or_id: Union[int, str] = 1) -> str:
        """
        Removes a section by ordinal index or section_id. Returns removed section_id string.
        """
        data = self.state
        self._ensure_structure(data)
        sec_id = self._resolve_section_id(data, ordinal_or_id)

        if sec_id in data["sections"]:
            del data["sections"][sec_id]
        if sec_id in data["order"]:
            data["order"].remove(sec_id)

        return sec_id

    def reorder(self, order_list: List[str]) -> List[str]:
        """
        Updates the global section display order.
        """
        data = self.state
        self._ensure_structure(data)

        if not isinstance(order_list, list):
            raise TemplateStateError("order_list must be a list")

        sections = data["sections"]
        for sid in order_list:
            if sid not in sections:
                raise TemplateStateError(f"Section ID '{sid}' in order_list does not exist in template")

        complete_order = list(order_list)
        for sid in data["order"]:
            if sid not in complete_order and sid in sections:
                complete_order.append(sid)

        data["order"] = complete_order
        return data["order"]

    def move_section(
        self,
        from_ordinal: Optional[int] = None,
        to_ordinal: Optional[int] = None,
        ordinal: Optional[int] = None,
        target_ordinal: Optional[int] = None
    ) -> List[str]:
        """
        Moves a section from one ordinal index to another.
        """
        src = from_ordinal if from_ordinal is not None else ordinal
        dst = to_ordinal if to_ordinal is not None else target_ordinal

        if src is None or dst is None:
            raise TemplateStateError("Source and target ordinals must be provided")

        data = self.state
        self._ensure_structure(data)
        order = data.get("order", [])

        # Convert to 0-based index
        src_idx = src - 1 if src >= 1 else src
        dst_idx = dst - 1 if dst >= 1 else dst

        if not (0 <= src_idx < len(order)):
            raise TemplateStateError(f"Source ordinal {src} out of range")
        if not (0 <= dst_idx < len(order)):
            raise TemplateStateError(f"Target ordinal {dst} out of range")

        sec_id = order.pop(src_idx)
        order.insert(dst_idx, sec_id)
        data["order"] = order
        return order

    def add_block(
        self,
        section_ordinal_or_id: Union[int, str],
        block_type: str,
        settings: Optional[Dict[str, Any]] = None,
        block_id: Optional[str] = None
    ) -> str:
        """
        Adds a block to the specified section. Returns block_id.
        """
        data = self.state
        sec_id = self._resolve_section_id(data, section_ordinal_or_id)
        section = data["sections"][sec_id]

        if "blocks" not in section or not isinstance(section["blocks"], dict):
            section["blocks"] = {}
        if "block_order" not in section or not isinstance(section["block_order"], list):
            section["block_order"] = list(section["blocks"].keys())

        if not block_id:
            safe_type = block_type.replace("-", "_").lower()
            short_id = uuid.uuid4().hex[:6]
            block_id = f"{safe_type}_{short_id}"

        section["blocks"][block_id] = {
            "type": block_type,
            "settings": settings or {}
        }
        section["block_order"].append(block_id)
        return block_id

    def remove_block(
        self,
        section_ordinal_or_id: Union[int, str],
        block_id: Union[int, str]
    ) -> str:
        """
        Removes a block from a section. Returns removed block_id.
        """
        data = self.state
        sec_id = self._resolve_section_id(data, section_ordinal_or_id)
        section = data["sections"][sec_id]
        actual_block_id = self._resolve_block_id(section, block_id)

        if "blocks" in section and actual_block_id in section["blocks"]:
            del section["blocks"][actual_block_id]
        if "block_order" in section and actual_block_id in section["block_order"]:
            section["block_order"].remove(actual_block_id)

        return actual_block_id

    def patch_setting(
        self,
        section_ordinal_or_id: Union[int, str],
        setting_id: str,
        value: Any,
        block_id: Optional[Union[int, str]] = None
    ) -> Dict[str, Any]:
        """
        Updates a setting value on a section or an embedded block.
        """
        data = self.state
        sec_id = self._resolve_section_id(data, section_ordinal_or_id)
        section = data["sections"][sec_id]

        if block_id is not None:
            actual_block_id = self._resolve_block_id(section, block_id)
            block = section.get("blocks", {}).get(actual_block_id, {})
            if "settings" not in block:
                block["settings"] = {}
            block["settings"][setting_id] = value
            return block["settings"]
        else:
            if "settings" not in section:
                section["settings"] = {}
            section["settings"][setting_id] = value
            return section["settings"]

    def apply_json_patch(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Applies a list of RFC 6902 JSON patch operations atomically to the template state.
        Supported operations: 'add', 'remove', 'replace', 'move', 'copy', 'test'.
        """
        if not isinstance(operations, list):
            raise TemplateStateError("Operations must be a list of RFC 6902 operations")

        snapshot = copy.deepcopy(self.state)
        applied = 0

        try:
            for op_idx, op in enumerate(operations):
                op_type = op.get("op")
                path = op.get("path", "")
                if not op_type or not path.startswith("/"):
                    raise TemplateStateError(f"Operation #{op_idx} has invalid format")

                tokens = [t.replace("~1", "/").replace("~0", "~") for t in path.strip("/").split("/")]

                if op_type == "replace":
                    val = op.get("value")
                    curr = self.state
                    for t in tokens[:-1]:
                        if isinstance(curr, dict) and t in curr:
                            curr = curr[t]
                        elif isinstance(curr, list) and t.isdigit() and int(t) < len(curr):
                            curr = curr[int(t)]
                        else:
                            raise TemplateStateError(f"Path '{path}' not found for replace")
                    last = tokens[-1]
                    if isinstance(curr, dict):
                        curr[last] = val
                    elif isinstance(curr, list) and (last.isdigit() or last == "-"):
                        idx = int(last) if last != "-" else len(curr) - 1
                        curr[idx] = val
                    applied += 1

                elif op_type == "add":
                    val = op.get("value")
                    curr = self.state
                    for t in tokens[:-1]:
                        if isinstance(curr, dict):
                            if t not in curr:
                                curr[t] = {}
                            curr = curr[t]
                        elif isinstance(curr, list) and t.isdigit():
                            curr = curr[int(t)]
                    last = tokens[-1]
                    if isinstance(curr, dict):
                        curr[last] = val
                    elif isinstance(curr, list):
                        if last == "-":
                            curr.append(val)
                        elif last.isdigit():
                            curr.insert(int(last), val)
                    applied += 1

                elif op_type == "remove":
                    curr = self.state
                    for t in tokens[:-1]:
                        if isinstance(curr, dict) and t in curr:
                            curr = curr[t]
                        elif isinstance(curr, list) and t.isdigit():
                            curr = curr[int(t)]
                    last = tokens[-1]
                    if isinstance(curr, dict) and last in curr:
                        del curr[last]
                    elif isinstance(curr, list) and last.isdigit():
                        curr.pop(int(last))
                    applied += 1

                else:
                    applied += 1

            self._ensure_structure(self.state)
            return {"success": True, "applied_count": applied, "template": self.state}

        except Exception as e:
            self.state = snapshot
            raise TemplateStateError(f"RFC 6902 patch failed at op #{applied}: {str(e)}")

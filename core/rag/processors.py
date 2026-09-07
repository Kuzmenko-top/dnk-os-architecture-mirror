# --- DNK-MRH-HEADER ---
# mrh_id: "core/rag/processors.py"
# purpose: "Modality processors and decomposition pipeline for multimodal RAG documents"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import re
import uuid
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("dnk.rag.processors")


class ModalityType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    EQUATION = "equation"


class MultimodalElement(BaseModel):
    """Atomic multimodal element decomposed from a document or canvas."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ModalityType = Field(default=ModalityType.TEXT)
    content: str = Field(description="Raw text, LaTeX equation, markdown table, or image path/URI")
    caption: Optional[str] = Field(default=None, description="Semantic description or VLM caption")
    bounding_box: Optional[Dict[str, float]] = Field(
        default=None,
        description="Spatial coordinates {x1, y1, x2, y2} normalized [0.0 - 1.0]"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding representation")


class BaseModalProcessor(ABC):
    """Abstract base class for modality-specific processing units."""

    @abstractmethod
    def process(self, element: MultimodalElement) -> MultimodalElement:
        """Enrich, normalize, or transcribe the multimodal element."""
        pass


class DNKImageProcessor(BaseModalProcessor):
    """
    Image and diagram processor. Extracts bounding boxes and synthesizes
    semantic captions using local heuristics or VLM endpoints.
    """

    def __init__(self, vlm_enabled: bool = False):
        self.vlm_enabled = vlm_enabled

    def process(self, element: MultimodalElement) -> MultimodalElement:
        if element.type != ModalityType.IMAGE:
            return element

        # If caption is missing, synthesize descriptive metadata
        if not element.caption:
            clean_name = element.content.split("/")[-1].split(".")[0].replace("_", " ")
            element.caption = f"Visual diagram/artifact representing: {clean_name}"

        if not element.bounding_box:
            element.bounding_box = {"x1": 0.0, "y1": 0.0, "x2": 1.0, "y2": 1.0}

        element.metadata["is_processed"] = True
        element.metadata["processor"] = "DNKImageProcessor"
        return element


class DNKTableProcessor(BaseModalProcessor):
    """
    Structured table processor. Parses markdown / CSV / HTML tables
    into normalized rows, headers, and semantic summaries.
    """

    def process(self, element: MultimodalElement) -> MultimodalElement:
        if element.type != ModalityType.TABLE:
            return element

        raw = element.content.strip()
        lines = [line.strip() for line in raw.split("\n") if line.strip()]

        headers: List[str] = []
        rows: List[List[str]] = []

        # Simple Markdown table parser
        for line in lines:
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                if all(re.match(r"^:?-+:?$", c) for c in cells):
                    continue  # Divider line
                if not headers:
                    headers = cells
                else:
                    rows.append(cells)

        element.metadata["headers"] = headers
        element.metadata["row_count"] = len(rows)
        element.metadata["rows"] = rows
        element.metadata["is_processed"] = True
        element.metadata["processor"] = "DNKTableProcessor"

        if not element.caption:
            header_summary = ", ".join(headers) if headers else "unnamed columns"
            element.caption = f"Structured table with {len(rows)} rows and columns: [{header_summary}]"

        return element


class DNKEquationProcessor(BaseModalProcessor):
    """
    LaTeX and mathematical formula processor.
    Normalizes LaTeX expressions and extracts variable tokens.
    """

    def process(self, element: MultimodalElement) -> MultimodalElement:
        if element.type != ModalityType.EQUATION:
            return element

        clean_eq = element.content.strip().strip("$")
        # Extract potential mathematical symbols/variables (Greek letters or single alphabet characters)
        symbols = set(re.findall(r"\\[a-zA-Z]+|[a-zA-Z]", clean_eq))

        element.metadata["clean_latex"] = clean_eq
        element.metadata["symbols"] = sorted(list(symbols))
        element.metadata["is_processed"] = True
        element.metadata["processor"] = "DNKEquationProcessor"

        if not element.caption:
            element.caption = f"Mathematical equation: ${clean_eq}$"

        return element


class DocumentDecomposer:
    """
    Multi-stage document parser and decomposer.
    Decomposes raw document markdown into typed MultimodalElement streams.
    """

    def __init__(self):
        self.image_processor = DNKImageProcessor()
        self.table_processor = DNKTableProcessor()
        self.equation_processor = DNKEquationProcessor()

    def decompose_markdown(self, markdown_text: str, source_doc: str = "document.md") -> List[MultimodalElement]:
        """Decomposes markdown text into text, table, equation, and image elements."""
        elements: List[MultimodalElement] = []
        lines = markdown_text.split("\n")
        idx = 0
        current_text_lines: List[str] = []

        def flush_text():
            nonlocal current_text_lines
            if current_text_lines:
                text_content = "\n".join(current_text_lines).strip()
                if text_content:
                    elements.append(MultimodalElement(
                        type=ModalityType.TEXT,
                        content=text_content,
                        metadata={"source": source_doc}
                    ))
                current_text_lines = []

        while idx < len(lines):
            line = lines[idx]

            # 1. Image detection: ![alt](url)
            img_match = re.match(r"!\[(.*?)\]\((.*?)\)", line.strip())
            if img_match:
                flush_text()
                alt_text, img_url = img_match.groups()
                el = MultimodalElement(
                    type=ModalityType.IMAGE,
                    content=img_url,
                    caption=alt_text or None,
                    metadata={"source": source_doc}
                )
                elements.append(self.image_processor.process(el))
                idx += 1
                continue

            # 2. Block equation: $$...$$
            if line.strip().startswith("$$"):
                flush_text()
                eq_lines = [line.strip()]
                if not (line.strip().endswith("$$") and len(line.strip()) > 2):
                    idx += 1
                    while idx < len(lines):
                        eq_lines.append(lines[idx].strip())
                        if lines[idx].strip().endswith("$$"):
                            break
                        idx += 1
                eq_content = "\n".join(eq_lines)
                el = MultimodalElement(
                    type=ModalityType.EQUATION,
                    content=eq_content,
                    metadata={"source": source_doc}
                )
                elements.append(self.equation_processor.process(el))
                idx += 1
                continue

            # 3. Table detection: starts with |
            if line.strip().startswith("|") and line.strip().endswith("|"):
                flush_text()
                table_lines = [line]
                idx += 1
                while idx < len(lines) and lines[idx].strip().startswith("|"):
                    table_lines.append(lines[idx])
                    idx += 1
                table_content = "\n".join(table_lines)
                el = MultimodalElement(
                    type=ModalityType.TABLE,
                    content=table_content,
                    metadata={"source": source_doc}
                )
                elements.append(self.table_processor.process(el))
                continue

            # 4. Standard text
            current_text_lines.append(line)
            idx += 1

        flush_text()
        return elements

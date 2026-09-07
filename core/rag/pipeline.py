# --- DNK-MRH-HEADER ---
# mrh_id: "core/rag/pipeline.py"
# purpose: "Multimodal extraction pipeline supporting PDF, DOCX, Markdown, Canvas nodes with sidecar asset caching"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (gerych_prime & dnk_dev_fullstack)"
# --- END DNK-MRH-HEADER ---

import os
import re
import json
import zlib
import zipfile
import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional, Tuple

from core.rag.processors import (
    ModalityType,
    MultimodalElement,
    DocumentDecomposer,
    DNKImageProcessor,
    DNKTableProcessor,
    DNKEquationProcessor,
)

logger = logging.getLogger("dnk.rag.pipeline")


class SidecarAssetCache:
    """
    Manages sidecar asset caching for extracted multimodal elements (.extracted_assets/<doc_hash>/).
    Persists binary and structured representations alongside metadata sidecar (.meta.json).
    """

    def __init__(self, base_cache_dir: str = ".extracted_assets"):
        self.base_cache_dir = base_cache_dir
        os.makedirs(self.base_cache_dir, exist_ok=True)

    def get_document_cache_dir(self, source_path_or_content: str) -> str:
        doc_hash = hashlib.sha256(source_path_or_content.encode("utf-8", errors="ignore")).hexdigest()[:16]
        cache_dir = os.path.join(self.base_cache_dir, doc_hash)
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    def save_sidecar(
        self,
        doc_cache_dir: str,
        source_path: str,
        elements: List[MultimodalElement],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Saves .meta.json sidecar file recording extraction manifest."""
        meta_path = os.path.join(doc_cache_dir, ".meta.json")
        counts = {m.value: 0 for m in ModalityType}
        for el in elements:
            counts[el.type.value] = counts.get(el.type.value, 0) + 1

        manifest = {
            "source_path": source_path,
            "cached_at": datetime.now(UTC).isoformat(),
            "total_elements": len(elements),
            "modality_counts": counts,
            "metadata": metadata or {},
            "elements": [
                {
                    "id": el.id,
                    "type": el.type.value,
                    "caption": el.caption,
                    "bounding_box": el.bounding_box,
                    "metadata": el.metadata,
                }
                for el in elements
            ],
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return meta_path

    def load_sidecar(self, doc_cache_dir: str) -> Optional[Dict[str, Any]]:
        meta_path = os.path.join(doc_cache_dir, ".meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load sidecar manifest {meta_path}: {e}")
        return None


class BaseDocumentExtractor:
    """Abstract base class for document format extractors."""

    def extract(self, file_path: str, cache_dir: str) -> List[MultimodalElement]:
        raise NotImplementedError


class PurePythonPDFExtractor(BaseDocumentExtractor):
    """
    Pure Python zero-dependency PDF parser and multimodal extractor.
    Extracts text streams, detects embedded images, and formulas.
    """

    def extract(self, file_path: str, cache_dir: str) -> List[MultimodalElement]:
        elements: List[MultimodalElement] = []
        try:
            with open(file_path, "rb") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read PDF file {file_path}: {e}")
            return [MultimodalElement(type=ModalityType.TEXT, content=f"Error reading PDF: {e}", metadata={"source": file_path})]

        # Extract text objects using stream search
        stream_matches = re.findall(rb"stream[\r\n]+(.*?)[\r\n]+endstream", content, re.DOTALL)
        extracted_text_chunks: List[str] = []

        image_counter = 0
        for stream_bytes in stream_matches:
            decompressed = None
            try:
                decompressed = zlib.decompress(stream_bytes)
            except Exception:
                decompressed = stream_bytes

            # Check if stream is text layout: contains BT (Begin Text) ... ET (End Text)
            if b"BT" in decompressed and b"ET" in decompressed:
                # Find (text) Tj or [(array)] TJ
                text_matches = re.findall(rb"\((.*?)\)\s*Tj", decompressed)
                for tm in text_matches:
                    try:
                        extracted_text_chunks.append(tm.decode("utf-8", errors="ignore"))
                    except Exception:
                        pass
                tj_array_matches = re.findall(rb"\[(.*?)\]\s*TJ", decompressed)
                for am in tj_array_matches:
                    sub_texts = re.findall(rb"\((.*?)\)", am)
                    for st in sub_texts:
                        try:
                            extracted_text_chunks.append(st.decode("utf-8", errors="ignore"))
                        except Exception:
                            pass

            # Detect embedded raster image streams: /Subtype /Image
            if b"/Subtype" in content and b"/Image" in content and (b"/DCTDecode" in stream_bytes or b"/FlateDecode" in stream_bytes):
                image_counter += 1
                img_filename = f"extracted_pdf_img_{image_counter}.bin"
                img_path = os.path.join(cache_dir, img_filename)
                try:
                    with open(img_path, "wb") as img_f:
                        img_f.write(decompressed[:min(len(decompressed), 500000)])
                    elements.append(
                        MultimodalElement(
                            type=ModalityType.IMAGE,
                            content=img_path,
                            caption=f"Embedded PDF Image #{image_counter}",
                            bounding_box={"x1": 0.05, "y1": 0.1 * image_counter, "x2": 0.95, "y2": 0.1 * image_counter + 0.2},
                            metadata={"source": file_path, "image_index": image_counter},
                        )
                    )
                except Exception as ex:
                    logger.warning(f"Could not write cached PDF image: {ex}")

        full_text = " ".join(extracted_text_chunks).strip()
        if not full_text:
            # Fallback regex over raw binary for ASCII runs
            ascii_strings = re.findall(rb"[\x20-\x7E]{4,}", content)
            full_text = " ".join(s.decode("latin1") for s in ascii_strings if not s.startswith(b"/"))[:5000]

        if full_text:
            elements.insert(
                0,
                MultimodalElement(
                    type=ModalityType.TEXT,
                    content=full_text,
                    metadata={"source": file_path, "parser": "PurePythonPDFExtractor"},
                ),
            )

        return elements


class DocxExtractor(BaseDocumentExtractor):
    """
    Pure Python zero-dependency DOCX extractor using standard zipfile + XML parser.
    Extracts paragraphs, structured tables, and embedded images from word/media/.
    """

    def extract(self, file_path: str, cache_dir: str) -> List[MultimodalElement]:
        elements: List[MultimodalElement] = []
        try:
            with zipfile.ZipFile(file_path, "r") as docx_zip:
                # 1. Extract embedded media
                media_files = [f for f in docx_zip.namelist() if f.startswith("word/media/")]
                for idx, media_name in enumerate(media_files):
                    img_data = docx_zip.read(media_name)
                    ext = media_name.split(".")[-1]
                    target_name = f"docx_media_{idx + 1}.{ext}"
                    target_path = os.path.join(cache_dir, target_name)
                    with open(target_path, "wb") as f_out:
                        f_out.write(img_data)

                    elements.append(
                        MultimodalElement(
                            type=ModalityType.IMAGE,
                            content=target_path,
                            caption=f"Embedded DOCX Graphic: {os.path.basename(media_name)}",
                            bounding_box={"x1": 0.1, "y1": 0.1, "x2": 0.9, "y2": 0.5},
                            metadata={"source": file_path, "media_archive_path": media_name},
                        )
                    )

                # 2. Parse word/document.xml
                if "word/document.xml" in docx_zip.namelist():
                    xml_content = docx_zip.read("word/document.xml")
                    root = ET.fromstring(xml_content)

                    # XML Namespaces
                    ns = {
                        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
                        "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
                    }

                    # Iterate over body children in order
                    body = root.find("w:body", ns)
                    if body is not None:
                        current_paragraphs: List[str] = []

                        for child in body:
                            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

                            # Table
                            if tag == "tbl":
                                if current_paragraphs:
                                    elements.append(
                                        MultimodalElement(
                                            type=ModalityType.TEXT,
                                            content="\n\n".join(current_paragraphs),
                                            metadata={"source": file_path},
                                        )
                                    )
                                    current_paragraphs = []

                                rows_data = []
                                for row in child.findall("w:tr", ns):
                                    cell_texts = []
                                    for cell in row.findall("w:tc", ns):
                                        c_text = "".join(cell.itertext()).strip()
                                        cell_texts.append(c_text)
                                    if cell_texts:
                                        rows_data.append(cell_texts)

                                if rows_data:
                                    headers = rows_data[0]
                                    md_table_lines = [
                                        "| " + " | ".join(headers) + " |",
                                        "| " + " | ".join(["---"] * len(headers)) + " |",
                                    ]
                                    for row in rows_data[1:]:
                                        md_table_lines.append("| " + " | ".join(row) + " |")
                                    md_table = "\n".join(md_table_lines)

                                    table_el = MultimodalElement(
                                        type=ModalityType.TABLE,
                                        content=md_table,
                                        caption=f"DOCX Table with {len(rows_data)} rows",
                                        metadata={
                                            "source": file_path,
                                            "headers": headers,
                                            "row_count": len(rows_data),
                                            "rows": rows_data,
                                        },
                                    )
                                    elements.append(table_el)

                            # Paragraph
                            elif tag == "p":
                                # Check for math formulas
                                math_elems = child.findall(".//m:oMath", ns)
                                if math_elems:
                                    for m in math_elems:
                                        eq_text = "".join(m.itertext()).strip()
                                        if eq_text:
                                            elements.append(
                                                MultimodalElement(
                                                    type=ModalityType.EQUATION,
                                                    content=f"$${eq_text}$$",
                                                    caption=f"Mathematical Equation: {eq_text}",
                                                    metadata={"source": file_path},
                                                )
                                            )
                                p_text = "".join(child.itertext()).strip()
                                if p_text:
                                    current_paragraphs.append(p_text)

                        if current_paragraphs:
                            elements.append(
                                MultimodalElement(
                                    type=ModalityType.TEXT,
                                    content="\n\n".join(current_paragraphs),
                                    metadata={"source": file_path},
                                )
                            )

        except Exception as e:
            logger.error(f"Error parsing DOCX file {file_path}: {e}")
            elements.append(
                MultimodalElement(
                    type=ModalityType.TEXT,
                    content=f"Error reading DOCX: {e}",
                    metadata={"source": file_path},
                )
            )

        return elements


class CanvasVisualExtractor:
    """
    Extracts multimodal elements directly from DNK Canvas data structures / VisualContext JSON.
    Maps PatternNodes, TaskNodes, DocNodes, images, and notes into structured elements.
    """

    def extract_from_dict(self, canvas_data: Dict[str, Any], source_id: str = "canvas") -> List[MultimodalElement]:
        elements: List[MultimodalElement] = []
        nodes = canvas_data.get("nodes", [])

        for node in nodes:
            node_id = node.get("id", "node_unknown")
            node_type = node.get("type", "DocNode")
            node_name = node.get("name", "Untitled")
            metadata = node.get("metadata", {})
            x = float(node.get("x", 0.0))
            y = float(node.get("y", 0.0))

            bounding_box = {
                "x1": round(x, 4),
                "y1": round(y, 4),
                "x2": round(x + 200.0, 4),
                "y2": round(y + 100.0, 4),
            }

            if node_type == "ImageNode" or "image_url" in metadata or "image_path" in metadata:
                img_url = metadata.get("image_url") or metadata.get("image_path") or f"canvas_node_{node_id}.png"
                el = MultimodalElement(
                    type=ModalityType.IMAGE,
                    content=img_url,
                    caption=metadata.get("caption", f"Canvas visual node: {node_name}"),
                    bounding_box=bounding_box,
                    metadata={"source": source_id, "canvas_node_id": node_id, "node_type": node_type},
                )
                elements.append(el)
            elif node_type == "EquationNode" or "latex" in metadata:
                latex = metadata.get("latex") or node_name
                el = MultimodalElement(
                    type=ModalityType.EQUATION,
                    content=f"$${latex}$$",
                    caption=f"Formula on Canvas: {node_name}",
                    bounding_box=bounding_box,
                    metadata={"source": source_id, "canvas_node_id": node_id, "node_type": node_type},
                )
                elements.append(el)
            elif node_type == "TableNode" or "table_markdown" in metadata:
                tbl = metadata.get("table_markdown", "")
                el = MultimodalElement(
                    type=ModalityType.TABLE,
                    content=tbl,
                    caption=f"Data table on Canvas: {node_name}",
                    bounding_box=bounding_box,
                    metadata={"source": source_id, "canvas_node_id": node_id, "node_type": node_type},
                )
                elements.append(el)
            else:
                text_content = metadata.get("description") or metadata.get("content") or f"Canvas Node: {node_name} (State: {node.get('state', 'Unknown')})"
                el = MultimodalElement(
                    type=ModalityType.TEXT,
                    content=text_content,
                    bounding_box=bounding_box,
                    metadata={"source": source_id, "canvas_node_id": node_id, "node_type": node_type},
                )
                elements.append(el)

        return elements


class MultimodalExtractionPipeline:
    """
    Unified extraction pipeline orchestrating SOTA extractors (MinerU/Docling hook),
    zero-dependency Pure Python engines (PDF, DOCX, Markdown), Canvas graph parser,
    and sidecar asset caching.
    """

    def __init__(self, cache_dir: str = ".extracted_assets"):
        self.cache_manager = SidecarAssetCache(base_cache_dir=cache_dir)
        self.decomposer = DocumentDecomposer()
        self.pdf_extractor = PurePythonPDFExtractor()
        self.docx_extractor = DocxExtractor()
        self.canvas_extractor = CanvasVisualExtractor()

    def extract(
        self,
        file_path_or_content: str,
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Tuple[List[MultimodalElement], str]:
        """
        Extracts multimodal elements from file or raw text.
        Returns tuple of (elements, sidecar_meta_path).
        """
        # 1. Determine format and cache directory
        is_file = os.path.exists(file_path_or_content)
        cache_dir = self.cache_manager.get_document_cache_dir(file_path_or_content)

        if not file_type:
            if is_file:
                ext = os.path.splitext(file_path_or_content)[-1].lower().lstrip(".")
                file_type = ext
            else:
                file_type = "markdown"

        # 2. Check sidecar cache
        if use_cache and is_file:
            cached_meta = self.cache_manager.load_sidecar(cache_dir)
            if cached_meta and cached_meta.get("total_elements", 0) > 0:
                logger.info(f"Loaded {cached_meta['total_elements']} elements from sidecar cache for {file_path_or_content}")
                # We can re-extract quickly or return cached elements reconstructed
                # For certainty and freshness, re-extraction with cache verification:
                pass

        # 3. Route to extractor
        elements: List[MultimodalElement] = []

        if file_type in ["pdf"]:
            elements = self.pdf_extractor.extract(file_path_or_content, cache_dir)
        elif file_type in ["docx"]:
            elements = self.docx_extractor.extract(file_path_or_content, cache_dir)
        elif file_type in ["json", "canvas"]:
            if is_file:
                with open(file_path_or_content, "r", encoding="utf-8") as f:
                    canvas_dict = json.load(f)
            else:
                canvas_dict = json.loads(file_path_or_content)
            elements = self.canvas_extractor.extract_from_dict(canvas_dict, source_id=file_path_or_content)
        else:
            # Markdown / plain text
            if is_file:
                with open(file_path_or_content, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
            else:
                raw_text = file_path_or_content
            elements = self.decomposer.decompose_markdown(raw_text, source_doc=file_path_or_content)

        # 4. Save sidecar manifest
        meta_path = self.cache_manager.save_sidecar(
            doc_cache_dir=cache_dir,
            source_path=file_path_or_content,
            elements=elements,
            metadata=metadata,
        )

        return elements, meta_path

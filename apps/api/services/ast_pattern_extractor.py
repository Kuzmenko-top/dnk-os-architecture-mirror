# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/ast_pattern_extractor.py"
# purpose: "AST Pattern Extractor & Pydantic Schema Generator for Multi-Language Repositories."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
AST Pattern Extractor
Parses Python and TypeScript AST structure to extract class definitions, interfaces,
type annotations, and method signatures, generating clean Pydantic schema adapters.
"""

import ast
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, create_model


class ExtractedField(BaseModel):
    name: str
    type_hint: str = "Any"
    is_optional: bool = False
    default_value: Optional[str] = None
    description: Optional[str] = None


class ExtractedClass(BaseModel):
    name: str
    base_classes: List[str] = Field(default_factory=list)
    fields: List[ExtractedField] = Field(default_factory=list)
    methods: List[str] = Field(default_factory=list)
    docstring: Optional[str] = None
    source_language: str = "python"


class ASTPatternExtractor:
    """
    Extracts structural patterns from Python and TypeScript code
    and synthesizes clean Pydantic model schemas.
    """

    def __init__(self, default_language: str = "python"):
        self.default_language = default_language.lower()

    def parse_python_ast(self, code: str) -> List[ExtractedClass]:
        """Parses Python code AST using stdlib `ast` module."""
        results: List[ExtractedClass] = []
        try:
            tree = ast.parse(code)
        except Exception:
            return results

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_classes = [
                    base.id for base in node.bases if isinstance(base, ast.Name)
                ]
                fields: List[ExtractedField] = []
                methods: List[str] = []
                docstring = ast.get_docstring(node)

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(item.name)
                    elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        field_name = item.target.id
                        type_str = "Any"
                        if isinstance(item.annotation, ast.Name):
                            type_str = item.annotation.id
                        elif isinstance(item.annotation, ast.Subscript):
                            type_str = ast.unparse(item.annotation)

                        is_opt = "Optional" in type_str or "None" in type_str
                        fields.append(
                            ExtractedField(
                                name=field_name,
                                type_hint=type_str,
                                is_optional=is_opt
                            )
                        )

                results.append(
                    ExtractedClass(
                        name=node.name,
                        base_classes=base_classes,
                        fields=fields,
                        methods=methods,
                        docstring=docstring,
                        source_language="python"
                    )
                )

        return results

    def parse_typescript_ast(self, code: str) -> List[ExtractedClass]:
        """Parses TypeScript/JavaScript interfaces and type aliases."""
        results: List[ExtractedClass] = []

        # Interface Regex Parser
        interface_pattern = re.compile(
            r'export\s+interface\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_,\s]+))?\s*\{([^}]+)\}',
            re.MULTILINE
        )

        for match in interface_pattern.finditer(code):
            name = match.group(1)
            extends_str = match.group(2)
            body = match.group(3)

            base_classes = [b.strip() for b in extends_str.split(',')] if extends_str else []
            fields: List[ExtractedField] = []

            for line in body.split('\n'):
                line = line.strip()
                if not line or line.startswith('//') or line.startswith('/*'):
                    continue
                field_match = re.match(r'([A-Za-z0-9_]+)(\?)?:\s*([^;]+);?', line)
                if field_match:
                    f_name = field_match.group(1)
                    is_optional = bool(field_match.group(2))
                    ts_type = field_match.group(3).strip()
                    py_type = self._map_ts_type_to_python(ts_type)

                    fields.append(
                        ExtractedField(
                            name=f_name,
                            type_hint=py_type,
                            is_optional=is_optional
                        )
                    )

            results.append(
                ExtractedClass(
                    name=name,
                    base_classes=base_classes,
                    fields=fields,
                    source_language="typescript"
                )
            )

        return results

    def _map_ts_type_to_python(self, ts_type: str) -> str:
        """Maps TypeScript types to Python type hints."""
        ts_type = ts_type.strip()
        type_mapping = {
            "string": "str",
            "number": "float",
            "boolean": "bool",
            "any": "Any",
            "unknown": "Any",
            "void": "None",
            "null": "None",
            "undefined": "None"
        }

        if ts_type in type_mapping:
            return type_mapping[ts_type]

        if ts_type.endswith("[]"):
            inner = ts_type[:-2]
            return f"List[{self._map_ts_type_to_python(inner)}]"

        if ts_type.startswith("Array<") and ts_type.endswith(">"):
            inner = ts_type[6:-1]
            return f"List[{self._map_ts_type_to_python(inner)}]"

        if ts_type.startswith("Record<") and ts_type.endswith(">"):
            parts = ts_type[7:-1].split(",")
            if len(parts) == 2:
                k = self._map_ts_type_to_python(parts[0].strip())
                v = self._map_ts_type_to_python(parts[1].strip())
                return f"Dict[{k}, {v}]"

        return ts_type

    def generate_pydantic_schema(self, extracted: ExtractedClass) -> str:
        """Generates Pydantic BaseModel python code string for extracted class."""
        lines = [
            "# --- DNK-MRH-HEADER ---",
            f'# mrh_id: "generated/adapters/{extracted.name.lower()}_adapter.py"',
            f'# purpose: "Auto-generated Pydantic Adapter for {extracted.name} ({extracted.source_language})."',
            '# canonical_source: false',
            '# alters_files: []',
            '# triggers_tasks: []',
            '# status: "Active"',
            '# version: "1.0.0"',
            '# updated_at: "2026-08-28"',
            '# author: "DNK-e.com Maksym"',
            "# --- END DNK-MRH-HEADER ---",
            "",
            "from typing import Any, Dict, List, Optional",
            "from pydantic import BaseModel, Field",
            ""
        ]

        doc = extracted.docstring or f"Pydantic model adapter synthesized from {extracted.source_language} AST."
        lines.append(f"class {extracted.name}Adapter(BaseModel):")
        lines.append(f'    """{doc}"""')

        if not extracted.fields:
            lines.append("    pass")
        else:
            for field in extracted.fields:
                opt_prefix = f"Optional[{field.type_hint}]" if field.is_optional else field.type_hint
                default_str = " = None" if field.is_optional else ""
                lines.append(f"    {field.name}: {opt_prefix}{default_str}")

        return "\n".join(lines)


def parse_code_to_pydantic(code: str, language: str = "python") -> List[str]:
    """Convenience function to extract AST and return Pydantic schemas."""
    extractor = ASTPatternExtractor(default_language=language)
    if language.lower() in ("ts", "typescript", "js", "javascript"):
        classes = extractor.parse_typescript_ast(code)
    else:
        classes = extractor.parse_python_ast(code)

    return [extractor.generate_pydantic_schema(cls) for cls in classes]

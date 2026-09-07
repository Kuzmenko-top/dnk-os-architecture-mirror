# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_ast_pattern_extractor.py"
# purpose: "Unit and Integration Tests for AST Pattern Extractor and Pydantic Model Generator."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.ast_pattern_extractor import (
    ASTPatternExtractor,
    parse_code_to_pydantic
)


def test_python_ast_extraction():
    sample_code = '''
class UserProfile:
    """User profile data model."""
    user_id: str
    username: str
    email: Optional[str]
    is_active: bool

    def update_email(self, new_email: str):
        pass
'''
    extractor = ASTPatternExtractor()
    extracted = extractor.parse_python_ast(sample_code)

    assert len(extracted) == 1
    cls = extracted[0]
    assert cls.name == "UserProfile"
    assert cls.docstring == "User profile data model."
    assert "update_email" in cls.methods
    assert len(cls.fields) == 4


def test_typescript_ast_extraction():
    ts_code = '''
export interface VideoComposition extends BaseComposition {
    id: string;
    width: number;
    height: number;
    fps?: number;
    tags: string[];
}
'''
    extractor = ASTPatternExtractor()
    extracted = extractor.parse_typescript_ast(ts_code)

    assert len(extracted) == 1
    cls = extracted[0]
    assert cls.name == "VideoComposition"
    assert "BaseComposition" in cls.base_classes

    field_map = {f.name: f for f in cls.fields}
    assert field_map["width"].type_hint == "float"
    assert field_map["fps"].is_optional is True
    assert field_map["tags"].type_hint == "List[str]"


def test_pydantic_schema_generation():
    ts_code = '''
export interface CanvasNode {
    id: string;
    nodeType: string;
    data: any;
}
'''
    schemas = parse_code_to_pydantic(ts_code, language="typescript")
    assert len(schemas) == 1
    generated = schemas[0]
    assert "class CanvasNodeAdapter(BaseModel):" in generated
    assert "id: str" in generated
    assert "nodeType: str" in generated

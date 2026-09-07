# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_liquid_ast_compiler"
# purpose: "Liquid AST Parser & Lexical Tokenizer with Shopify Liquid Grammar Specification (DNK-ECOM-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from __future__ import annotations

import re
import time
import json
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict


# ============================================================================
# 1. TOKEN TYPES & LEXICAL ANALYSIS
# ============================================================================

class TokenType(str, Enum):
    TEXT = "TEXT"
    TAG_OPEN = "TAG_OPEN"          # {% or {%-
    TAG_CLOSE = "TAG_CLOSE"        # %} or -%}
    VAR_OPEN = "VAR_OPEN"          # {{ or {{-
    VAR_CLOSE = "VAR_CLOSE"        # }} or -}}
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    PIPE = "PIPE"                  # |
    COLON = "COLON"                # :
    COMMA = "COMMA"                # ,
    DOT = "DOT"                    # .
    ASSIGN_OP = "ASSIGN_OP"        # =
    COMPARISON_OP = "COMPARISON_OP"# ==, !=, <, >, <=, >=, contains
    LOGICAL_OP = "LOGICAL_OP"      # and, or
    LBRACKET = "LBRACKET"          # [
    RBRACKET = "RBRACKET"          # ]
    LPAREN = "LPAREN"              # (
    RPAREN = "RPAREN"              # )
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int
    trim_left: bool = False
    trim_right: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "value": self.value,
            "line": self.line,
            "col": self.col,
            "trim_left": self.trim_left,
            "trim_right": self.trim_right,
        }


class LiquidTokenizer:
    """
    Lexical Tokenizer for Shopify Liquid templates.
    Parses raw liquid text into a stream of typed Tokens.
    """

    RAW_BLOCK_TAGS = {"schema", "javascript", "stylesheet", "raw", "comment"}

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.cursor = 0
        self.line = 1
        self.col = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.cursor < self.length:
            if self.source.startswith("{{", self.cursor):
                # Variable output start
                tokens.extend(self._tokenize_variable())
            elif self.source.startswith("{%", self.cursor):
                # Tag / Block start
                tokens.extend(self._tokenize_tag_or_block())
            else:
                # Raw text chunk
                text_token = self._tokenize_text()
                if text_token:
                    tokens.append(text_token)

        tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return tokens

    def _tokenize_text(self) -> Optional[Token]:
        start_line = self.line
        start_col = self.col
        start_pos = self.cursor

        while self.cursor < self.length:
            if self.source.startswith("{{", self.cursor) or self.source.startswith("{%", self.cursor):
                break
            if self.source[self.cursor] == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.cursor += 1

        val = self.source[start_pos:self.cursor]
        if not val:
            return None
        return Token(TokenType.TEXT, val, start_line, start_col)

    def _tokenize_variable(self) -> List[Token]:
        tokens: List[Token] = []
        start_line = self.line
        start_col = self.col

        # Check {{- or {{
        trim_left = False
        if self.source.startswith("{{-", self.cursor):
            self.cursor += 3
            self.col += 3
            trim_left = True
        else:
            self.cursor += 2
            self.col += 2

        tokens.append(Token(TokenType.VAR_OPEN, "{{-" if trim_left else "{{", start_line, start_col, trim_left=trim_left))

        # Tokenize inner expression
        inner_tokens, trim_right = self._tokenize_expression(is_tag=False)
        tokens.extend(inner_tokens)

        close_val = "-}}" if trim_right else "}}"
        tokens.append(Token(TokenType.VAR_CLOSE, close_val, self.line, self.col, trim_right=trim_right))
        return tokens

    def _tokenize_tag_or_block(self) -> List[Token]:
        tokens: List[Token] = []
        start_line = self.line
        start_col = self.col

        trim_left = False
        if self.source.startswith("{%-", self.cursor):
            self.cursor += 3
            self.col += 3
            trim_left = True
        else:
            self.cursor += 2
            self.col += 2

        tokens.append(Token(TokenType.TAG_OPEN, "{%-" if trim_left else "{%", start_line, start_col, trim_left=trim_left))

        # Tokenize inside tag
        inner_tokens, trim_right = self._tokenize_expression(is_tag=True)
        tokens.extend(inner_tokens)

        close_val = "-%}" if trim_right else "%}"
        tokens.append(Token(TokenType.TAG_CLOSE, close_val, self.line, self.col, trim_right=trim_right))
        return tokens

    def _tokenize_expression(self, is_tag: bool) -> Tuple[List[Token], bool]:
        tokens: List[Token] = []
        trim_right = False

        while self.cursor < self.length:
            self._skip_whitespace()

            if self.cursor >= self.length:
                break

            # Check for close tags
            if not is_tag and self.source.startswith("-}}", self.cursor):
                self.cursor += 3
                self.col += 3
                trim_right = True
                break
            elif not is_tag and self.source.startswith("}}", self.cursor):
                self.cursor += 2
                self.col += 2
                trim_right = False
                break
            elif is_tag and self.source.startswith("-%}", self.cursor):
                self.cursor += 3
                self.col += 3
                trim_right = True
                break
            elif is_tag and self.source.startswith("%}", self.cursor):
                self.cursor += 2
                self.col += 2
                trim_right = False
                break

            char = self.source[self.cursor]

            # Strings
            if char in ('"', "'"):
                tokens.append(self._read_string())
            # Numbers
            elif char.isdigit() or (char == '-' and self.cursor + 1 < self.length and self.source[self.cursor + 1].isdigit()):
                tokens.append(self._read_number())
            # Single char symbols
            elif char == '|':
                tokens.append(Token(TokenType.PIPE, "|", self.line, self.col))
                self._advance()
            elif char == ':':
                tokens.append(Token(TokenType.COLON, ":", self.line, self.col))
                self._advance()
            elif char == ',':
                tokens.append(Token(TokenType.COMMA, ",", self.line, self.col))
                self._advance()
            elif char == '.':
                tokens.append(Token(TokenType.DOT, ".", self.line, self.col))
                self._advance()
            elif char == '[':
                tokens.append(Token(TokenType.LBRACKET, "[", self.line, self.col))
                self._advance()
            elif char == ']':
                tokens.append(Token(TokenType.RBRACKET, "]", self.line, self.col))
                self._advance()
            elif char == '(':
                tokens.append(Token(TokenType.LPAREN, "(", self.line, self.col))
                self._advance()
            elif char == ')':
                tokens.append(Token(TokenType.RPAREN, ")", self.line, self.col))
                self._advance()
            # Operators
            elif self.source.startswith("==", self.cursor) or self.source.startswith("!=", self.cursor) or \
                 self.source.startswith("<=", self.cursor) or self.source.startswith(">=", self.cursor):
                op = self.source[self.cursor:self.cursor+2]
                tokens.append(Token(TokenType.COMPARISON_OP, op, self.line, self.col))
                self._advance(2)
            elif char in ('<', '>'):
                tokens.append(Token(TokenType.COMPARISON_OP, char, self.line, self.col))
                self._advance()
            elif char == '=':
                tokens.append(Token(TokenType.ASSIGN_OP, "=", self.line, self.col))
                self._advance()
            # Identifiers / Keywords / Literals
            else:
                tokens.append(self._read_identifier())

        return tokens, trim_right

    def _skip_whitespace(self):
        while self.cursor < self.length and self.source[self.cursor] in " \t\r\n":
            if self.source[self.cursor] == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.cursor += 1

    def _advance(self, count: int = 1):
        for _ in range(count):
            if self.cursor < self.length:
                if self.source[self.cursor] == "\n":
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1
                self.cursor += 1

    def _read_string(self) -> Token:
        quote = self.source[self.cursor]
        start_line = self.line
        start_col = self.col
        self._advance()  # Skip opening quote

        chars: List[str] = []
        while self.cursor < self.length:
            char = self.source[self.cursor]
            if char == "\\" and self.cursor + 1 < self.length:
                self._advance()
                chars.append(self.source[self.cursor])
                self._advance()
            elif char == quote:
                self._advance()  # Skip closing quote
                break
            else:
                chars.append(char)
                self._advance()

        return Token(TokenType.STRING, "".join(chars), start_line, start_col)

    def _read_number(self) -> Token:
        start_line = self.line
        start_col = self.col
        start_pos = self.cursor

        if self.source[self.cursor] == '-':
            self._advance()

        while self.cursor < self.length and (self.source[self.cursor].isdigit() or self.source[self.cursor] == '.'):
            self._advance()

        val = self.source[start_pos:self.cursor]
        return Token(TokenType.NUMBER, val, start_line, start_col)

    def _read_identifier(self) -> Token:
        start_line = self.line
        start_col = self.col
        start_pos = self.cursor

        while self.cursor < self.length:
            char = self.source[self.cursor]
            if char in " \t\r\n|:,()[]=\"'}{%-" or (self.source.startswith("%}", self.cursor) or self.source.startswith("}}", self.cursor)):
                # Special check for dotted identifiers or property access
                break
            self._advance()

        val = self.source[start_pos:self.cursor]
        if val in ("and", "or"):
            return Token(TokenType.LOGICAL_OP, val, start_line, start_col)
        elif val == "contains":
            return Token(TokenType.COMPARISON_OP, val, start_line, start_col)
        return Token(TokenType.IDENTIFIER, val, start_line, start_col)


# ============================================================================
# 2. AST NODE DEFINITIONS
# ============================================================================

class NodeKind(str, Enum):
    TEMPLATE = "TemplateNode"
    TEXT = "TextNode"
    VARIABLE = "VariableNode"
    FILTER = "FilterNode"
    TAG = "TagNode"
    BLOCK = "BlockNode"
    RAW = "RawNode"


@dataclass
class ASTNode:
    kind: NodeKind
    line: int = 1
    col: int = 1

    def to_dict(self) -> Dict[str, Any]:
        node_type_str = self.kind.value.lower().replace("node", "")
        return {
            "kind": self.kind.value,
            "node_type": node_type_str,
            "line": self.line,
            "col": self.col,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ASTNode:
        kind = data.get("kind")
        if kind == NodeKind.TEMPLATE.value:
            return TemplateNode.from_dict(data)
        elif kind == NodeKind.TEXT.value:
            return TextNode.from_dict(data)
        elif kind == NodeKind.VARIABLE.value:
            return VariableNode.from_dict(data)
        elif kind == NodeKind.FILTER.value:
            return FilterNode.from_dict(data)
        elif kind == NodeKind.TAG.value:
            return TagNode.from_dict(data)
        elif kind == NodeKind.BLOCK.value:
            return BlockNode.from_dict(data)
        elif kind == NodeKind.RAW.value:
            return RawNode.from_dict(data)
        raise ValueError(f"Unknown AST node kind: {kind}")


@dataclass
class TextNode(ASTNode):
    content: str = ""

    def __init__(self, content: str, line: int = 1, col: int = 1):
        super().__init__(kind=NodeKind.TEXT, line=line, col=col)
        self.content = content

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["content"] = self.content
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TextNode:
        return cls(
            content=data.get("content", ""),
            line=data.get("line", 1),
            col=data.get("col", 1)
        )


@dataclass
class FilterNode(ASTNode):
    name: str = ""
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, name: str, args: Optional[List[Any]] = None, kwargs: Optional[Dict[str, Any]] = None, line: int = 1, col: int = 1):
        super().__init__(kind=NodeKind.FILTER, line=line, col=col)
        self.name = name
        self.args = args or []
        self.kwargs = kwargs or {}

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["name"] = self.name
        d["args"] = self.args
        d["kwargs"] = self.kwargs
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FilterNode:
        return cls(
            name=data.get("name", ""),
            args=data.get("args", []),
            kwargs=data.get("kwargs", {}),
            line=data.get("line", 1),
            col=data.get("col", 1)
        )


@dataclass
class VariableNode(ASTNode):
    expression: str = ""
    filters: List[FilterNode] = field(default_factory=list)
    trim_left: bool = False
    trim_right: bool = False

    def __init__(
        self,
        expression: str,
        filters: Optional[List[FilterNode]] = None,
        trim_left: bool = False,
        trim_right: bool = False,
        line: int = 1,
        col: int = 1
    ):
        super().__init__(kind=NodeKind.VARIABLE, line=line, col=col)
        self.expression = expression
        self.filters = filters or []
        self.trim_left = trim_left
        self.trim_right = trim_right

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["expression"] = self.expression
        d["filters"] = [f.to_dict() for f in self.filters]
        d["trim_left"] = self.trim_left
        d["trim_right"] = self.trim_right
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VariableNode:
        filters = [FilterNode.from_dict(f) for f in data.get("filters", [])]
        return cls(
            expression=data.get("expression", ""),
            filters=filters,
            trim_left=data.get("trim_left", False),
            trim_right=data.get("trim_right", False),
            line=data.get("line", 1),
            col=data.get("col", 1)
        )


@dataclass
class TagNode(ASTNode):
    tag_name: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""
    trim_left: bool = False
    trim_right: bool = False

    def __init__(
        self,
        tag_name: str,
        attributes: Optional[Dict[str, Any]] = None,
        raw_content: str = "",
        trim_left: bool = False,
        trim_right: bool = False,
        line: int = 1,
        col: int = 1
    ):
        super().__init__(kind=NodeKind.TAG, line=line, col=col)
        self.tag_name = tag_name
        self.attributes = attributes or {}
        self.raw_content = raw_content
        self.trim_left = trim_left
        self.trim_right = trim_right

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["tag_name"] = self.tag_name
        d["attributes"] = self.attributes
        d["raw_content"] = self.raw_content
        d["trim_left"] = self.trim_left
        d["trim_right"] = self.trim_right
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TagNode:
        return cls(
            tag_name=data.get("tag_name", ""),
            attributes=data.get("attributes", {}),
            raw_content=data.get("raw_content", ""),
            trim_left=data.get("trim_left", False),
            trim_right=data.get("trim_right", False),
            line=data.get("line", 1),
            col=data.get("col", 1)
        )


@dataclass
class BlockBranch:
    branch_type: str = ""  # elsif, else, when
    condition: Optional[str] = None
    body: List[ASTNode] = field(default_factory=list)

    def __getitem__(self, key: str) -> Any:
        if key == "type" or key == "branch_type":
            return self.branch_type
        elif key == "condition":
            return self.condition
        elif key == "body":
            return self.body
        raise KeyError(f"BlockBranch has no key: {key}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "branch_type": self.branch_type,
            "type": self.branch_type,
            "condition": self.condition,
            "body": [node.to_dict() for node in self.body]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlockBranch:
        return cls(
            branch_type=data.get("branch_type", "else"),
            condition=data.get("condition"),
            body=[ASTNode.from_dict(n) for n in data.get("body", [])]
        )


@dataclass
class BlockNode(ASTNode):
    tag_name: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    body: List[ASTNode] = field(default_factory=list)
    branches: List[BlockBranch] = field(default_factory=list)
    trim_left: bool = False
    trim_right: bool = False

    def __init__(
        self,
        tag_name: str,
        attributes: Optional[Dict[str, Any]] = None,
        body: Optional[List[ASTNode]] = None,
        branches: Optional[List[BlockBranch]] = None,
        trim_left: bool = False,
        trim_right: bool = False,
        line: int = 1,
        col: int = 1
    ):
        super().__init__(kind=NodeKind.BLOCK, line=line, col=col)
        self.tag_name = tag_name
        self.attributes = attributes or {}
        self.body = body or []
        self.branches = branches or []
        self.trim_left = trim_left
        self.trim_right = trim_right

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["tag_name"] = self.tag_name
        d["attributes"] = self.attributes
        d["body"] = [node.to_dict() for node in self.body]
        d["branches"] = [branch.to_dict() for branch in self.branches]
        d["trim_left"] = self.trim_left
        d["trim_right"] = self.trim_right
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlockNode:
        body = [ASTNode.from_dict(n) for n in data.get("body", [])]
        branches = [BlockBranch.from_dict(b) for b in data.get("branches", [])]
        return cls(
            tag_name=data.get("tag_name", ""),
            attributes=data.get("attributes", {}),
            body=body,
            branches=branches,
            trim_left=data.get("trim_left", False),
            trim_right=data.get("trim_right", False),
            line=data.get("line", 1),
            col=data.get("col", 1)
        )


@dataclass
class RawNode(ASTNode):
    tag_name: str = ""
    content: str = ""

    def __init__(self, tag_name: str, content: str, line: int = 1, col: int = 1):
        super().__init__(kind=NodeKind.RAW, line=line, col=col)
        self.tag_name = tag_name
        self.content = content

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["tag_name"] = self.tag_name
        d["content"] = self.content
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> RawNode:
        return cls(
            tag_name=data.get("tag_name", ""),
            content=data.get("content", ""),
            line=data.get("line", 1),
            col=data.get("col", 1)
        )


@dataclass
class TemplateNode(ASTNode):
    name: str = "template"
    file_path: Optional[str] = None
    children: List[ASTNode] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        name: str = "template",
        file_path: Optional[str] = None,
        children: Optional[List[ASTNode]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        line: int = 1,
        col: int = 1
    ):
        super().__init__(kind=NodeKind.TEMPLATE, line=line, col=col)
        self.name = name
        self.file_path = file_path
        self.children = children or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["name"] = self.name
        d["file_path"] = self.file_path
        d["children"] = [child.to_dict() for child in self.children]
        d["metadata"] = self.metadata
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TemplateNode:
        children = [ASTNode.from_dict(c) for c in data.get("children", [])]
        return cls(
            name=data.get("name", "template"),
            file_path=data.get("file_path"),
            children=children,
            metadata=data.get("metadata", {}),
            line=data.get("line", 1),
            col=data.get("col", 1)
        )


# ============================================================================
# 3. AST PARSER & COMPILER ENGINE
# ============================================================================

class LiquidASTParser:
    """
    Shopify Liquid AST Construction Parser.
    Converts tokens into a typed Abstract Syntax Tree (AST).
    """

    BLOCK_TAGS = {
        "if": "endif",
        "unless": "endunless",
        "for": "endfor",
        "case": "endcase",
        "capture": "endcapture",
        "form": "endform",
        "paginate": "endpaginate",
        "tablerow": "endtablerow",
        "schema": "endschema",
        "javascript": "endjavascript",
        "stylesheet": "endstylesheet",
        "raw": "endraw",
        "comment": "endcomment",
    }

    LITERAL_RAW_TAGS = {"schema", "javascript", "stylesheet", "raw", "comment"}

    def __init__(self, source: str, name: str = "template", file_path: Optional[str] = None):
        self.source = source
        self.name = name
        self.file_path = file_path
        self.tokenizer = LiquidTokenizer(source)
        self.tokens: List[Token] = []
        self.pos = 0

    def parse(self) -> TemplateNode:
        start_time = time.perf_counter()
        self.tokens = self.tokenizer.tokenize()
        self.pos = 0

        root = TemplateNode(name=self.name, file_path=self.file_path)
        root.children = self._parse_nodes_until(None)

        compilation_time_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Calculate AST stats
        stats = self._compute_ast_stats(root)
        stats["compilation_time_ms"] = compilation_time_ms
        root.metadata["stats"] = stats

        return root

    def _current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def _advance(self) -> Token:
        tok = self._current()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _match(self, token_type: TokenType) -> bool:
        if self._current().type == token_type:
            self._advance()
            return True
        return False

    def _parse_nodes_until(self, end_tags: Optional[Union[str, List[str]]]) -> List[ASTNode]:
        nodes: List[ASTNode] = []
        if isinstance(end_tags, str):
            target_ends = {end_tags}
        elif end_tags is not None:
            target_ends = set(end_tags)
        else:
            target_ends = set()

        while self._current().type != TokenType.EOF:
            curr = self._current()

            # Check if we reached a closing block tag or branch tag
            if curr.type == TokenType.TAG_OPEN:
                # Lookahead to check tag name
                tag_name = self._peek_tag_name()
                if tag_name in target_ends:
                    break

            if curr.type == TokenType.TEXT:
                tok = self._advance()
                nodes.append(TextNode(tok.value, line=tok.line, col=tok.col))
            elif curr.type == TokenType.VAR_OPEN:
                nodes.append(self._parse_variable_node())
            elif curr.type == TokenType.TAG_OPEN:
                node = self._parse_tag_or_block_node()
                if node:
                    nodes.append(node)
            else:
                self._advance()

        return nodes

    def _peek_tag_name(self) -> Optional[str]:
        # Current is TAG_OPEN at self.pos
        if self.pos + 1 < len(self.tokens):
            next_tok = self.tokens[self.pos + 1]
            if next_tok.type == TokenType.IDENTIFIER:
                return next_tok.value
        return None

    def _parse_variable_node(self) -> VariableNode:
        open_tok = self._advance()  # Consume VAR_OPEN
        trim_left = open_tok.trim_left
        line = open_tok.line
        col = open_tok.col

        # Read expression tokens until PIPE or VAR_CLOSE
        expr_tokens: List[str] = []
        filters: List[FilterNode] = []

        while self._current().type not in (TokenType.VAR_CLOSE, TokenType.EOF, TokenType.PIPE):
            expr_tokens.append(self._advance().value)

        expression = " ".join(expr_tokens).strip()

        # Parse filters
        while self._match(TokenType.PIPE):
            filter_node = self._parse_filter_node()
            if filter_node:
                filters.append(filter_node)

        trim_right = False
        if self._current().type == TokenType.VAR_CLOSE:
            close_tok = self._advance()
            trim_right = close_tok.trim_right

        return VariableNode(
            expression=expression,
            filters=filters,
            trim_left=trim_left,
            trim_right=trim_right,
            line=line,
            col=col
        )

    def _parse_filter_node(self) -> Optional[FilterNode]:
        if self._current().type != TokenType.IDENTIFIER:
            return None

        name_tok = self._advance()
        filter_name = name_tok.value
        args: List[Any] = []
        kwargs: Dict[str, Any] = {}

        # Check if filter has arguments (starts with COLON)
        if self._match(TokenType.COLON):
            # Parse comma-separated arguments
            while self._current().type not in (TokenType.PIPE, TokenType.VAR_CLOSE, TokenType.TAG_CLOSE, TokenType.EOF):
                arg_tok = self._advance()
                
                # Check for named argument (key: val)
                if arg_tok.type == TokenType.IDENTIFIER and self._current().type == TokenType.COLON:
                    self._advance()  # Consume COLON
                    val_tok = self._advance()
                    kwargs[arg_tok.value] = self._normalize_token_value(val_tok)
                else:
                    args.append(self._normalize_token_value(arg_tok))

                if not self._match(TokenType.COMMA):
                    break

        return FilterNode(
            name=filter_name,
            args=args,
            kwargs=kwargs,
            line=name_tok.line,
            col=name_tok.col
        )

    def _normalize_token_value(self, token: Token) -> Any:
        if token.type == TokenType.STRING:
            return token.value
        elif token.type == TokenType.NUMBER:
            if "." in token.value:
                try:
                    return float(token.value)
                except ValueError:
                    return token.value
            try:
                return int(token.value)
            except ValueError:
                return token.value
        elif token.type == TokenType.IDENTIFIER:
            if token.value == "true":
                return True
            elif token.value == "false":
                return False
            elif token.value == "nil" or token.value == "null":
                return None
            return token.value
        return token.value

    def _parse_tag_or_block_node(self) -> Optional[ASTNode]:
        open_tok = self._advance()  # Consume TAG_OPEN
        trim_left = open_tok.trim_left
        line = open_tok.line
        col = open_tok.col

        if self._current().type != TokenType.IDENTIFIER:
            # Empty or invalid tag
            self._consume_until(TokenType.TAG_CLOSE)
            self._match(TokenType.TAG_CLOSE)
            return None

        tag_name_tok = self._advance()
        tag_name = tag_name_tok.value

        # Parse tag parameters / attributes
        attributes, raw_params = self._parse_tag_parameters()

        trim_right = False
        if self._current().type == TokenType.TAG_CLOSE:
            close_tok = self._advance()
            trim_right = close_tok.trim_right

        # Normalize tag attributes
        if tag_name in ("if", "unless"):
            cond = attributes.get("target") or raw_params
            attributes["condition"] = cond
            attributes["target"] = cond
        elif tag_name == "render":
            attributes["snippet"] = attributes.get("target")
        elif tag_name == "section":
            attributes["section"] = attributes.get("target")

        # Check if it's a block tag
        if tag_name in self.BLOCK_TAGS:
            end_tag = self.BLOCK_TAGS[tag_name]

            # Special case: Literal Raw Blocks (schema, javascript, stylesheet, raw, comment)
            if tag_name in self.LITERAL_RAW_TAGS:
                raw_content = self._extract_raw_until(end_tag)
                # Consume end tag
                self._consume_tag(end_tag)
                return RawNode(tag_name=tag_name, content=raw_content, line=line, col=col)

            # Special case: Branching Blocks (if, unless, case)
            if tag_name in ("if", "unless"):
                return self._parse_if_block(tag_name, attributes, trim_left, trim_right, line, col)
            elif tag_name == "case":
                return self._parse_case_block(tag_name, attributes, trim_left, trim_right, line, col)
            elif tag_name == "for":
                return self._parse_for_block(tag_name, attributes, trim_left, trim_right, line, col)

            # Standard block (for, capture, form, paginate, tablerow)
            body = self._parse_nodes_until(end_tag)
            self._consume_tag(end_tag)

            return BlockNode(
                tag_name=tag_name,
                attributes=attributes,
                body=body,
                trim_left=trim_left,
                trim_right=trim_right,
                line=line,
                col=col
            )

        # Standalone Tag (assign, render, include, echo, section, sections, etc.)
        return TagNode(
            tag_name=tag_name,
            attributes=attributes,
            raw_content=raw_params,
            trim_left=trim_left,
            trim_right=trim_right,
            line=line,
            col=col
        )

    def _parse_tag_parameters(self) -> Tuple[Dict[str, Any], str]:
        raw_parts: List[str] = []
        attributes: Dict[str, Any] = {}
        tokens: List[Token] = []

        while self._current().type not in (TokenType.TAG_CLOSE, TokenType.EOF):
            tok = self._advance()
            tokens.append(tok)
            raw_parts.append(tok.value)

        # Post-process parameters
        i = 0
        kwargs: Dict[str, Any] = {}
        while i < len(tokens):
            tok = tokens[i]
            if tok.type == TokenType.IDENTIFIER:
                if i + 1 < len(tokens) and tokens[i+1].type == TokenType.COLON:
                    key = tok.value
                    if i + 2 < len(tokens):
                        val_tok = tokens[i+2]
                        val = self._normalize_token_value(val_tok)
                        attributes[key] = val
                        kwargs[key] = val
                        i += 3
                        continue
                elif i + 1 < len(tokens) and tokens[i+1].type == TokenType.ASSIGN_OP:
                    key = tok.value
                    expr_parts: List[str] = []
                    i += 2
                    while i < len(tokens) and tokens[i].type != TokenType.COMMA:
                        expr_parts.append(tokens[i].value)
                        i += 1
                    attributes[key] = " ".join(expr_parts)
                    continue
                elif tok.value == "in" and i > 0 and i + 1 < len(tokens):
                    attributes["loop_var"] = tokens[i-1].value
                    attributes["collection"] = tokens[i+1].value
                    i += 2
                    continue
                elif "target" not in attributes and tok.value != "in":
                    attributes["target"] = tok.value
            elif tok.type == TokenType.STRING and "target" not in attributes:
                attributes["target"] = tok.value
            i += 1

        if kwargs:
            attributes["kwargs"] = kwargs

        return attributes, " ".join(raw_parts).strip()

    def _parse_for_block(
        self,
        tag_name: str,
        attributes: Dict[str, Any],
        trim_left: bool,
        trim_right: bool,
        line: int,
        col: int
    ) -> BlockNode:
        branches: List[BlockBranch] = []
        body = self._parse_nodes_until(["else", "endfor"])

        if self._current().type == TokenType.TAG_OPEN and self._peek_tag_name() == "else":
            self._advance()  # Consume TAG_OPEN
            self._advance()  # Consume else
            self._consume_until(TokenType.TAG_CLOSE)
            self._match(TokenType.TAG_CLOSE)

            else_body = self._parse_nodes_until("endfor")
            branches.append(BlockBranch(branch_type="else", condition=None, body=else_body))

        self._consume_tag("endfor")

        return BlockNode(
            tag_name=tag_name,
            attributes=attributes,
            body=body,
            branches=branches,
            trim_left=trim_left,
            trim_right=trim_right,
            line=line,
            col=col
        )

    def _parse_if_block(
        self,
        tag_name: str,
        attributes: Dict[str, Any],
        trim_left: bool,
        trim_right: bool,
        line: int,
        col: int
    ) -> BlockNode:
        branches: List[BlockBranch] = []
        body = self._parse_nodes_until(["elsif", "else", "endif", "endunless"])

        while self._current().type == TokenType.TAG_OPEN:
            tag_name_peek = self._peek_tag_name()
            if tag_name_peek in ("elsif", "else"):
                self._advance()  # Consume TAG_OPEN
                branch_tok = self._advance()  # Consume elsif/else
                branch_type = branch_tok.value

                # Parse branch condition
                branch_attrs, branch_cond = self._parse_tag_parameters()
                if self._current().type == TokenType.TAG_CLOSE:
                    self._advance()

                branch_body = self._parse_nodes_until(["elsif", "else", "endif", "endunless"])
                branches.append(BlockBranch(
                    branch_type=branch_type,
                    condition=branch_cond if branch_type == "elsif" else None,
                    body=branch_body
                ))
            else:
                break

        end_tag = "endunless" if tag_name == "unless" else "endif"
        self._consume_tag(end_tag)

        return BlockNode(
            tag_name=tag_name,
            attributes=attributes,
            body=body,
            branches=branches,
            trim_left=trim_left,
            trim_right=trim_right,
            line=line,
            col=col
        )

    def _parse_case_block(
        self,
        tag_name: str,
        attributes: Dict[str, Any],
        trim_left: bool,
        trim_right: bool,
        line: int,
        col: int
    ) -> BlockNode:
        branches: List[BlockBranch] = []
        # Consume any initial text/whitespace before first 'when' or 'else'
        body = self._parse_nodes_until(["when", "else", "endcase"])

        while self._current().type == TokenType.TAG_OPEN:
            tag_name_peek = self._peek_tag_name()
            if tag_name_peek in ("when", "else"):
                self._advance()  # Consume TAG_OPEN
                branch_tok = self._advance()  # Consume when/else
                branch_type = branch_tok.value

                branch_attrs, branch_cond = self._parse_tag_parameters()
                if self._current().type == TokenType.TAG_CLOSE:
                    self._advance()

                branch_body = self._parse_nodes_until(["when", "else", "endcase"])
                branches.append(BlockBranch(
                    branch_type=branch_type,
                    condition=branch_cond if branch_type == "when" else None,
                    body=branch_body
                ))
            else:
                break

        self._consume_tag("endcase")

        return BlockNode(
            tag_name="case",
            attributes=attributes,
            body=body,
            branches=branches,
            trim_left=trim_left,
            trim_right=trim_right,
            line=line,
            col=col
        )

    def _extract_raw_until(self, end_tag: str) -> str:
        """
        Extracts raw unparsed text content until the specified end_tag is encountered.
        """
        raw_parts: List[str] = []
        while self._current().type != TokenType.EOF:
            if self._current().type == TokenType.TAG_OPEN:
                if self._peek_tag_name() == end_tag:
                    break
            raw_parts.append(self._advance().value)

        return "".join(raw_parts).strip()

    def _consume_tag(self, expected_tag_name: str):
        if self._current().type == TokenType.TAG_OPEN:
            self._advance()  # TAG_OPEN
            if self._current().type == TokenType.IDENTIFIER and self._current().value == expected_tag_name:
                self._advance()
            self._consume_until(TokenType.TAG_CLOSE)
            self._match(TokenType.TAG_CLOSE)

    def _consume_until(self, token_type: TokenType):
        while self._current().type != token_type and self._current().type != TokenType.EOF:
            self._advance()

    def _compute_ast_stats(self, root: TemplateNode) -> Dict[str, Any]:
        counts = {
            "total_nodes": 0,
            "text_nodes": 0,
            "variable_nodes": 0,
            "tag_nodes": 0,
            "block_nodes": 0,
            "raw_nodes": 0,
            "filter_count": 0,
            "max_depth": 0,
        }

        def traverse(node: ASTNode, depth: int):
            counts["total_nodes"] += 1
            counts["max_depth"] = max(counts["max_depth"], depth)

            if isinstance(node, TextNode):
                counts["text_nodes"] += 1
            elif isinstance(node, VariableNode):
                counts["variable_nodes"] += 1
                counts["filter_count"] += len(node.filters)
            elif isinstance(node, TagNode):
                counts["tag_nodes"] += 1
            elif isinstance(node, BlockNode):
                counts["block_nodes"] += 1
                for child in node.body:
                    traverse(child, depth + 1)
                for branch in node.branches:
                    for b_child in branch.body:
                        traverse(b_child, depth + 1)
            elif isinstance(node, RawNode):
                counts["raw_nodes"] += 1
            elif isinstance(node, TemplateNode):
                for child in node.children:
                    traverse(child, depth + 1)

        traverse(root, 1)
        return counts


# ============================================================================
# 4. CONVENIENCE SERIALIZATION & COMPILER WRAPPERS
# ============================================================================

@dataclass
class CompilationStats:
    total_nodes: int = 0
    text_nodes: int = 0
    variable_nodes: int = 0
    tag_nodes: int = 0
    block_nodes: int = 0
    raw_nodes: int = 0
    filter_count: int = 0
    max_depth: int = 0
    compilation_time_ms: int = 0
    node_breakdown: Dict[str, int] = field(default_factory=dict)


@dataclass
class ASTCompilationResult:
    template: TemplateNode
    stats: CompilationStats
    ast_dict: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)


class LiquidASTCompiler:
    """
    High-level facade for compiling Shopify Liquid source to AST and performance metrics.
    """
    def compile(self, source: str, name: str = "template", file_path: Optional[str] = None) -> ASTCompilationResult:
        tree, stats = self.compile_source(source, name=name, file_path=file_path)
        return ASTCompilationResult(
            template=tree,
            stats=stats,
            ast_dict=tree.to_dict(),
            warnings=[]
        )

    @classmethod
    def compile_source(cls, source: str, name: str = "template", file_path: Optional[str] = None) -> Tuple[TemplateNode, CompilationStats]:
        start = time.perf_counter()
        parser = LiquidASTParser(source, name=name, file_path=file_path)
        tree = parser.parse()
        elapsed_ms = max(0, int((time.perf_counter() - start) * 1000))
        
        counts = parser._compute_ast_stats(tree)
        node_breakdown = {
            "TextNode": counts.get("text_nodes", 0),
            "VariableNode": counts.get("variable_nodes", 0),
            "TagNode": counts.get("tag_nodes", 0),
            "BlockNode": counts.get("block_nodes", 0),
            "RawNode": counts.get("raw_nodes", 0),
        }
        
        stats = CompilationStats(
            total_nodes=counts.get("total_nodes", 0),
            text_nodes=counts.get("text_nodes", 0),
            variable_nodes=counts.get("variable_nodes", 0),
            tag_nodes=counts.get("tag_nodes", 0),
            block_nodes=counts.get("block_nodes", 0),
            raw_nodes=counts.get("raw_nodes", 0),
            filter_count=counts.get("filter_count", 0),
            max_depth=counts.get("max_depth", 0),
            compilation_time_ms=elapsed_ms,
            node_breakdown=node_breakdown
        )
        return tree, stats

    @classmethod
    def compile_to_dict(cls, source: str, name: str = "template") -> Dict[str, Any]:
        tree, _ = cls.compile_source(source, name=name)
        return tree.to_dict()

    @classmethod
    def compile_to_json(cls, source: str, name: str = "template", indent: int = 2) -> str:
        tree, _ = cls.compile_source(source, name=name)
        return ast_to_json(tree, indent=indent)


def compile_liquid_to_ast(source: str, name: str = "template", file_path: Optional[str] = None) -> TemplateNode:
    """
    Compiles a raw Liquid template string into an AST TemplateNode tree.
    """
    parser = LiquidASTParser(source, name=name, file_path=file_path)
    return parser.parse()


def ast_to_dict(root: TemplateNode) -> Dict[str, Any]:
    """
    Serializes a TemplateNode AST tree into a Python dictionary.
    """
    return root.to_dict()


def ast_from_dict(data: Dict[str, Any]) -> TemplateNode:
    """
    Deserializes a dictionary back into a TemplateNode AST tree.
    """
    return TemplateNode.from_dict(data)


def ast_to_json(root: TemplateNode, indent: int = 2) -> str:
    """
    Serializes a TemplateNode AST tree into JSON string.
    """
    return json.dumps(root.to_dict(), indent=indent, ensure_ascii=False)


def ast_from_json(json_str: str) -> TemplateNode:
    """
    Deserializes a JSON string back into a TemplateNode AST tree.
    """
    data = json.loads(json_str)
    return TemplateNode.from_dict(data)

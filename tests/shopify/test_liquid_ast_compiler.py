# --- DNK-MRH-HEADER ---
# mrh_id: "tests_shopify_test_liquid_ast_compiler"
# purpose: "Unit & Integration Test Suite for Liquid AST Parser, Lexer & Tokenizer (DNK-ECOM-003 Phase 1)"
# author: "DNK-e.com Maksym"
# version: "1.0.0"
# status: "Active"
# language: "Python"
# --- END DNK-MRH-HEADER ---

import json
import uuid
import pytest
from apps.api.services.liquid_ast_compiler import (
    LiquidTokenizer,
    LiquidASTParser,
    LiquidASTCompiler,
    TokenType,
    TemplateNode,
    TextNode,
    VariableNode,
    TagNode,
    BlockNode,
    BlockBranch,
    FilterNode,
    RawNode,
    compile_liquid_to_ast,
    ast_to_dict,
    ast_from_dict,
    ast_to_json,
    ast_from_json,
)
from apps.api.db.models.shopify_theme_config import ShopifyThemeConfigModel
from apps.api.db.models.shopify_ast_compilation import ShopifyASTCompilationModel


class TestLiquidTokenizer:
    """Tests for Liquid lexical tokenization."""

    def test_tokenize_plain_text(self):
        source = "<div class='container'>Hello World</div>"
        tokenizer = LiquidTokenizer(source)
        tokens = tokenizer.tokenize()
        assert len(tokens) == 2  # Text + EOF
        assert tokens[0].type == TokenType.TEXT
        assert tokens[0].value == source

    def test_tokenize_variables_standard_and_trimmed(self):
        source = "{{ product.title }} and {{- customer.name -}}"
        tokens = LiquidTokenizer(source).tokenize()
        
        types = [t.type for t in tokens]
        assert TokenType.VAR_OPEN in types
        assert TokenType.VAR_CLOSE in types
        # Verify trim flags
        var_opens = [t for t in tokens if t.type == TokenType.VAR_OPEN]
        assert var_opens[0].trim_left is False
        assert var_opens[1].trim_left is True

    def test_tokenize_filters(self):
        source = '{{ product.price | money_with_currency | default: "$0.00" }}'
        tokens = LiquidTokenizer(source).tokenize()
        types = [t.type for t in tokens]
        assert TokenType.PIPE in types
        assert TokenType.COLON in types
        assert any(t.type == TokenType.STRING and t.value == "$0.00" for t in tokens)

    def test_tokenize_tags(self):
        source = "{% assign count = 42 %}{%- if count > 10 -%}"
        tokens = LiquidTokenizer(source).tokenize()
        types = [t.type for t in tokens]
        assert TokenType.TAG_OPEN in types
        assert TokenType.TAG_CLOSE in types
        assert any(t.type == TokenType.IDENTIFIER and t.value == "assign" for t in tokens)
        assert any(t.type == TokenType.IDENTIFIER and t.value == "if" for t in tokens)


class TestLiquidASTParser:
    """Tests for Liquid AST construction."""

    def test_parse_simple_template(self):
        source = "<h1>{{ page.title | upcase }}</h1>"
        tree = compile_liquid_to_ast(source, name="header.liquid")
        
        assert isinstance(tree, TemplateNode)
        assert tree.name == "header.liquid"
        assert len(tree.children) == 3
        
        # <h1>
        assert isinstance(tree.children[0], TextNode)
        assert tree.children[0].content == "<h1>"
        
        # {{ page.title | upcase }}
        var_node = tree.children[1]
        assert isinstance(var_node, VariableNode)
        assert var_node.expression == "page.title"
        assert len(var_node.filters) == 1
        assert var_node.filters[0].name == "upcase"
        
        # </h1>
        assert isinstance(tree.children[2], TextNode)
        assert tree.children[2].content == "</h1>"

    def test_parse_if_elsif_else_block(self):
        source = """
        {% if product.available %}
          <span>In Stock</span>
        {% elsif product.incoming %}
          <span>Coming Soon</span>
        {% else %}
          <span>Sold Out</span>
        {% endif %}
        """
        tree = compile_liquid_to_ast(source)
        blocks = [node for node in tree.children if isinstance(node, BlockNode)]
        assert len(blocks) == 1
        
        if_block = blocks[0]
        assert if_block.tag_name == "if"
        assert if_block.attributes.get("condition") == "product.available"
        assert len(if_block.branches) == 2  # elsif and else
        assert if_block.branches[0].branch_type == "elsif"
        assert if_block.branches[0].condition == "product.incoming"
        assert if_block.branches[1].branch_type == "else"

    def test_parse_for_loop_with_else(self):
        source = """
        {% for item in collection.products limit: 4 %}
          <div class="card">{{ item.title }}</div>
        {% else %}
          <p>No products found</p>
        {% endfor %}
        """
        tree = compile_liquid_to_ast(source)
        blocks = [node for node in tree.children if isinstance(node, BlockNode)]
        assert len(blocks) == 1
        
        for_block = blocks[0]
        assert for_block.tag_name == "for"
        assert for_block.attributes.get("loop_var") == "item"
        assert for_block.attributes.get("collection") == "collection.products"
        assert for_block.attributes.get("limit") == 4
        assert len(for_block.branches) == 1
        assert for_block.branches[0].branch_type == "else"

    def test_parse_schema_block(self):
        source = """
        <div class="banner">Hero</div>
        {% schema %}
        {
          "name": "Hero Banner",
          "settings": [
            {
              "type": "text",
              "id": "heading",
              "label": "Heading Text"
            }
          ]
        }
        {% endschema %}
        """
        tree = compile_liquid_to_ast(source)
        schema_nodes = [node for node in tree.children if isinstance(node, RawNode) and node.tag_name == "schema"]
        assert len(schema_nodes) == 1
        
        schema_node = schema_nodes[0]
        schema_json = json.loads(schema_node.content)
        assert schema_json["name"] == "Hero Banner"
        assert schema_json["settings"][0]["id"] == "heading"

    def test_parse_render_and_section_tags(self):
        source = """
        {% render 'icon-cart', size: 24, class: 'w-6 h-6' %}
        {% section 'announcement-bar' %}
        """
        tree = compile_liquid_to_ast(source)
        tag_nodes = [node for node in tree.children if isinstance(node, TagNode)]
        assert len(tag_nodes) == 2
        
        render_tag = tag_nodes[0]
        assert render_tag.tag_name == "render"
        assert render_tag.attributes.get("snippet") == "icon-cart"
        assert render_tag.attributes.get("kwargs") == {"size": 24, "class": "w-6 h-6"}
        
        section_tag = tag_nodes[1]
        assert section_tag.tag_name == "section"
        assert section_tag.attributes.get("section") == "announcement-bar"


class TestLiquidASTSerialization:
    """Tests for AST serialization, JSON roundtrip, and deserialization."""

    def test_ast_dict_and_json_roundtrip(self):
        source = """
        <div class="hero">
          {% if user.logged_in %}
            <p>Welcome back, {{ user.name | escape }}!</p>
          {% endif %}
        </div>
        """
        tree = compile_liquid_to_ast(source, name="welcome.liquid")
        
        # Serialize to dict & JSON
        ast_dict = ast_to_dict(tree)
        ast_json = ast_to_json(tree)
        
        assert isinstance(ast_dict, dict)
        assert ast_dict["node_type"] == "template"
        assert ast_dict["name"] == "welcome.liquid"
        
        # Reconstruct AST from dict and JSON
        reconstructed_from_dict = ast_from_dict(ast_dict)
        reconstructed_from_json = ast_from_json(ast_json)
        
        assert isinstance(reconstructed_from_dict, TemplateNode)
        assert isinstance(reconstructed_from_json, TemplateNode)
        assert len(reconstructed_from_dict.children) == len(tree.children)
        assert ast_to_dict(reconstructed_from_dict) == ast_dict
        assert ast_to_dict(reconstructed_from_json) == ast_dict

    def test_compiler_service_full_compilation(self):
        source = """
        <main>
          {% for product in collection.products %}
            {% render 'product-card', product: product %}
          {% endfor %}
        </main>
        """
        tree, stats = LiquidASTCompiler.compile_source(source, name="collection.liquid")
        
        assert isinstance(tree, TemplateNode)
        assert stats.total_nodes > 0
        assert stats.compilation_time_ms >= 0
        assert "BlockNode" in stats.node_breakdown
        assert "TagNode" in stats.node_breakdown

    def test_db_models_instantiation(self):
        ws_id = uuid.uuid4()
        theme_cfg = ShopifyThemeConfigModel(
            workspace_id=ws_id,
            theme_name="DNK Turbo Theme",
            theme_version="1.0.0",
            liquid_version="2024",
            optimization_level="aggressive",
            tree_shaking_enabled=True,
            minification_enabled=True,
            tailwind_jit_enabled=True,
        )
        assert theme_cfg.theme_name == "DNK Turbo Theme"
        assert theme_cfg.optimization_level == "aggressive"
        
        ast_comp = ShopifyASTCompilationModel(
            theme_config_id=theme_cfg.id,
            source_file_path="sections/main-product.liquid",
            ast_json={"node_type": "template", "children": []},
            compilation_time_ms=12,
            optimization_stats={"tree_shaken_blocks": 2},
        )
        assert ast_comp.source_file_path == "sections/main-product.liquid"
        assert ast_comp.compilation_time_ms == 12

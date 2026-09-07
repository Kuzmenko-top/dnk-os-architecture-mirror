# --- DNK-MRH-HEADER ---
# mrh_id: "tests/shopify/test_liquid_ast_optimizer.py"
# purpose: "Unit and integration tests for Shopify Liquid AST Optimizer, Tree-Shaking, DCE & Vite Plugin Integration."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-ECOM-003"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym / Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.liquid_ast_compiler import (
    LiquidASTCompiler,
    TemplateNode,
    BlockNode,
    TagNode,
    TextNode,
    RawNode,
)
from apps.api.services.liquid_ast_optimizer import (
    CSSMinifier,
    JSMinifier,
    LiquidASTOptimizer,
    OptimizationStats,
    ShopifyViteCompilerPlugin,
)


class TestMinifiers:
    def test_css_minifier_strips_comments_and_whitespace(self):
        raw_css = """
        /* Main Hero Header */
        .hero-banner {
            background-color: #ffffff;
            margin: 0px 10px;
            padding: 20px ;
        }
        /* Empty block */
        .empty-rule { }
        """
        minified = CSSMinifier.minify(raw_css)
        assert "/*" not in minified
        assert "Main Hero Header" not in minified
        assert ".empty-rule" not in minified
        assert ".hero-banner{background-color:#ffffff;margin:0px 10px;padding:20px}" == minified

    def test_js_minifier_strips_comments(self):
        raw_js = """
        // Initialize ATC Button
        function initATC() {
            /* multi line
               comment */
            const el = document.getElementById("buy-btn");
            if (el) {
                console.log("ATC Ready");
            }
        }
        """
        minified = JSMinifier.minify(raw_js)
        assert "//" not in minified
        assert "/*" not in minified
        assert "function initATC()" in minified
        assert "console.log(\"ATC Ready\");" in minified or "console.log(\"ATC Ready\")" in minified


class TestLiquidASTOptimizerDCE:
    @pytest.fixture
    def compiler(self):
        return LiquidASTCompiler()

    @pytest.fixture
    def optimizer(self):
        return LiquidASTOptimizer()

    def test_dead_code_elimination_prunes_false_if_block(self, compiler, optimizer):
        source = """
        <div>
          {% if false %}
            <div class="dead-code">This should never render</div>
          {% endif %}
          <p>Always visible</p>
        </div>
        """
        ast_result = compiler.compile(source)
        assert ast_result.template is not None

        optimized_tree, stats = optimizer.optimize(ast_result.template, source)
        assert stats.dead_branches_pruned >= 1
        assert stats.nodes_eliminated >= 1

        # Check serialized output has no dead-code node
        ast_dict = optimized_tree.to_dict()
        node_strs = str(ast_dict)
        assert "This should never render" not in node_strs
        assert "Always visible" in node_strs

    def test_dead_code_elimination_flattens_true_if_block(self, compiler, optimizer):
        source = """
        <div>
          {% if true %}
            <span>Main Branch Active</span>
          {% else %}
            <span>Unreachable Branch</span>
          {% endif %}
        </div>
        """
        ast_result = compiler.compile(source)
        assert ast_result.template is not None

        optimized_tree, stats = optimizer.optimize(ast_result.template, source)
        assert stats.dead_branches_pruned >= 1

        ast_dict = optimized_tree.to_dict()
        node_strs = str(ast_dict)
        assert "Main Branch Active" in node_strs
        assert "Unreachable Branch" not in node_strs

    def test_unused_assignment_tree_shaking(self, compiler, optimizer):
        source = """
        {% assign unused_variable = "dead_value" %}
        {% assign active_title = product.title %}
        <h1>{{ active_title }}</h1>
        """
        ast_result = compiler.compile(source)
        assert ast_result.template is not None

        optimized_tree, stats = optimizer.optimize(ast_result.template, source)
        assert stats.unused_assigns_pruned == 1

        ast_dict = optimized_tree.to_dict()
        node_strs = str(ast_dict)
        assert "unused_variable" not in node_strs
        assert "active_title" in node_strs

    def test_raw_comment_node_eliminated_in_optimization(self, compiler, optimizer):
        source = """
        <div>
          {% comment %}
            Internal developer notes that should be stripped
          {% endcomment %}
          <span>Visible Content</span>
        </div>
        """
        ast_result = compiler.compile(source)
        assert ast_result.template is not None

        optimized_tree, stats = optimizer.optimize(ast_result.template, source)
        assert stats.nodes_eliminated >= 1
        ast_dict = optimized_tree.to_dict()
        assert "Internal developer notes" not in str(ast_dict)
        assert "Visible Content" in str(ast_dict)


class TestLiquidASTOptimizerTreeShaking:
    @pytest.fixture
    def compiler(self):
        return LiquidASTCompiler()

    @pytest.fixture
    def optimizer(self):
        return LiquidASTOptimizer()

    def test_collects_referenced_snippets_and_sections(self, compiler, optimizer):
        source = """
        <header>
          {% section 'header' %}
          {% render 'product-card', product: product %}
          {% render 'price-badge' %}
        </header>
        """
        ast_result = compiler.compile(source)
        assert ast_result.template is not None

        available_snippets = ["product-card", "price-badge", "unused-carousel", "orphan-drawer"]
        optimized_tree, stats = optimizer.optimize(
            ast_result.template,
            source,
            available_snippets=available_snippets
        )

        assert "product-card" in stats.snippets_referenced
        assert "price-badge" in stats.snippets_referenced
        assert "header" in stats.sections_referenced
        assert "unused-carousel" in stats.snippets_pruned
        assert "orphan-drawer" in stats.snippets_pruned


class TestShopifyViteCompilerPlugin:
    def test_vite_config_generation(self):
        plugin = ShopifyViteCompilerPlugin(theme_root=".", output_dir="assets")
        config = plugin.generate_vite_config(["src/main.js", "src/styles.css"])

        assert "vite-plugin-shopify-liquid" in config["plugins"]
        assert config["build"]["outDir"] == "assets"
        assert config["build"]["rollupOptions"]["input"] == ["src/main.js", "src/styles.css"]

    def test_asset_tag_generation(self):
        plugin = ShopifyViteCompilerPlugin()
        css_tag = plugin.generate_asset_tag("theme.min.css", "stylesheet")
        js_tag = plugin.generate_asset_tag("app.min.js", "script")

        assert css_tag == "{{ 'theme.min.css' | asset_url | stylesheet_tag }}"
        assert js_tag == "{{ 'app.min.js' | asset_url | script_tag }}"

    def test_process_liquid_file_pipeline(self):
        plugin = ShopifyViteCompilerPlugin()
        liquid_source = """
        {% assign temp = 123 %}
        {% style %}
          .hero { color: red; margin: 10px; }
        {% endstyle %}
        {% render 'icon-star' %}
        <h1>{{ product.title }}</h1>
        """
        res = plugin.process_liquid_file(
            liquid_source=liquid_source,
            filename="sections/hero.liquid",
            available_snippets=["icon-star", "unused-modal"]
        )

        assert res["status"] == "success"
        assert res["filename"] == "sections/hero.liquid"
        assert "icon-star" in res["stats"]["snippets_referenced"]
        assert "unused-modal" in res["stats"]["snippets_pruned"]
        assert res["stats"]["unused_assigns_pruned"] == 1

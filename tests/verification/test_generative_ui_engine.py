# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_generative_ui_engine.py"
# purpose: "Verification tests for Generative UI Engine: Dashboards, Forms, Tables & Storybook Registry"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-UI-GEN-001", "DNK-UI-GEN-002", "DNK-UI-GEN-003"]
# status: "Active"
# version: "3.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.generative_ui_engine import (
    GenerativeUIEngine,
    UISpecParser,
    ComponentGenerator,
    FormGenerator,
    TableGenerator,
    RegistryGenerator,
    DataBindingLayer,
    UIValidator,
    UIComponentKind,
    GeneratedUIBundle,
    GeneratedFile,
    UISpec,
    MetricCardConfig,
    FormFieldConfig,
    ColumnConfig,
    DataBindingSpec,
)


def test_ui_spec_parser_dashboard_prompt():
    prompt = "Створи Dashboard для моніторингу агентів з метриками ASR, latency та error rate"
    spec = UISpecParser.parse_natural_language(prompt)

    assert spec.kind == UIComponentKind.DASHBOARD
    assert len(spec.metric_cards) >= 2
    assert any(card.metric_key == "asr_rate" for card in spec.metric_cards)
    assert any(card.metric_key == "p95_latency_ms" for card in spec.metric_cards)
    assert spec.data_binding is not None
    assert spec.data_binding.query_key == "agentMetrics"


def test_ui_spec_parser_form_prompt():
    prompt = "Форма додавання агента з полями: name, model, api_key, status"
    spec = UISpecParser.parse_natural_language(prompt)

    assert spec.kind == UIComponentKind.FORM
    assert len(spec.fields) == 4
    field_names = [f.name for f in spec.fields]
    assert "name" in field_names
    assert "model" in field_names
    assert "api_key" in field_names
    assert "status" in field_names
    assert spec.data_binding is not None
    assert spec.data_binding.method == "POST"


def test_ui_spec_parser_table_prompt():
    prompt = "Таблиця агентів з сортуванням, фільтрацією, пагінацією"
    spec = UISpecParser.parse_natural_language(prompt)

    assert spec.kind == UIComponentKind.TABLE
    assert len(spec.columns) >= 4
    column_keys = [c.key for c in spec.columns]
    assert "name" in column_keys
    assert "model" in column_keys
    assert "status" in column_keys
    assert "latency_p95" in column_keys
    assert spec.data_binding is not None
    assert spec.data_binding.method == "GET"


def test_ui_spec_parser_registry_prompt():
    prompt = "Design system registry storybook компонентів"
    spec = UISpecParser.parse_natural_language(prompt)

    assert spec.kind == UIComponentKind.REGISTRY


def test_component_generator_dashboard():
    engine = GenerativeUIEngine()
    prompt = "Створи Dashboard для моніторингу агентів з ASR та latency"
    bundle = engine.generate_ui_from_prompt(prompt)

    assert bundle.validation_status == "PASSED"
    assert len(bundle.files) == 6
    paths = [f.relative_path for f in bundle.files]
    assert "apps/web/app/dashboard/page.tsx" in paths
    assert "apps/web/app/dashboard/components/AgentMetricsCards.tsx" in paths
    assert "apps/web/app/dashboard/components/ASRChart.tsx" in paths
    assert "apps/web/app/dashboard/hooks/useAgentMetrics.ts" in paths
    assert "apps/web/app/dashboard/types.ts" in paths


def test_form_generator_rhf_zod():
    engine = GenerativeUIEngine()
    prompt = "Форма створення нового агента"
    bundle = engine.generate_ui_from_prompt(prompt)

    assert bundle.validation_status == "PASSED"
    assert len(bundle.files) == 3
    paths = [f.relative_path for f in bundle.files]
    assert "apps/web/app/agents/new/page.tsx" in paths
    assert "apps/web/app/agents/new/components/AgentForm.tsx" in paths
    assert "apps/web/app/agents/new/hooks/useCreateAgent.ts" in paths

    # Check Zod schema in form component
    form_file = next(f for f in bundle.files if f.relative_path == "apps/web/app/agents/new/components/AgentForm.tsx")
    assert "z.object({" in form_file.code
    assert "useForm<AgentFormData>" in form_file.code
    assert "zodResolver(agentFormSchema)" in form_file.code


def test_table_generator_tanstack_table():
    engine = GenerativeUIEngine()
    prompt = "Таблиця агентів з пагінацією та фільтрами"
    bundle = engine.generate_ui_from_prompt(prompt)

    assert bundle.validation_status == "PASSED"
    assert len(bundle.files) == 3
    paths = [f.relative_path for f in bundle.files]
    assert "apps/web/app/agents/page.tsx" in paths
    assert "apps/web/app/agents/components/AgentsTable.tsx" in paths
    assert "apps/web/app/agents/hooks/useAgents.ts" in paths

    # Check TanStack Table in table component
    table_file = next(f for f in bundle.files if f.relative_path == "apps/web/app/agents/components/AgentsTable.tsx")
    assert "useReactTable" in table_file.code
    assert "getCoreRowModel" in table_file.code
    assert "getPaginationRowModel" in table_file.code
    assert "flexRender" in table_file.code


def test_registry_generator_storybook():
    engine = GenerativeUIEngine()
    prompt = "Component registry storybook export"
    bundle = engine.generate_ui_from_prompt(prompt)

    assert bundle.validation_status == "PASSED"
    assert len(bundle.files) == 2
    paths = [f.relative_path for f in bundle.files]
    assert "apps/web/ui/index.ts" in paths
    assert "apps/web/.storybook/main.ts" in paths


def test_ui_validator_catches_violations():
    invalid_file = GeneratedFile(
        relative_path="apps/web/app/broken/Broken.tsx",
        is_client_component=True,
        code="export function Broken() { return <div>Unbalanced",  # missing "use client", unclosed braces, no MRH
        file_type="tsx",
    )
    bundle = GeneratedUIBundle(
        spec=UISpec(title="Broken", kind=UIComponentKind.FORM, description="test"),
        files=[invalid_file],
    )

    validated = UIValidator.validate_bundle(bundle)
    assert validated.validation_status == "FAILED"
    assert any("Missing DNK-MRH-HEADER" in err for err in validated.validation_errors)
    assert any("Unbalanced curly braces" in err for err in validated.validation_errors)
    assert any("missing '\"use client\";'" in err for err in validated.validation_errors)

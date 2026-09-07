# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_tencent_memory_hub.py"
# purpose: "Unit and Integration tests for TencentDB Agent Memory Hub (CodeGraph AST, LLM-Wiki, Distillation, and Proxy)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-MEMORY-HUB-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from core.memory.tencent_memory_provider import (
    TencentDBMemoryProvider,
    LocalCodeGraphEngine,
    LLMWikiEngine,
    LayeredDistillationEngine
)

def test_codegraph_ast_indexing_and_symbol_lookup():
    engine = LocalCodeGraphEngine()
    sample_code = chr(10).join([
        'def authenticate_user(token: str) -> bool:',
        '    """Validates authentication token."""',
        '    return True',
        '',
        'class MemoryVault:',
        '    """Vault for persistent facts."""',
        '    def store_fact(self, fact: str):',
        '        pass'
    ])
    engine.index_file('core/auth/security.py', content=sample_code)
    func_sym = engine.find_symbol('authenticate_user')
    assert func_sym is not None
    assert func_sym['type'] == 'function'
    assert func_sym['file_path'] == 'core/auth/security.py'
    assert 'Validates authentication token' in func_sym['docstring']

    cls_sym = engine.find_symbol('MemoryVault')
    assert cls_sym is not None
    assert cls_sym['type'] == 'class'

def test_llm_wiki_engine_search():
    wiki = LLMWikiEngine()
    wiki.add_wiki_node(
        topic='Architecture Overview',
        content='DNK OS uses a microservice tree with AST CodeGraph indexing.',
        tags=['arch', 'codegraph', 'core']
    )
    wiki.add_wiki_node(
        topic='Shopify Sync',
        content='Automated Liquid theme deployment pipeline.',
        tags=['shopify', 'ecom']
    )
    results = wiki.search_wiki('CodeGraph')
    assert len(results) == 1
    assert results[0]['topic'] == 'Architecture Overview'

def test_layered_distillation_engine():
    distill = LayeredDistillationEngine()
    distill.distill_l1_fact('TencentDB uses Redis as L0 cache and SQLite/Postgres as L1.', domain='infra')
    distill.update_l2_context('TASK-101', {'branch': 'mentor/core/test'})
    recalled = distill.recall_layered('What is the infra cache for TencentDB?')
    assert len(recalled['l1_facts']) == 1
    assert recalled['l1_facts'][0]['domain'] == 'infra'
    assert recalled['l2_context']['active_task_id'] == 'TASK-101'

def test_tencent_memory_provider_integration():
    provider = TencentDBMemoryProvider()
    provider.initialize(session_id='test-session-001', tenant_id='tenant-dnk', workspace_id='ws-main')
    schemas = provider.get_tool_schemas()
    names = [s['name'] for s in schemas]
    assert 'codegraph_find_symbol' in names
    assert 'codegraph_impact_analysis' in names
    assert 'wiki_query' in names
    assert 'tencent_add_fact' in names

    dummy_code = chr(10).join([
        'def execute_pipeline(pipeline_id: str):',
        '    """Runs agentic swarm pipeline."""',
        '    return True'
    ])
    provider.codegraph.index_file('core/pipeline.py', content=dummy_code)

    call_res = provider.handle_tool_call('codegraph_find_symbol', {'symbol_name': 'execute_pipeline'})
    parsed = json.loads(call_res)
    assert parsed['name'] == 'execute_pipeline'
    assert parsed['file_path'] == 'core/pipeline.py'

    fact_res = provider.handle_tool_call('tencent_add_fact', {
        'fact': 'Swarm routing is mediated by Tencent Proxy.',
        'domain': 'swarm'
    })
    fact_parsed = json.loads(fact_res)
    assert fact_parsed['status'] == 'stored'

    prefetch_out = provider.prefetch('Tell me about swarm routing and proxy')
    assert '<memory-context>' in prefetch_out
    assert 'Swarm routing is mediated by Tencent Proxy.' in prefetch_out

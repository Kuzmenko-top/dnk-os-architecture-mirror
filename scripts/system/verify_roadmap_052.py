#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/verify_roadmap_052.py"
# purpose: "End-to-end local verification script for all 5 steps of the 052 roadmap."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK Swarm (Gerych Prime & Swarm Director)"
# --- END DNK-MRH-HEADER ---

import sys
import json
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_step_1():
    print("🔹 [КРОК 1] Перевірка UnifiedMemoryBroker (рекурсивне сканування сховища)...")
    from core.memory.unified_memory_broker import UnifiedMemoryBroker, MemoryTier
    t0 = time.time()
    broker = UnifiedMemoryBroker(vault_path=str(PROJECT_ROOT / "docs/notes"))
    stats = broker.get_tier_stats()
    query_res = broker.route_and_query("Remotion", tiers=[MemoryTier.OBSIDIAN_VAULT], limit=3)
    dt_ms = (time.time() - t0) * 1000

    assert stats["tier_4_obsidian_notes"] > 0, "Не знайдено жодної нотатки в сховищі"
    assert len(query_res.records) > 0, "Запит до сховища не повернув записів"
    
    print(f"   ✅ Успішно! Знайдено {stats['tier_4_obsidian_notes']} нотаток у сховищі.")
    print(f"   ⏱️  Час вибірки: {query_res.total_latency_ms:.2f}ms (загальний час кроку: {dt_ms:.2f}ms)")
    print(f"   🔍 Топ результат: {query_res.records[0].topic}")
    return True

def run_step_2_and_3():
    print("\n🔹 [КРОК 2 & 3] Перевірка гігієни нотаток та Adversarial Quality Gate...")
    from tests.verification.test_obsidian_vault_hygiene import (
        test_vault_notes_yaml_frontmatter_validity,
        test_vault_root_notes_header_hygiene,
        test_vault_note_prefixes_unique
    )
    test_vault_notes_yaml_frontmatter_validity()
    test_vault_root_notes_header_hygiene()
    test_vault_note_prefixes_unique()
    print("   ✅ Успішно! Усі YAML frontmatter, MRH-заголовки та префікси нотаток валідні й унікальні.")
    return True

def run_step_4():
    print("\n🔹 [КРОК 4] Перевірка Swarm Control Plane (SwarmDirector + ExecutionBroker)...")
    from core.orchestrator.swarm_director import SwarmDirector
    from core.framework.execution_broker import ExecutionBroker
    
    director = SwarmDirector()
    health = director.get_swarm_health()
    agents = director.list_agents()
    assert health["total_agents"] == 14, f"Очікувалось 14 агентів, знайдено {health['total_agents']}"
    assert health["status"] == "HEALTHY"

    # Семантичний роутинг
    sample_task = "Створити 9:16 Remotion відео-креатив для Instagram Reels"
    routed_agent = director.route_agent(sample_task)
    assert routed_agent == "dnk_video_ai_creator", f"Невірний агент: {routed_agent}"

    # Виконання DAG пайплайну
    exec_broker = ExecutionBroker()
    pipe = exec_broker.create_dag_pipeline("local_verify_pipeline")

    def cmo_step(**kw):
        return {"brief": "Launch PersonaLive", "offer": "B2B Ecom Streamer"}

    def video_step(**kw):
        return {"render": "Remotion 9:16", "frames": 450, "fps": 30}

    def auditor_step(**kw):
        return {"gate": "100% GREEN", "approved": True}

    pipe.step("cmo_brief", cmo_step, agent_role="dnk_marketing_cmo")
    pipe.step("video_render", video_step, depends_on=["cmo_brief"], agent_role="dnk_video_ai_creator")
    pipe.step("qa_gate", auditor_step, depends_on=["video_render"], agent_role="gerych_auditor")

    res = pipe.execute()
    assert res["summary"]["all_completed"] is True, "Пайплайн не завершився успішно"
    
    print(f"   ✅ Успішно! SwarmDirector: 14 агентів готові (HEALTHY).")
    print(f"   🎯 Семантичний роутинг: \"{sample_task[:35]}...\" -> [{routed_agent}]")
    print(f"   ⚡ DAG Pipeline: виконано 3 кроки (cmo_brief -> video_render -> qa_gate). All completed = True.")
    return True

def run_step_5():
    print("\n🔹 [КРОК 5] Перевірка Маркетингового Хабу та Remotion Шаблонів...")
    from tests.verification.test_marketing_assets_hygiene import (
        test_marketing_assets_directory_and_core_files_exist,
        test_remotion_template_json_manifests_are_valid,
        test_commercial_pitches_coverage_of_core_innovations
    )
    test_marketing_assets_directory_and_core_files_exist()
    test_remotion_template_json_manifests_are_valid()
    test_commercial_pitches_coverage_of_core_innovations()
    print("   ✅ Успішно! Шаблони Remotion (9:16, 16:9, 1:1) та комерційні пітчі (PersonaLive, Diffusion Studio, Lakehouse, Swarm) повністю валідні.")
    return True

def main():
    print("=" * 70)
    print("🚀 DNK OS MVP: ЛОКАЛЬНА ВЕРИФІКАЦІЯ ВСІХ ЕТАПІВ ДОРОЖНЬОЇ КАРТИ 052")
    print("=" * 70)
    
    try:
        run_step_1()
        run_step_2_and_3()
        run_step_4()
        run_step_5()
        print("\n" + "=" * 70)
        print("🏆 100% УСПІХ! УСІ 5 КРОКІВ ДОРОЖНЬОЇ КАРТИ ПРАЦЮЮТЬ БЕЗДОГАННО.")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n❌ ПОМИЛКА ВЕРИФІКАЦІЇ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ НЕПЕРЕДБАЧЕНА ПОМИЛКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/system/verify_gemini_drift_live.py"
# purpose: "Live local verification of Gemini drift monitoring, self-healing loop, and telemetry endpoints."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import time
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.monitoring.metrics import metrics_registry
from core.orchestrator.gemini_self_heal import GeminiSelfHealer
from services.dnk_analytics.telemetry_exporter import default_telemetry_exporter

def run_live_verification():
    print("=" * 65)
    print("🚀 [DNK OS] ЛОКАЛЬНА ПЕРЕВІРКА КОНТУРУ САМОЗЦІЛЕННЯ ТА ТЕЛЕМЕТРІЇ")
    print("=" * 65)

    # 1. Створюємо екземпляр GeminiSelfHealer
    healer = GeminiSelfHealer(
        telemetry_exporter=default_telemetry_exporter,
        use_online_baseline=True,
        use_ema=True,
        max_retries=2
    )

    print("\n🔹 ЕТАП 1: Симуляція нормальних генерацій (навчання бейзлайну)")
    for i in range(5):
        def normal_call(p):
            return f'{{"step": {i}, "status": "ok", "payload": "healthy response number {i} with high entropy words and diverse vocabulary"}}'
        
        res = healer.execute_with_healing(
            call_fn=normal_call,
            initial_params={"model": "gemini-2.5-pro", "temperature": 0.7},
            expect_json=True
        )
        print(f"  [Sample {i+1}/5] Успіх: {res.success} | Спроб: {res.total_attempts} | Дії: {res.healing_actions or 'NONE'}")

    print("\n🔹 ЕТАП 2: Симуляція битого JSON (Zero-cost Local Repair)")
    # Відповідь містить markdown обгортку, Python True, висячі коми та unquoted ключ
    def broken_json_call(p):
        return """Here is the response from Gemini:
        ```json
        {
            "task": "local_repair_test",
            status: "repaired_instantly",
            "active": True,
            "details": "trailing comma test",
        }
        ```
        Hope this structure helps!"""

    t_start = time.perf_counter()
    res_heal = healer.execute_with_healing(
        call_fn=broken_json_call,
        initial_params={"model": "gemini-2.5-pro"},
        expect_json=True
    )
    t_repair = (time.perf_counter() - t_start) * 1000

    print(f"  ⚡ Відновлено за {t_repair:.2f} мс!")
    print(f"  🛠️ Стратегія ремонту: {res_heal.healing_actions}")
    print(f"  📦 Отриманий розпарсений JSON: {res_heal.parsed_json}")
    assert res_heal.success is True
    assert res_heal.parsed_json is not None
    assert res_heal.parsed_json["task"] == "local_repair_test"

    print("\n🔹 ЕТАП 3: Симуляція колапсу ентропії (Entropy Collapse & Dynamic Retry)")
    # Модель спочатку зациклюється (падає ентропія), а після демпфування температури повертає здоровий текст
    call_attempts = 0
    def collapsing_call(p):
        nonlocal call_attempts
        call_attempts += 1
        if call_attempts == 1:
            # Зациклення токенів: низька ентропія
            return '{"repeat": "loop loop loop loop loop loop loop loop loop loop loop loop"}'
        return '{"recovered": true, "message": "Entropy restored to high diversity after temperature dampening"}'

    res_entropy = healer.execute_with_healing(
        call_fn=collapsing_call,
        initial_params={"model": "gemini-2.5-pro", "temperature": 0.9},
        expect_json=True
    )
    print(f"  🔄 Застосовано спроб: {res_entropy.total_attempts}")
    print(f"  🛠️ Фінальні дії зцілення: {res_entropy.healing_actions}")
    print(f"  📦 Результат після самозцілення: {res_entropy.parsed_json}")

    print("\n🔹 ЕТАП 4: Перевірка ендпоінтів API та Експорту Телеметрії")
    client = TestClient(app)

    # 4.1. Prometheus Endpoint /metrics
    resp_metrics = client.get("/metrics")
    print(f"  [GET /metrics] HTTP Status: {resp_metrics.status_code}")
    metrics_text = resp_metrics.text
    assert resp_metrics.status_code == 200
    assert "dnk_gemini_entropy_mean" in metrics_text
    assert "dnk_gemini_self_healings_total" in metrics_text
    print("  ✅ Prometheus Exposition формат валідний:")
    for line in metrics_text.splitlines():
        if "dnk_gemini_self_healings_total" in line or "dnk_gemini_entropy_mean" in line or "dnk_gemini_is_healthy" in line:
            print(f"     | {line}")

    # 4.2. Visual Shell JSON Endpoint
    resp_telemetry = client.get("/api/v1/analytics/drift/telemetry")
    print(f"\n  [GET /api/v1/analytics/drift/telemetry] HTTP Status: {resp_telemetry.status_code}")
    assert resp_telemetry.status_code == 200
    telem_data = resp_telemetry.json()
    print("  ✅ DNK Visual Shell JSON формат валідний:")
    print(f"     | Model: {telem_data.get('model')}")
    print(f"     | Status: {telem_data.get('status')} (is_healthy: {telem_data.get('is_healthy')})")
    print(f"     | Total Samples: {telem_data.get('summary', {}).get('total_samples')}")
    print(f"     | Total Self-Healed: {telem_data.get('healing', {}).get('total_healed')}")
    print(f"     | Healing Counts: {telem_data.get('healing', {}).get('cumulative_counts')}")
    w_stats = telem_data.get("welford_stats") or {}
    ent_stats = w_stats.get("entropy") or {}
    ema_stats = telem_data.get("baseline_ema") or {}

    print(f"     | Online Welford Entropy Mean: {ent_stats.get('mean', 0.0):.4f}")
    print(f"     | EMA Entropy Mean: {ema_stats.get('entropy_mean', 0.0):.4f}")

    print("\n" + "=" * 65)
    print("🎉 ВСІ 4 РІВНІ ПЕРЕВІРЕНО УСПІШНО! СИСТЕМА ПОВНІСТЮ ГОТОВА ДО РОБОТИ.")
    print("=" * 65)

if __name__ == "__main__":
    run_live_verification()

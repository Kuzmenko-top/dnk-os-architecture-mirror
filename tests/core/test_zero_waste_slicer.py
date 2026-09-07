# --- DNK-MRH-HEADER ---
# mrh_id: "tests_core_test_zero_waste_slicer"
# purpose: "Unit and integration tests for Zero-Waste Task Slicing DAG Engine"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# alters_files: []
# triggers_tasks: []
# --- END DNK-MRH-HEADER ---

import tempfile
from pathlib import Path
from core.orchestrator.zero_waste_slicer import ZeroWasteSlicer, TaskSlice


def test_decompose_markdown_table():
    prompt = """
## План дій: Phase 1 Completion (1 день)

| № | Завдання | Файл | ETA | DoD |
|---|----------|------|-----|-----|
| **1.1** | `triggerNodeAgent` екшн | `apps/web/store/canvasStore.ts` | 2-3 год | Клік на ноду → `{type: "TASK_EXECUTE"}` у WebSocket |
| **1.2** | Live стрім логів | `apps/web/components/canvas/StitchAgentLog.tsx` | 2 год | Відображення стрімінгу від бекенду |
| **1.3** | E2E перевірка | `tests/canvas/test_canvas_swarm_bridge.py` | 1 год | Повний прогон |
"""
    slicer = ZeroWasteSlicer()
    slices = slicer.decompose(prompt)

    assert len(slices) == 3
    assert slices[0].id == "slice-1-1"
    assert "apps/web/store/canvasStore.ts" in slices[0].target_files
    assert slices[0].max_iterations <= 25

    assert slices[1].id == "slice-1-2"
    assert "apps/web/components/canvas/StitchAgentLog.tsx" in slices[1].target_files

    assert slices[2].id == "slice-1-3"
    assert "tests/canvas/test_canvas_swarm_bridge.py" in slices[2].target_files
    assert "pytest" in slices[2].verification_cmd


def test_decompose_numbered_list():
    prompt = """
1.1 Create auth router in apps/api/routers/auth.py
1.2 Implement login form in apps/web/components/LoginForm.tsx
1.3 Add security tests in tests/security/test_auth.py
"""
    slicer = ZeroWasteSlicer()
    slices = slicer.decompose(prompt)

    assert len(slices) == 3
    assert slices[0].id == "slice-1-1"
    assert "apps/api/routers/auth.py" in slices[0].target_files
    assert slices[1].id == "slice-1-2"
    assert "apps/web/components/LoginForm.tsx" in slices[1].target_files
    assert slices[2].id == "slice-1-3"
    assert "tests/security/test_auth.py" in slices[2].target_files


def test_save_and_load_plan():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        slicer = ZeroWasteSlicer(workspace_root=tmp_path)

        slices = [
            TaskSlice(
                id="slice-a",
                index=1,
                title="Subtask A",
                description="Desc A",
                target_files=["apps/web/store/test.ts"],
                max_iterations=20
            ),
            TaskSlice(
                id="slice-b",
                index=2,
                title="Subtask B",
                description="Desc B",
                target_files=["apps/api/test.py"],
                max_iterations=25
            )
        ]

        plan_file = slicer.save_plan(slices, "test_plan.json")
        assert plan_file.exists()

        loaded = slicer.load_plan("test_plan.json")
        assert len(loaded) == 2
        assert loaded[0].id == "slice-a"
        assert loaded[1].id == "slice-b"

        # Check next pending slice
        next_s = slicer.get_next_pending_slice("test_plan.json")
        assert next_s is not None
        assert next_s.id == "slice-a"

        # Complete first slice
        slicer.update_slice_status("slice-a", "completed", summary="Done A", filename="test_plan.json")
        next_s = slicer.get_next_pending_slice("test_plan.json")
        assert next_s is not None
        assert next_s.id == "slice-b"

        # Complete second slice
        slicer.update_slice_status("slice-b", "completed", summary="Done B", filename="test_plan.json")
        next_s = slicer.get_next_pending_slice("test_plan.json")
        assert next_s is None


def test_generate_slice_prompt():
    slicer = ZeroWasteSlicer()
    slice_item = TaskSlice(
        id="slice-1",
        index=1,
        title="Setup router",
        description="Write FastAPI router",
        target_files=["apps/api/test.py"],
        max_iterations=20,
        dod=["Router returns 200 OK"],
        verification_cmd="uv run pytest tests/test_router.py"
    )

    prompt = slicer.generate_slice_prompt(slice_item, total_count=3)
    assert "ZERO-WASTE SLICE [1/3]" in prompt
    assert "apps/api/test.py" in prompt
    assert "Router returns 200 OK" in prompt
    assert "uv run pytest tests/test_router.py" in prompt
    assert "DIRECTIVE" in prompt
    assert "BLOCKED RULE" in prompt


def test_decompose_canonical_markdown_slices():
    prompt = """
# 🎯 СЛАЙС 1.1: Створити 5 компонентів Mind Map нод

## 📌 ЦІЛЬОВА ДИРЕКТИВА
Створити 5 компонентів у apps/web/components/canvas/nodes/.

## 📁 ЦІЛЬОВІ ФАЙЛИ
- [NEW] apps/web/components/canvas/nodes/MindMapIdeaNode.tsx
- [NEW] apps/web/components/canvas/nodes/MindMapGoalNode.tsx

## ✅ DEFINITION OF DONE (DoD)
- ✅ 5 файлів нод створено
- ✅ npx tsc --noEmit повертає 0 помилок

## 🔍 КОМАНДА ВЕРИФІКАЦІЇ
```bash
npx --prefix apps/web tsc --project apps/web/tsconfig.json --noEmit
```

# 🎯 СЛАЙС 1.2: Створити 4 типи зв'язків
- apps/web/components/canvas/edges/DependencyEdge.tsx
- ✅ 4 еджі створено
"""
    slicer = ZeroWasteSlicer()
    slices = slicer.decompose(prompt)

    assert len(slices) == 2
    assert slices[0].id == "slice-1-1"
    assert "apps/web/components/canvas/nodes/MindMapIdeaNode.tsx" in slices[0].target_files
    assert "apps/web/components/canvas/nodes/MindMapGoalNode.tsx" in slices[0].target_files
    assert "npx --prefix apps/web tsc" in slices[0].verification_cmd
    assert any("5 файлів нод створено" in d for d in slices[0].dod)

    assert slices[1].id == "slice-1-2"
    assert "apps/web/components/canvas/edges/DependencyEdge.tsx" in slices[1].target_files


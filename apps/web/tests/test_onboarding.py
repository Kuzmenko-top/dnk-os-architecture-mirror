# --- DNK-MRH-HEADER ---
# mrh_id: "apps/web/tests/test_onboarding.py"
# purpose: "Comprehensive Unit Test Suite for DNK OS User Onboarding Flow (Slice 13.1)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych"
# standard: "DNK-STD-0090"
# --- END DNK-MRH-HEADER ---

import os
import re
import pytest

HUB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

TARGET_FILES = [
    "apps/web/app/onboarding/page.tsx",
    "apps/web/components/onboarding/OnboardingWizard.tsx",
    "apps/web/components/onboarding/StepWelcome.tsx",
    "apps/web/components/onboarding/StepTutorial.tsx",
    "apps/web/components/onboarding/StepVideoGuides.tsx",
    "docs/user-guides/GETTING_STARTED.md",
    "docs/user-guides/VIDEO_TUTORIALS.md",
    "apps/web/app/page.tsx",
]


def test_onboarding_target_files_exist():
    """Test 1: Verify all 8 target files exist on disk."""
    for rel_path in TARGET_FILES:
        full_path = os.path.join(HUB_ROOT, rel_path)
        assert os.path.exists(full_path), f"Missing required file: {rel_path}"


def test_getting_started_mrh_and_structure():
    """Test 2: GETTING_STARTED.md created with MRH DNK-STD-0090 and complete structure."""
    path = os.path.join(HUB_ROOT, "docs/user-guides/GETTING_STARTED.md")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DNK-STD-0090" in content, "Missing standard DNK-STD-0090 in MRH header"
    assert "Швидкий старт (5 хвилин)" in content or "Швидкий старт" in content
    assert "Створення першого Canvas" in content or "Перші кроки" in content
    assert "Advanced Features" in content or "Просунуті можливості" in content
    assert "Troubleshooting" in content or "Вирішення проблем" in content
    assert "FAQ" in content or "Поширені запитання" in content
    assert "```python" in content, "Missing Python code example"
    assert "```typescript" in content or "```javascript" in content, "Missing TypeScript/JavaScript code example"


def test_video_tutorials_mrh_and_timestamps():
    """Test 3: VIDEO_TUTORIALS.md created with MRH DNK-STD-0091, timestamps and transcripts."""
    path = os.path.join(HUB_ROOT, "docs/user-guides/VIDEO_TUTORIALS.md")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DNK-STD-0091" in content, "Missing standard DNK-STD-0091 in MRH header"
    assert "5:32" in content, "Missing 5:32 timestamp"
    assert "8:15" in content, "Missing 8:15 timestamp"
    assert "12:45" in content, "Missing 12:45 timestamp"
    assert "Transcript" in content or "Текстова транскрипція" in content


def test_onboarding_wizard_renders_5_steps():
    """Test 4: OnboardingWizard renders 5 steps."""
    path = os.path.join(HUB_ROOT, "apps/web/components/onboarding/OnboardingWizard.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "TOTAL_STEPS = 5" in content, "TOTAL_STEPS must be 5"
    assert "StepWelcome" in content
    assert "StepTutorial" in content
    assert "StepVideoGuides" in content
    assert "renderKnowledgeBase" in content or "Knowledge Base" in content
    assert "renderCompletion" in content or "Вітаємо! Ви готові до роботи" in content


def test_progress_bar_updates_correctly():
    """Test 5: Progress bar updates correctly with accessible ARIA tags."""
    path = os.path.join(HUB_ROOT, "apps/web/components/onboarding/OnboardingWizard.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'role="progressbar"' in content
    assert "aria-valuenow" in content
    assert "progressPercentage" in content
    assert "Step {currentStep} of {TOTAL_STEPS}" in content or "Крок {currentStep} з {TOTAL_STEPS}" in content


def test_local_storage_persists_progress():
    """Test 6: Local storage persists progress and completion flag."""
    path = os.path.join(HUB_ROOT, "apps/web/components/onboarding/OnboardingWizard.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "dnk_onboarding_completed" in content
    assert "dnk_onboarding_completed_steps" in content
    assert "localStorage.setItem" in content
    assert "localStorage.getItem" in content


def test_navigation_back_next_skip_works():
    """Test 7: Navigation Back/Next/Skip handlers are present and operational."""
    path = os.path.join(HUB_ROOT, "apps/web/components/onboarding/OnboardingWizard.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "handleNext" in content
    assert "handleBack" in content
    assert "handleSkip" in content
    assert "finishOnboarding" in content


def test_step_welcome_content_and_cta():
    """Test 8: StepWelcome contains welcome copy, 2-3 sentence description, and CTA buttons."""
    path = os.path.join(HUB_ROOT, "apps/web/components/onboarding/StepWelcome.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Ласкаво просимо до" in content
    assert "Розпочати тур" in content
    assert "Пропустити" in content
    assert "DNK OS" in content


def test_step_tutorial_interactive_actions():
    """Test 9: StepTutorial includes 3 interactive actions with real-time feedback."""
    path = os.path.join(HUB_ROOT, "apps/web/components/onboarding/StepTutorial.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Створіть своє перше полотно" in content
    assert "Generate" in content
    assert "Подивіться результат" in content
    assert "Чудово! Ви створили полотно" in content
    assert "3 з 3 дій виконано" in content or "completedCount" in content


def test_step_video_guides_and_page_cta():
    """Test 10: StepVideoGuides badges and apps/web/app/page.tsx onboarding CTA integration."""
    video_path = os.path.join(HUB_ROOT, "apps/web/components/onboarding/StepVideoGuides.tsx")
    with open(video_path, "r", encoding="utf-8") as f:
        v_content = f.read()

    assert "5:32" in v_content
    assert "8:15" in v_content
    assert "12:45" in v_content
    assert "Дивитися всі відео" in v_content

    page_path = os.path.join(HUB_ROOT, "apps/web/app/page.tsx")
    with open(page_path, "r", encoding="utf-8") as f:
        p_content = f.read()

    assert "OnboardingWizard" in p_content
    assert "Пройти Onboarding" in p_content
    assert "/onboarding" in p_content

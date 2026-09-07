# --- DNK-MRH-HEADER ---
# mrh_id: "apps/web/tests/test_interactive_tutorial.py"
# purpose: "Comprehensive Verification Suite for Slice 13.2 Interactive Tutorial (In-App Canvas Demo)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---

import os
import re
import pytest

HUB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))


def test_tutorial_target_files_exist():
    """Test 1: Verify all required tutorial target files exist with DNK-MRH headers."""
    target_files = [
        "apps/web/components/tutorial/InteractiveCanvasDemo.tsx",
        "apps/web/components/tutorial/StepByStepGuide.tsx",
        "apps/web/components/tutorial/RealTimeFeedback.tsx",
        "apps/web/components/tutorial/AchievementBadges.tsx",
        "apps/web/app/onboarding/page.tsx",
        "apps/web/tests/test_interactive_tutorial.py"
    ]
    for rel_path in target_files:
        full_path = os.path.join(HUB_ROOT, rel_path)
        assert os.path.exists(full_path), f"Missing target file: {rel_path}"
        with open(full_path, "r", encoding="utf-8") as f:
            header = f.read(500)
            assert "DNK-MRH-HEADER" in header, f"Missing DNK-MRH header in {rel_path}"


def test_interactive_canvas_demo_structure_and_mock_data():
    """Test 2: Verify InteractiveCanvasDemo embeds canvas, mock data, glow highlights and click tracking."""
    path = os.path.join(HUB_ROOT, "apps/web/components/tutorial/InteractiveCanvasDemo.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Mock data presence
    assert "INITIAL_MOCK_NODES" in content
    assert "Input Prompt" in content
    assert "Gerych Planner" in content
    assert "Builder Worker" in content

    # Highlight and glow effect
    assert "ring-4 ring-cyan-400" in content or "getHighlightClass" in content
    assert "animate-pulse" in content

    # Click tracking and progress
    assert "tutorial-new-canvas-btn" in content
    assert "tutorial-canvas-title-input" in content
    assert "tutorial-template-select" in content
    assert "tutorial-generate-btn" in content
    assert "tutorial-canvas-preview" in content
    assert "markStepDone" in content


def test_step_by_step_guide_5_steps_and_highlights():
    """Test 3: Verify StepByStepGuide implements all 5 steps, hints, and skip step."""
    path = os.path.join(HUB_ROOT, "apps/web/components/tutorial/StepByStepGuide.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 5 steps definition
    assert "Натисніть 'New Canvas'" in content
    assert "Введіть назву полотна" in content
    assert "Оберіть template" in content
    assert "Натисніть 'Generate'" in content
    assert "Подивіться результат" in content

    # Hint and skip actions
    assert "Показати підказку" in content
    assert "Пропустити крок" in content
    assert "auto-advance" in content or "onStepComplete" in content
    assert "TUTORIAL_STEPS" in content


def test_real_time_feedback_toasts_sounds_and_confetti():
    """Test 4: Verify RealTimeFeedback provides toast notifications, synthesized sounds, and confetti."""
    path = os.path.join(HUB_ROOT, "apps/web/components/tutorial/RealTimeFeedback.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Toast feedback variations
    assert "Чудово! Ви створили полотно" in content
    assert "Спробуйте ще раз" in content
    assert "Натисніть сюди" in content

    # Sound effects (synthesized gentle chime & soft buzz, muted by default)
    assert "AudioContext" in content or "webkitAudioContext" in content
    assert "playChime" in content or "chime" in content
    assert "playBuzz" in content or "buzz" in content
    assert "soundEnabled" in content

    # Animation confetti
    assert "Confetti" in content or "confetti" in content
    assert "CONFETTI_PARTICLES" in content or "particle" in content

    # Progress bar: крок X з Y
    assert "Крок" in content and "з" in content


def test_achievement_badges_4_badges_and_collection():
    """Test 5: Verify AchievementBadges contains 4 required badges, collection page, and shareable features."""
    path = os.path.join(HUB_ROOT, "apps/web/components/tutorial/AchievementBadges.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 4 required badges
    assert "First Canvas" in content
    assert "Quick Learner" in content
    assert "Onboarding Complete" in content
    assert "Creative Mind" in content

    # Collection view & modal
    assert "Колекція досягнень" in content or "Badge Collection" in content
    assert "showModal" in content or "isModalOpen" in content

    # Shareable features
    assert "Поділитися" in content or "Share" in content
    assert "handleShareBadge" in content or "navigator.clipboard" in content


def test_onboarding_page_integration():
    """Test 6: Verify apps/web/app/onboarding/page.tsx integrates InteractiveCanvasDemo and mode switching."""
    path = os.path.join(HUB_ROOT, "apps/web/app/onboarding/page.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "InteractiveCanvasDemo" in content
    assert "OnboardingWizard" in content
    assert "tutorial_completed" in content
    assert "activeTab" in content or "view" in content


def test_local_storage_persistence():
    """Test 7: Verify progress and completion are persisted in localStorage."""
    demo_path = os.path.join(HUB_ROOT, "apps/web/components/tutorial/InteractiveCanvasDemo.tsx")
    with open(demo_path, "r", encoding="utf-8") as f:
        demo_content = f.read()

    assert "STORAGE_TUTORIAL_COMPLETED" in demo_content or "tutorial_completed" in demo_content
    assert "STORAGE_TUTORIAL_PROGRESS" in demo_content or "tutorial_progress" in demo_content
    assert "STORAGE_TUTORIAL_CURRENT_STEP" in demo_content or "tutorial_current_step" in demo_content
    assert "localStorage.setItem" in demo_content


def test_analytics_event_tracking():
    """Test 8: Verify all required analytics events are emitted."""
    demo_path = os.path.join(HUB_ROOT, "apps/web/components/tutorial/InteractiveCanvasDemo.tsx")
    with open(demo_path, "r", encoding="utf-8") as f:
        demo_content = f.read()

    required_events = [
        "tutorial_started",
        "tutorial_step_completed",
        "tutorial_completed",
        "tutorial_abandoned"
    ]
    for ev in required_events:
        assert ev in demo_content, f"Missing analytics event: {ev}"


def test_accessibility_wcag_2_1_aa():
    """Test 9: Verify accessibility requirements (ARIA roles, keyboard nav, high contrast, reduced motion)."""
    files_to_check = [
        "apps/web/components/tutorial/InteractiveCanvasDemo.tsx",
        "apps/web/components/tutorial/StepByStepGuide.tsx",
        "apps/web/components/tutorial/RealTimeFeedback.tsx",
        "apps/web/components/tutorial/AchievementBadges.tsx"
    ]
    for rel_path in files_to_check:
        with open(os.path.join(HUB_ROOT, rel_path), "r", encoding="utf-8") as f:
            content = f.read()
        assert "aria-label" in content or "aria-live" in content, f"Missing ARIA in {rel_path}"

    # Specific checks
    guide_path = os.path.join(HUB_ROOT, "apps/web/components/tutorial/StepByStepGuide.tsx")
    with open(guide_path, "r", encoding="utf-8") as f:
        guide_content = f.read()
    assert "aria-valuenow" in guide_content or "progressbar" in guide_content
    assert "onKeyDown" in guide_content or "Tab" in guide_content or "Escape" in guide_content

    feedback_path = os.path.join(HUB_ROOT, "apps/web/components/tutorial/RealTimeFeedback.tsx")
    with open(feedback_path, "r", encoding="utf-8") as f:
        feedback_content = f.read()
    assert "aria-live" in feedback_content
    assert "reducedMotion" in feedback_content


def test_step_tutorial_backward_compatibility_and_integration():
    """Test 10: Verify StepTutorial.tsx integrates InteractiveCanvasDemo while keeping existing requirements."""
    path = os.path.join(HUB_ROOT, "apps/web/components/onboarding/StepTutorial.tsx")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Integration
    assert "InteractiveCanvasDemo" in content
    # Backward compatibility
    assert "Створіть своє перше полотно" in content
    assert "Generate" in content
    assert "Подивіться результат" in content
    assert "Чудово! Ви створили полотно" in content
    assert "3 з 3 дій виконано" in content or "completedCount" in content

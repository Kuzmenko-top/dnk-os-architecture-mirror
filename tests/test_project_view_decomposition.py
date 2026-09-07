# --- DNK-MRH-HEADER ---
# mrh_id: "tests/test_project_view_decomposition.py"
# purpose: "Regression and isolation test certifying the modular decomposition of God component ProjectView"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_VIEW_DIR = BASE_DIR / "visual_shell" / "open_design" / "apps" / "web" / "src" / "components" / "project-view"
COMPONENTS_DIR = BASE_DIR / "visual_shell" / "open_design" / "apps" / "web" / "src" / "components"
TESTS_COMPONENTS_DIR = BASE_DIR / "visual_shell" / "open_design" / "apps" / "web" / "tests" / "components"


def test_project_view_submodules_exist():
    """Verify that ProjectView modular components exist and have valid MRH headers."""
    expected_files = [
        "layoutUtils.ts",
        "conversationUtils.ts",
        "artifactRecoveryUtils.ts",
        "index.ts",
    ]
    for filename in expected_files:
        filepath = PROJECT_VIEW_DIR / filename
        assert filepath.is_file(), f"Expected modular file {filepath} to exist"
        content = filepath.read_text(encoding="utf-8")
        assert "DNK-MRH-HEADER" in content, f"File {filename} missing DNK-MRH-HEADER"


def test_layout_utils_exports():
    """Verify layoutUtils exports necessary layout calculations."""
    content = (PROJECT_VIEW_DIR / "layoutUtils.ts").read_text(encoding="utf-8")
    expected_symbols = [
        "workspacePanelMinWidthForSplit",
        "maxChatPanelWidthForSplit",
        "clampPreferredChatPanelWidth",
        "clampChatPanelWidth",
        "readSavedChatPanelWidth",
        "saveChatPanelWidth",
        "projectSplitClassName",
        "shouldDefaultCollapseChatForSharedNonOwner",
        "buildQuestionFormKey",
        "projectSplitStyle",
    ]
    for sym in expected_symbols:
        assert f"export function {sym}" in content or f"export const {sym}" in content, f"Missing export {sym} in layoutUtils.ts"


def test_conversation_utils_exports():
    """Verify conversationUtils exports streaming and recovery utilities."""
    content = (PROJECT_VIEW_DIR / "conversationUtils.ts").read_text(encoding="utf-8")
    expected_symbols = [
        "mergeSavedPreviewComment",
        "mergeServerMessageWithLocal",
        "mergeServerMessagesIntoConversation",
        "normalizeConversationMessageOrder",
        "isGenericDaemonDisconnect",
        "isActiveRunStatus",
        "isTerminalRunStatus",
        "isStoppableAssistantMessage",
        "resolveSucceededRunStatus",
        "resolveRetryTarget",
        "createBufferedTextUpdates",
    ]
    for sym in expected_symbols:
        assert f"export function {sym}" in content or f"export const {sym}" in content, f"Missing export {sym} in conversationUtils.ts"


def test_artifact_recovery_utils_exports():
    """Verify artifactRecoveryUtils exports file resolution and recovery utilities."""
    content = (PROJECT_VIEW_DIR / "artifactRecoveryUtils.ts").read_text(encoding="utf-8")
    expected_symbols = [
        "computeProducedFiles",
        "computeTraceObjectFiles",
        "findTouchedProjectFile",
        "resolveAgentTouchedFileNames",
        "mergeRecoveredArtifact",
        "mergeRecoveredTraceObjectFile",
        "extractTouchedFilePathsFromEvents",
    ]
    for sym in expected_symbols:
        assert f"export function {sym}" in content or f"export const {sym}" in content, f"Missing export {sym} in artifactRecoveryUtils.ts"


def test_consumers_decoupled_from_god_component():
    """Verify that key consumers import from the modular project-view package instead of ProjectView God component."""
    use_conv_chat = COMPONENTS_DIR / "workspace" / "useConversationChat.ts"
    assert use_conv_chat.is_file()
    use_conv_content = use_conv_chat.read_text(encoding="utf-8")
    assert "from '../project-view'" in use_conv_content, "useConversationChat.ts should import from '../project-view'"
    assert "from '../ProjectView'" not in use_conv_content, "useConversationChat.ts should not import from '../ProjectView'"

    file_workspace_test = TESTS_COMPONENTS_DIR / "FileWorkspace.test.tsx"
    assert "from '../../src/components/project-view'" in file_workspace_test.read_text(encoding="utf-8")

    buffered_test = TESTS_COMPONENTS_DIR / "buffered-text-pending.test.tsx"
    assert "from '../../src/components/project-view'" in buffered_test.read_text(encoding="utf-8")

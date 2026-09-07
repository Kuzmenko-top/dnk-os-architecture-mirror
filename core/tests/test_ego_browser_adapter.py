# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_ego_browser_adapter.py"
# purpose: "Unit tests for the ego-lite adapter (DNKEgoBrowserAdapter) with mocked subprocess"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from unittest.mock import MagicMock, patch
from core.adapters.ego_browser_adapter import DNKEgoBrowserAdapter

@pytest.fixture
def mock_popen():
    with patch("subprocess.Popen") as mock:
        yield mock

def test_start_stop(mock_popen):
    mock_process = MagicMock()
    mock_popen.return_value = mock_process
    
    adapter = DNKEgoBrowserAdapter(ego_binary="ego-browser")
    adapter.start()
    
    mock_popen.assert_called_once_with(
        ["ego-browser", "--stdin"],
        stdin=-1, # subprocess.PIPE
        stdout=-1,
        stderr=-1
    )
    assert adapter.process == mock_process
    
    adapter.stop()
    mock_process.terminate.assert_called_once()
    mock_process.wait.assert_called_once()
    assert adapter.process is None

def test_send_command(mock_popen):
    mock_process = MagicMock()
    mock_popen.return_value = mock_process
    
    adapter = DNKEgoBrowserAdapter()
    adapter.start()
    adapter.send_command("click @12")
    
    mock_process.stdin.write.assert_called_with(b"click @12\n")
    mock_process.stdin.flush.assert_called_once()

def test_get_output(mock_popen):
    mock_process = MagicMock()
    mock_process.communicate.return_value = (b"output data", b"")
    mock_popen.return_value = mock_process
    
    adapter = DNKEgoBrowserAdapter()
    adapter.start()
    out = adapter.get_output()
    
    assert out == "output data"
    mock_process.communicate.assert_called_once()

def test_task_spaces(mock_popen):
    mock_process = MagicMock()
    mock_process.communicate.return_value = (b'[{"id": 1, "name": "space-1", "ownership": "agent"}]', b"")
    mock_popen.return_value = mock_process
    
    adapter = DNKEgoBrowserAdapter()
    spaces = adapter.list_task_spaces()
    
    assert len(spaces) == 1
    assert spaces[0]["name"] == "space-1"
    assert adapter.is_agent_owned(spaces[0]["ownership"]) is True
    
    found = adapter.find_task_space("space-1")
    assert found is not None
    assert found["id"] == 1

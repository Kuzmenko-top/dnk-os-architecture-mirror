# --- DNK-MRH-HEADER ---
# mrh_id: "tests/session/test_session.py"
# purpose: "Unit and integration tests for SessionManager and session API endpoints"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
import pytest

from dnk_os.core.agent import app, session_manager
from dnk_os.core.session import SessionManager


class TestSessionManager:
    """Test suite for SessionManager unit logic."""

    def test_init(self):
        """Test initialization."""
        manager = SessionManager(redis_url="redis://localhost:6379", session_ttl_hours=48, key_prefix="test:session:")
        assert manager is not None
        assert manager.session_ttl_hours == 48
        assert manager.key_prefix == "test:session:"

    def test_create_session(self):
        """Test session creation."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        manager.redis.setex = MagicMock()

        session_id = manager.create_session(user_id="user_123", metadata={"role": "admin"})
        assert session_id is not None
        assert len(session_id) == 36  # Valid UUID4 length
        assert manager.redis.setex.called
        call_args = manager.redis.setex.call_args[0]
        assert call_args[0] == f"dnk:session:{session_id}"
        assert call_args[1] == 24 * 3600
        saved_data = json.loads(call_args[2])
        assert saved_data["user_id"] == "user_123"
        assert saved_data["metadata"] == {"role": "admin"}
        assert saved_data["task_count"] == 0
        assert saved_data["status"] == "active"

    def test_get_session(self):
        """Test session retrieval."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        mock_data = json.dumps({"session_id": "test_id", "user_id": "u1", "status": "active", "task_count": 2})
        manager.redis.get = MagicMock(return_value=mock_data.encode("utf-8"))
        manager.redis.setex = MagicMock()

        session = manager.get_session(session_id="test_id")
        assert session is not None
        assert session["session_id"] == "test_id"
        assert session["user_id"] == "u1"
        assert manager.redis.setex.called

    def test_get_session_not_found(self):
        """Test session retrieval when key does not exist."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        manager.redis.get = MagicMock(return_value=None)

        session = manager.get_session(session_id="missing_id")
        assert session is None

    def test_update_session(self):
        """Test session update."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        mock_data = json.dumps({"session_id": "test_id", "status": "active", "task_count": 0})
        manager.redis.get = MagicMock(return_value=mock_data)
        manager.redis.setex = MagicMock()

        success = manager.update_session(session_id="test_id", updates={"status": "paused", "task_count": 3})
        assert success is True
        assert manager.redis.setex.called
        call_args = manager.redis.setex.call_args[0]
        updated_data = json.loads(call_args[2])
        assert updated_data["status"] == "paused"
        assert updated_data["task_count"] == 3

    def test_update_session_not_found(self):
        """Test session update when session is missing."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        manager.redis.get = MagicMock(return_value=None)

        success = manager.update_session(session_id="missing_id", updates={"status": "paused"})
        assert success is False

    def test_delete_session(self):
        """Test session deletion."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        manager.redis.delete = MagicMock(return_value=1)

        success = manager.delete_session(session_id="test_id")
        assert success is True
        manager.redis.delete.assert_called_once_with("dnk:session:test_id")

    def test_increment_task_count(self):
        """Test task count increment."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        mock_data = json.dumps({"session_id": "test_id", "task_count": 5})
        manager.redis.get = MagicMock(return_value=mock_data)
        manager.redis.setex = MagicMock()

        count = manager.increment_task_count(session_id="test_id")
        assert count == 6

    def test_increment_task_count_not_found(self):
        """Test task count increment on missing session."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        manager.redis.get = MagicMock(return_value=None)

        count = manager.increment_task_count(session_id="missing_id")
        assert count == 0

    def test_list_sessions(self):
        """Test session listing."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        manager.redis.keys = MagicMock(return_value=[b"dnk:session:s1", b"dnk:session:s2"])
        
        def mock_get(key):
            if key == "dnk:session:s1":
                return json.dumps({"session_id": "s1", "user_id": "user_1"}).encode("utf-8")
            return json.dumps({"session_id": "s2", "user_id": "user_2"}).encode("utf-8")

        manager.redis.get = MagicMock(side_effect=mock_get)

        sessions = manager.list_sessions(limit=10)
        assert len(sessions) == 2

        filtered_sessions = manager.list_sessions(user_id="user_1")
        assert len(filtered_sessions) == 1
        assert filtered_sessions[0]["session_id"] == "s1"

    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        manager.redis.keys = MagicMock(return_value=[b"dnk:session:s1", b"dnk:session:s2"])
        manager.redis.ttl = MagicMock(side_effect=[-2, 3600])

        cleaned = manager.cleanup_expired_sessions()
        assert cleaned == 1

    def test_get_session_stats(self):
        """Test session statistics aggregation."""
        manager = SessionManager(redis_url="redis://localhost:6379")
        manager.redis = MagicMock()
        manager.redis.keys = MagicMock(return_value=[b"dnk:session:s1", b"dnk:session:s2"])
        
        def mock_get(key):
            if "s1" in str(key):
                return json.dumps({"session_id": "s1", "status": "active", "task_count": 4})
            return json.dumps({"session_id": "s2", "status": "inactive", "task_count": 6})

        manager.redis.get = MagicMock(side_effect=mock_get)

        stats = manager.get_session_stats()
        assert stats["total_sessions"] == 2
        assert stats["active_sessions"] == 1
        assert stats["total_tasks"] == 10
        assert stats["avg_tasks_per_session"] == 5.0
        assert "timestamp" in stats


class TestSessionAPIEndpoints:
    """Test suite for FastAPI session endpoints."""

    def setup_method(self):
        """Mock Redis for global session_manager in agent."""
        session_manager.redis = MagicMock()
        self.client = TestClient(app)

    def test_api_create_session(self):
        """Test POST /session/create endpoint."""
        session_manager.redis.setex = MagicMock()
        response = self.client.post("/session/create", json={"user_id": "usr_99", "metadata": {"env": "prod"}})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "created"

    def test_api_get_session(self):
        """Test GET /session/{session_id} endpoint."""
        mock_session = {"session_id": "test_session_1", "user_id": "usr_1", "status": "active"}
        session_manager.redis.get = MagicMock(return_value=json.dumps(mock_session).encode("utf-8"))
        session_manager.redis.setex = MagicMock()

        response = self.client.get("/session/test_session_1")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test_session_1"

    def test_api_get_session_not_found(self):
        """Test GET /session/{session_id} 404 response."""
        session_manager.redis.get = MagicMock(return_value=None)
        response = self.client.get("/session/non_existent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Session not found"

    def test_api_update_session(self):
        """Test POST /session/{session_id}/update endpoint."""
        mock_session = {"session_id": "test_session_1", "status": "active"}
        session_manager.redis.get = MagicMock(return_value=json.dumps(mock_session))
        session_manager.redis.setex = MagicMock()

        response = self.client.post("/session/test_session_1/update", json={"status": "completed"})
        assert response.status_code == 200

    def test_api_delete_session(self):
        """Test DELETE /session/{session_id} endpoint."""
        session_manager.redis.delete = MagicMock(return_value=1)
        response = self.client.delete("/session/test_session_1")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["session_id"] == "test_session_1"

    def test_api_list_sessions(self):
        """Test GET /sessions endpoint."""
        session_manager.redis.keys = MagicMock(return_value=[b"dnk:session:s1"])
        session_manager.redis.get = MagicMock(return_value=json.dumps({"session_id": "s1", "user_id": "u1"}))

        response = self.client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["sessions"]) == 1

    def test_api_session_stats(self):
        """Test GET /session/stats endpoint."""
        session_manager.redis.keys = MagicMock(return_value=[b"dnk:session:s1"])
        session_manager.redis.get = MagicMock(return_value=json.dumps({"session_id": "s1", "status": "active", "task_count": 2}))

        response = self.client.get("/session/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sessions"] == 1
        assert data["active_sessions"] == 1
        assert data["total_tasks"] == 2

    def test_api_cleanup_sessions(self):
        """Test POST /session/cleanup endpoint."""
        session_manager.redis.keys = MagicMock(return_value=[b"dnk:session:s1"])
        session_manager.redis.ttl = MagicMock(return_value=-2)

        response = self.client.post("/session/cleanup")
        assert response.status_code == 200
        assert response.json()["cleaned_sessions"] == 1

# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_checkpointer.py"
# purpose: "Test suite for checkpointer persistence layer"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from dnk_os.core.checkpointer import (
    MemoryCheckpointer,
    SQLiteCheckpointer,
    RedisCheckpointer,
    create_checkpointer
)

class TestMemoryCheckpointer:
    """Test suite for MemoryCheckpointer."""
    
    def test_init(self):
        """Test initialization."""
        chkpt = MemoryCheckpointer()
        assert chkpt is not None
    
    def test_put_get(self):
        """Test put and get."""
        chkpt = MemoryCheckpointer()
        checkpoint = {"state": "active", "messages": ["Hello"]}
        checkpoint_id = chkpt.put(thread_id="thread_1", checkpoint=checkpoint, checkpoint_ns="ns1")
        assert checkpoint_id is not None
        
        result = chkpt.get(thread_id="thread_1", checkpoint_ns="ns1")
        assert result is not None
        assert result["state"] == "active"
        assert result["id"] == checkpoint_id
        
        # Test get non-existent
        assert chkpt.get(thread_id="thread_1", checkpoint_ns="nonexistent") is None
    
    def test_list(self):
        """Test list checkpoints."""
        chkpt = MemoryCheckpointer()
        chkpt.put(thread_id="thread_1", checkpoint={"state": "1"}, checkpoint_ns="ns1")
        chkpt.put(thread_id="thread_1", checkpoint={"state": "2"}, checkpoint_ns="ns2")
        chkpt.put(thread_id="thread_2", checkpoint={"state": "3"}, checkpoint_ns="ns1")
        
        results = chkpt.list(thread_id="thread_1", limit=10)
        assert len(results) == 2
        
        results_limited = chkpt.list(thread_id="thread_1", limit=1)
        assert len(results_limited) == 1
    
    def test_delete(self):
        """Test delete checkpoint."""
        chkpt = MemoryCheckpointer()
        checkpoint_id = chkpt.put(thread_id="thread_1", checkpoint={"state": "active"}, checkpoint_ns="ns1")
        
        deleted = chkpt.delete(thread_id="thread_1", checkpoint_id=checkpoint_id)
        assert deleted is True
        
        result = chkpt.get(thread_id="thread_1", checkpoint_ns="ns1")
        assert result is None
        
        # Test delete non-existent
        assert chkpt.delete(thread_id="thread_1", checkpoint_id="fake_id") is False


class TestSQLiteCheckpointer:
    """Test suite for SQLiteCheckpointer."""
    
    def test_init(self, tmp_path):
        """Test initialization."""
        db_path = tmp_path / "test.db"
        chkpt = SQLiteCheckpointer(db_path=str(db_path))
        assert chkpt is not None
    
    def test_put_get(self, tmp_path):
        """Test put and get."""
        db_path = tmp_path / "test.db"
        chkpt = SQLiteCheckpointer(db_path=str(db_path))
        checkpoint = {"state": "active", "messages": ["Hello"]}
        checkpoint_id = chkpt.put(thread_id="thread_1", checkpoint=checkpoint, checkpoint_ns="ns1")
        assert checkpoint_id is not None
        
        result = chkpt.get(thread_id="thread_1", checkpoint_ns="ns1")
        assert result is not None
        assert result["state"] == "active"
        assert result["id"] == checkpoint_id
        
        assert chkpt.get(thread_id="thread_1", checkpoint_ns="none") is None
    
    def test_list(self, tmp_path):
        """Test list checkpoints."""
        db_path = tmp_path / "test.db"
        chkpt = SQLiteCheckpointer(db_path=str(db_path))
        chkpt.put(thread_id="thread_1", checkpoint={"state": "1"}, checkpoint_ns="ns1")
        chkpt.put(thread_id="thread_1", checkpoint={"state": "2"}, checkpoint_ns="ns2")
        
        results = chkpt.list(thread_id="thread_1", limit=10)
        assert len(results) == 2
        
        results_limited = chkpt.list(thread_id="thread_1", limit=1)
        assert len(results_limited) == 1
    
    def test_delete(self, tmp_path):
        """Test delete checkpoint."""
        db_path = tmp_path / "test.db"
        chkpt = SQLiteCheckpointer(db_path=str(db_path))
        checkpoint_id = chkpt.put(thread_id="thread_1", checkpoint={"state": "active"})
        
        deleted = chkpt.delete(thread_id="thread_1", checkpoint_id=checkpoint_id)
        assert deleted is True
        
        result = chkpt.get(thread_id="thread_1")
        assert result is None
        
        # Test delete non-existent
        assert chkpt.delete(thread_id="thread_1", checkpoint_id="fake_id") is False


class MockRedis:
    """Mock Redis client for testing."""
    def __init__(self):
        self.store = {}
    
    def get(self, key):
        return self.store.get(key)
    
    def set(self, key, value):
        self.store[key] = value.encode("utf-8") if isinstance(value, str) else value
    
    def keys(self, pattern):
        prefix = pattern.replace("*", "")
        return [k for k in self.store.keys() if k.startswith(prefix)]
    
    def delete(self, key):
        if key in self.store:
            del self.store[key]
            return 1
        return 0


class TestRedisCheckpointer:
    """Test suite for RedisCheckpointer."""
    
    def test_init(self):
        """Test initialization with mock redis client."""
        chkpt = RedisCheckpointer(redis_client=MockRedis())
        assert chkpt is not None
        
    def test_init_real_redis_import(self, monkeypatch):
        """Test import logic in init."""
        class FakeRedisModule:
            @staticmethod
            def from_url(url):
                return MockRedis()
        import sys
        monkeypatch.setitem(sys.modules, 'redis', FakeRedisModule)
        chkpt = RedisCheckpointer(redis_url="redis://fake")
        assert chkpt is not None
    
    def test_put_get(self):
        """Test put and get."""
        chkpt = RedisCheckpointer(redis_client=MockRedis())
        checkpoint = {"state": "active", "messages": ["Hello"]}
        checkpoint_id = chkpt.put(thread_id="thread_1", checkpoint=checkpoint, checkpoint_ns="ns1")
        assert checkpoint_id is not None
        
        result = chkpt.get(thread_id="thread_1", checkpoint_ns="ns1")
        assert result is not None
        assert result["state"] == "active"
        assert result["id"] == checkpoint_id
        
        assert chkpt.get(thread_id="thread_1", checkpoint_ns="none") is None
        
        # Test string decoding fallback
        mock_redis = chkpt.redis
        getattr(mock_redis, "store")[f"{chkpt.key_prefix}thread_1:ns1"] = json.dumps({"state": "string_test", "id": "123"})
        result_str = chkpt.get(thread_id="thread_1", checkpoint_ns="ns1")
        assert result_str["state"] == "string_test"
    
    def test_list(self):
        """Test list checkpoints."""
        chkpt = RedisCheckpointer(redis_client=MockRedis())
        chkpt.put(thread_id="thread_1", checkpoint={"state": "1"}, checkpoint_ns="ns1")
        chkpt.put(thread_id="thread_1", checkpoint={"state": "2"}, checkpoint_ns="ns2")
        
        results = chkpt.list(thread_id="thread_1", limit=10)
        assert len(results) == 2
        
        results_limited = chkpt.list(thread_id="thread_1", limit=1)
        assert len(results_limited) == 1
        
        # Test string decoding in list
        mock_redis = chkpt.redis
        getattr(mock_redis, "store")[f"{chkpt.key_prefix}thread_1:ns3"] = json.dumps({"state": "string_list_test", "id": "123"})
        results_str = chkpt.list(thread_id="thread_1", limit=10)
        assert any(r.get("state") == "string_list_test" for r in results_str)
    
    def test_delete(self):
        """Test delete checkpoint."""
        chkpt = RedisCheckpointer(redis_client=MockRedis())
        checkpoint_id = chkpt.put(thread_id="thread_1", checkpoint={"state": "active"}, checkpoint_ns="ns1")
        
        deleted = chkpt.delete(thread_id="thread_1", checkpoint_id=checkpoint_id)
        assert deleted is True
        
        result = chkpt.get(thread_id="thread_1", checkpoint_ns="ns1")
        assert result is None
        
        # Test string decoding in delete
        checkpoint_id2 = chkpt.put(thread_id="thread_2", checkpoint={"state": "active2"}, checkpoint_ns="ns2")
        mock_redis = chkpt.redis
        getattr(mock_redis, "store")[f"{chkpt.key_prefix}thread_2:ns2"] = json.dumps({"state": "active2", "id": checkpoint_id2})
        deleted2 = chkpt.delete(thread_id="thread_2", checkpoint_id=checkpoint_id2)
        assert deleted2 is True
        
        # Test delete non-existent
        assert chkpt.delete(thread_id="thread_1", checkpoint_id="fake_id") is False


class TestCheckpointerFactory:
    """Test suite for checkpointer factory."""
    
    def test_create_memory(self):
        """Test create memory checkpointer."""
        chkpt = create_checkpointer(backend="memory")
        assert isinstance(chkpt, MemoryCheckpointer)
    
    def test_create_sqlite(self, tmp_path):
        """Test create SQLite checkpointer."""
        db_path = tmp_path / "test.db"
        chkpt = create_checkpointer(backend="sqlite", db_path=str(db_path))
        assert isinstance(chkpt, SQLiteCheckpointer)
        
    def test_create_redis(self):
        """Test create Redis checkpointer."""
        chkpt = create_checkpointer(backend="redis", redis_client=MockRedis())
        assert isinstance(chkpt, RedisCheckpointer)
    
    def test_create_invalid(self):
        """Test create invalid backend."""
        with pytest.raises(ValueError, match="Unknown backend"):
            create_checkpointer(backend="invalid")

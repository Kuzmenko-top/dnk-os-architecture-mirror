# --- DNK-MRH-HEADER ---
# mrh_id: "tests/streaming/test_streaming.py"
# purpose: "Unit and integration tests for StreamingService and SSE endpoints"
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
from fastapi.testclient import TestClient

from dnk_os.core.streaming import StreamingService
from dnk_os.core.agent import app


class TestStreamingService:
    """Test suite for StreamingService."""

    @pytest.mark.asyncio
    async def test_stream_tokens(self):
        """Test token streaming."""
        service = StreamingService()
        text = "Hello world this is a test"

        events = []
        async for event in service.stream_tokens(text, tokens_per_second=1000):
            events.append(event)

        assert len(events) > 0
        assert "token" in events[0]
        
        # Verify first event parsing
        first_payload = json.loads(events[0].replace("data: ", "").strip())
        assert first_payload["type"] == "token"
        assert first_payload["data"]["token"] == "Hello"
        assert first_payload["data"]["index"] == 0
        assert first_payload["data"]["total"] == 6

        # Verify completion event
        last_payload = json.loads(events[-1].replace("data: ", "").strip())
        assert last_payload["type"] == "completion"
        assert last_payload["data"]["total_tokens"] == 6
        assert last_payload["data"]["status"] == "complete"

    @pytest.mark.asyncio
    async def test_stream_tokens_empty(self):
        """Test token streaming with empty string."""
        service = StreamingService()
        events = []
        async for event in service.stream_tokens("", tokens_per_second=1000):
            events.append(event)

        assert len(events) == 1
        payload = json.loads(events[0].replace("data: ", "").strip())
        assert payload["type"] == "completion"
        assert payload["data"]["total_tokens"] == 0

    @pytest.mark.asyncio
    async def test_stream_task_execution(self):
        """Test task execution streaming."""
        service = StreamingService()

        events = []
        async for event in service.stream_task_execution(
            task_id="task_123",
            worker_name="Герич",
            task_description="Test task",
            sleep_interval=0.0
        ):
            events.append(event)

        # Parse all event payloads
        payloads = [json.loads(e.replace("data: ", "").strip()) for e in events if e.strip()]
        event_types = [p.get("type") for p in payloads]

        assert "start" in event_types
        assert "progress" in event_types
        assert "completion" in event_types

        start_event = payloads[0]
        assert start_event["type"] == "start"
        assert start_event["data"]["task_id"] == "task_123"
        assert start_event["data"]["worker"] == "Герич"

        completion_event = payloads[-1]
        assert completion_event["type"] == "completion"
        assert completion_event["data"]["status"] == "completed"
        assert completion_event["data"]["progress_percent"] == 100

    @pytest.mark.asyncio
    async def test_stream_worker_output_tokens(self):
        """Test worker output streaming (token mode)."""
        service = StreamingService()
        output = "This is worker output"

        events = []
        async for event in service.stream_worker_output(
            worker_name="Герич",
            output=output,
            stream_mode="tokens",
            sleep_interval=0.0
        ):
            events.append(event)

        assert len(events) > 0
        first_payload = json.loads(events[0].replace("data: ", "").strip())
        assert first_payload["type"] == "token"

    @pytest.mark.asyncio
    async def test_stream_worker_output_words(self):
        """Test worker output streaming (word mode)."""
        service = StreamingService()
        output = "This is worker output"

        events = []
        async for event in service.stream_worker_output(
            worker_name="Герич",
            output=output,
            stream_mode="words",
            sleep_interval=0.0
        ):
            events.append(event)

        assert len(events) == 5  # 4 words + 1 completion
        payloads = [json.loads(e.replace("data: ", "").strip()) for e in events if e.strip()]
        assert payloads[0]["type"] == "word"
        assert payloads[0]["data"]["word"] == "This"
        assert payloads[-1]["type"] == "completion"
        assert payloads[-1]["data"]["worker"] == "Герич"

    @pytest.mark.asyncio
    async def test_stream_worker_output_lines(self):
        """Test worker output streaming (line mode)."""
        service = StreamingService()
        output = "Line 1\nLine 2\nLine 3"

        events = []
        async for event in service.stream_worker_output(
            worker_name="Герич",
            output=output,
            stream_mode="lines",
            sleep_interval=0.0
        ):
            events.append(event)

        assert len(events) == 4  # 3 lines + 1 completion
        payloads = [json.loads(e.replace("data: ", "").strip()) for e in events if e.strip()]
        assert payloads[0]["type"] == "line"
        assert payloads[0]["data"]["line"] == "Line 1"
        assert payloads[-1]["type"] == "completion"

    def test_create_sse_response(self):
        """Test SSE response creation."""
        service = StreamingService()

        async def dummy_generator():
            yield "data: test\n\n"

        response = service.create_sse_response(dummy_generator())
        assert response is not None
        assert response.media_type == "text/event-stream"
        assert response.headers["Cache-Control"] == "no-cache"
        assert response.headers["Connection"] == "keep-alive"
        assert response.headers["X-Accel-Buffering"] == "no"


class TestStreamingEndpoints:
    """Test suite for FastAPI SSE streaming endpoints."""

    def test_stream_example_endpoint(self):
        """Test GET /stream/example."""
        client = TestClient(app)
        response = client.get("/stream/example")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        content = response.text
        assert "data: " in content
        assert "completion" in content

    def test_stream_task_endpoint(self):
        """Test GET /stream/task/{task_id}."""
        client = TestClient(app)
        response = client.get("/stream/task/test-task-42?worker=Герич")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        content = response.text
        assert "test-task-42" in content
        assert "started" in content
        assert "completed" in content

    def test_execute_stream_endpoint(self):
        """Test POST /execute/stream."""
        client = TestClient(app)
        response = client.post("/execute/stream", json={"task": "Process analytics pipeline"})
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        content = response.text
        assert "data: " in content
        assert "token" in content
        assert "completion" in content

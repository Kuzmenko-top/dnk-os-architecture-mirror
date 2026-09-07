# --- DNK-MRH-HEADER ---
# mrh_id: "examples/streaming_client.py"
# purpose: "Client example for consuming SSE streaming endpoints from DNK OS Core API"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import requests


def stream_task_execution(task_id: str, api_url: str = "http://localhost:8000"):
    """
    Stream task execution from DNK OS API.
    
    Args:
        task_id: Task identifier
        api_url: API URL
    """
    url = f"{api_url}/stream/task/{task_id}"
    
    with requests.get(url, stream=True) as response:
        for line in response.iter_lines():
            if line:
                # Parse SSE event
                if line.startswith(b"data: "):
                    event = json.loads(line[6:].decode())
                    event_type = event.get("type")
                    data = event.get("data", {})
                    
                    if event_type == "start":
                        print(f"🚀 Task started: {data.get('description')}")
                    elif event_type == "progress":
                        progress = data.get("progress_percent", 0)
                        print(f"📊 Progress: {progress}%")
                    elif event_type == "completion":
                        print("✅ Task completed!")
                        if "result" in data:
                            print(f"Result: {data['result']}")
                    elif event_type == "token":
                        token = data.get("token", "")
                        print(token, end=" ", flush=True)


if __name__ == "__main__":
    stream_task_execution(task_id="task_123")

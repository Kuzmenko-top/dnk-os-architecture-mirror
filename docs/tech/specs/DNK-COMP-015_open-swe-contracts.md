# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-015_open-swe-contracts.md"
# purpose: "Component Contracts for open-swe Dispatcher, Scheduler, and Sandbox Components"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-14"
# --- END DNK-MRH-HEADER ---

# 📄 DNK Component Contracts: open-swe Interfaces (DNK-COMP-015)

Data structures and interface specifications for open-swe core primitives in `DNK_HUB`.

---

## 1. Data Contracts & Schemas

### 1.1 `SWETaskPayload`
```python
class SWETaskPayload(BaseModel):
    task_id: str
    issue_description: str
    repository_path: str
    target_files: List[str]
    context_files: List[str]
    max_retries: int = 3
```

### 1.2 `SWEPatchResult`
```python
class SWEPatchResult(BaseModel):
    task_id: str
    status: str  # "success", "failed", "max_retries_exceeded"
    applied_patches: List[str]
    test_output: str
    error_summary: Optional[str] = None
    duration_ms: float
```

---

## 2. Interface Contracts

### 2.1 `SWEDispatcherPort`
```python
class SWEDispatcherPort(ABC):
    @abstractmethod
    def pack_context(self, repository_path: str, issue_text: str) -> SWETaskPayload:
        pass

    @abstractmethod
    def dispatch_task(self, payload: SWETaskPayload) -> str:
        pass
```

### 2.2 `SWESchedulerPort`
```python
class SWESchedulerPort(ABC):
    @abstractmethod
    def enqueue(self, task: SWETaskPayload) -> str:
        pass

    @abstractmethod
    def poll_status(self, job_id: str) -> Dict[str, Any]:
        pass
```

### 2.3 `SWESandboxRuntimePort`
```python
class SWESandboxRuntimePort(ABC):
    @abstractmethod
    def execute_test(self, container_image: str, command: str, timeout: int = 300) -> Dict[str, Any]:
        pass
```

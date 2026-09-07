# 🗃️ Component Inventory & Interfaces: Isolated FS Contracts
# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-COMP-002_isolated-fs-contracts.md"
# purpose: "Establish Type-Safe Interfaces and Error Contracts for Isolated Filesystems."
# author: "Maxim"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

## 📌 1. Python Interfaces (Pydantic / Dataclasses)

The Python implementation enforces strict Pydantic models for request/response serialization and interface contracts.

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from abc import ABC, abstractmethod
import os

class SandboxFileMetadata(BaseModel):
    path: str = Field(..., description="Relative path within the isolated sandbox workspace")
    size_bytes: int = Field(..., description="File size in bytes")
    is_directory: bool = Field(..., description="True if the path refers to a folder")
    modified_at: float = Field(..., description="Epoch timestamp of last file modification")

class SandboxExecResult(BaseModel):
    exit_code: int = Field(..., description="Unix exit code of the executed isolated command")
    stdout: str = Field(..., description="Captured standard output stream")
    stderr: str = Field(..., description="Captured error stream")
    duration_seconds: float = Field(..., description="Time taken to execute")

# Contract-only interface. Implementations: DNKDockerSandboxFS, DNKLocalDevFS.
class DNKIsolatedFileSystem(ABC):
    root_boundary: str

    @abstractmethod
    def read_file(self, path: str) -> str:
        """
        Read the contents of a file within the sandbox root boundary.
        Raises PathTraversalError if the path attempts to escape the root boundary.
        """
        ...

    @abstractmethod
    def write_file(self, path: str, content: str) -> None:
        """
        Write content to a file within the sandbox root boundary.
        Raises PathTraversalError if the path attempts to escape the root boundary.
        """
        ...

    @abstractmethod
    def list_dir(self, path: str) -> List[SandboxFileMetadata]:
        """
        Lists all files and subdirectories at the given path.
        """
        ...

    @abstractmethod
    def exec_isolated(self, command: str, args: List[str], timeout_seconds: int = 30) -> SandboxExecResult:
        """
        Executes a binary or bash command inside the sandbox runner container.
        Raises ExecutionTimeoutError if the execution exceeds the timeout.
        """
        ...
```

---

## 💻 2. TypeScript Interfaces (TS-contracts)

The TypeScript interfaces are aligned with the Next.js and frontend canvas dashboards (`dnk_os_frontend` and TMA components).

```typescript
export interface SandboxFileMetadata {
  path: string;
  sizeBytes: number;
  isDirectory: boolean;
  modifiedAt: number; // epoch milliseconds
}

export interface SandboxExecResult {
  exitCode: number;
  stdout: string;
  stderr: string;
  durationSeconds: number;
}

export interface DNKIsolatedFileSystem {
  readonly rootBoundary: string;

  /**
   * Reads file content as UTF-8.
   * @throws {PathTraversalError} if path escapes rootBoundary
   */
  readFile(path: string): Promise<string>;

  /**
   * Writes file content to the target sandbox path.
   * @throws {PathTraversalError} if path escapes rootBoundary
   */
  writeFile(path: string, content: string): Promise<void>;

  /**
   * Lists sandbox directory items.
   */
  listDir(path: string): Promise<SandboxFileMetadata[]>;

  /**
   * Executes an isolated command in the sandbox container.
   * @throws {ExecutionTimeoutError} if command runs longer than timeoutSeconds
   */
  execIsolated(
    command: string, 
    args: string[], 
    timeoutSeconds?: number
  ): Promise<SandboxExecResult>;
}
```

---

## 🚨 3. Exception & Error Definitions

To ensure deterministic error handling across language boundaries, we define specialized exception types:

### `PathTraversalError`
- **Cause:** Attempting to access a file path that, when normalized, resolves outside the scope of `root_boundary`.
- **Python Signature:** `class PathTraversalError(ValueError): ...`
- **JSON Error Representation:**
  ```json
  {
    "error_class": "PathTraversalError",
    "message": "Access denied: Path resolves outside of sandbox root boundary.",
    "attempted_path": "../../etc/passwd",
    "normalized_boundary": "${PROJECT_ROOT:-.}/sandbox/workspace"
  }
  ```

### `ExecutionTimeoutError`
- **Cause:** The command execution within the isolated container exceeded the pre-allocated execution threshold.
- **Python Signature:** `class ExecutionTimeoutError(TimeoutError): ...`
- **JSON Error Representation:**
  ```json
  {
    "error_class": "ExecutionTimeoutError",
    "message": "Process terminated: Execution limit of 30 seconds exceeded.",
    "command": "python -c 'import time; time.sleep(60)'",
    "timeout_seconds": 30
  }
  ```

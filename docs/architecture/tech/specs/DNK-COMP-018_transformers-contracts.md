# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-018_transformers-contracts.md"
# purpose: "Component Contracts for HuggingFace Transformers Architecture Primitives in DNK OS"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

# 📄 DNK Component Contracts: Transformers Interfaces (DNK-COMP-018)

Data structures and interface specifications for HuggingFace Transformers core primitives in `DNK_HUB`.

---

## 1. Data Contracts & Schemas

### 1.1 `TransformersModelConfig`
```python
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class TransformersModelConfig(BaseModel):
    model_name_or_path: str = Field(..., description="Model identifier or local checkpoint path")
    architectures: List[str] = Field(default_factory=list, description="Model architecture type list")
    hidden_size: int = Field(default=768, description="Hidden state dimension")
    num_attention_heads: int = Field(default=12, description="Number of attention heads")
    num_hidden_layers: int = Field(default=12, description="Number of hidden layers")
    vocab_size: int = Field(default=30522, description="Tokenizer vocabulary size")
    torch_dtype: Optional[str] = Field(default="float32", description="PyTorch tensor dtype")
    extra_params: Dict[str, Any] = Field(default_factory=dict, description="Additional hyperparameter metadata")
```

### 1.2 `TokenizerEncodingResult`
```python
class TokenizerEncodingResult(BaseModel):
    input_ids: List[int] = Field(..., description="Token ID sequence")
    attention_mask: List[int] = Field(..., description="Attention mask binary sequence")
    token_type_ids: Optional[List[int]] = Field(default=None, description="Segment token type IDs")
    offset_mapping: Optional[List[tuple]] = Field(default=None, description="Character offset bounds")
    tokens: List[str] = Field(default_factory=list, description="Raw token strings")
```

### 1.3 `PipelineRequest` & `PipelineResponse`
```python
class PipelineRequest(BaseModel):
    task: str = Field(..., description="Task name e.g. text-generation, embeddings, classification")
    inputs: Any = Field(..., description="Input text or batch of texts")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Generation / inference parameters")

class PipelineResponse(BaseModel):
    task: str
    outputs: Any = Field(..., description="Pipeline execution output")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")
    model_id: str
```

---

## 2. Interface Contracts

### 2.1 `TransformersTokenizerPort`
```python
from abc import ABC, abstractmethod

class TransformersTokenizerPort(ABC):
    @abstractmethod
    def encode(self, text: str, max_length: int = 512, truncation: bool = True) -> TokenizerEncodingResult:
        ...

    @abstractmethod
    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        ...
```

### 2.2 `TransformersModelPort`
```python
class TransformersModelPort(ABC):
    @abstractmethod
    def forward(self, input_ids: List[int], attention_mask: Optional[List[int]] = None) -> Any:
        ...

    @abstractmethod
    def get_config(self) -> TransformersModelConfig:
        ...
```

### 2.3 `TransformersPipelinePort`
```python
class TransformersPipelinePort(ABC):
    @abstractmethod
    def run_pipeline(self, request: PipelineRequest) -> PipelineResponse:
        ...
```

### 2.4 `TransformersModelHubPort`
```python
class TransformersModelHubPort(ABC):
    @abstractmethod
    def load_model(self, model_id: str, revision: Optional[str] = None) -> TransformersModelPort:
        ...

    @abstractmethod
    def load_tokenizer(self, model_id: str) -> TransformersTokenizerPort:
        ...
```

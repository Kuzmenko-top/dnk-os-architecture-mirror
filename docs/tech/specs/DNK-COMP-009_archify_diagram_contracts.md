# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-009_archify_diagram_contracts.md"
# purpose: "Component Contracts & Pydantic DTOs for Archify Diagram Engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-ARCHIFY-ASSIMILATION-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# DNK-COMP-009: Контракти компонентів та інтерфейси Archify Adapter

## 1. DTO Моделі (Data Transfer Objects)

### 1.1 `ArchifyNode`
```python
class ArchifyNode(BaseModel):
    id: str
    label: str
    sublabel: Optional[str] = None
    type: Optional[str] = "backend"  # frontend | backend | database | security | external
    lane: Optional[str] = None
    col: Optional[int] = None
    row: Optional[int] = None
    width: Optional[int] = 140
    tag: Optional[str] = None
    icon: Optional[str] = None
```

### 1.2 `ArchifyEdge`
```python
class ArchifyEdge(BaseModel):
    id: str
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    label: Optional[str] = None
    variant: Optional[str] = "default"  # default | emphasis | dashed | security
    role: Optional[str] = None
    from_side: Optional[str] = Field(default=None, alias="fromSide")
    to_side: Optional[str] = Field(default=None, alias="toSide")
    route: Optional[str] = None
```

### 1.3 `ArchifyMeta` & `ArchifyViewSpec`
```python
class ArchifyViewSpec(BaseModel):
    id: str
    label: str
    focus: List[str] = Field(default_factory=list)
    note: Optional[str] = None

class ArchifyMeta(BaseModel):
    title: str
    subtitle: Optional[str] = None
    animation: Optional[str] = "trace"  # trace | pulse | none
    visual_preset: Optional[str] = "signal-flow"
    quality_profile: Optional[str] = "showcase"
    views: List[ArchifyViewSpec] = Field(default_factory=list)
    output: Optional[str] = None
```

## 2. Інтерфейс адаптера `DNKArchifyAdapter`
- `is_engine_ready() -> bool`: перевірка працездатності CLI.
- `render_diagram(diagram_type, payload, output_html_path) -> str`: компіляція у файл.
- `build_swarm_workflow_preset(...) -> Dict[str, Any]`: пресет життєвого циклу Swarm.

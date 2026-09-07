# Generative UI 2.0: Component Sandbox, Auto-Layout & Smart Connectors

Architecture patterns and reference implementations for isolated component execution, automatic spatial layout, and semantic edge inference in generative visual canvases.

## 1. Sandbox Component Isolation

### Strict Content Security Policy (CSP) Iframe Envelope
When executing user- or AI-generated React/Vue/Svelte components in runtime canvases, enforce sandboxing via iframe envelopes with restrictive CSP headers and isolated postMessage bridges.

```python
def generate_iframe_envelope(component_code: str, props: dict, instance_id: str) -> str:
    csp = (
        "default-src 'none'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https:;"
    )
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="{csp}">
  <title>Sandbox {instance_id}</title>
</head>
<body>
  <div id="root"></div>
  <script type="application/json" id="props">{json.dumps(props)}</script>
</body>
</html>"""
```

### Native Shadow DOM Isolation Descriptor
For Web Components, encapsulate DOM and styles using open Shadow Root descriptors:

```python
def generate_shadow_dom_descriptor(component_name: str, css_scoped: str, template: str) -> dict:
    return {
        "tag_name": f"dnk-{component_name.lower().replace('_', '-')}",
        "mode": "open",
        "scoped_styles": css_scoped,
        "template": template,
        "delegates_focus": True
    }
```

## 2. Component Lifecycle & Inter-Node Message Bus

- **Lifecycle States**: `IDLE` ➔ `MOUNTING` ➔ `MOUNTED` ➔ `UPDATING` ➔ `UNMOUNTED` (with `ERROR` transition on crash).
- **Supervisor-Worker Coordination**:
  - Supervisor nodes emit task dispatches (`action="EXECUTE_TASK"`).
  - Worker components receive state payloads and emit render events or completion RPC messages.

## 3. Spatial Auto-Layout Algorithms

When adding or rearranging generative components on infinite canvas:
- **Horizontal Flow**: $x_i = x_0 + i \cdot \Delta x$, $y_i = y_0$.
- **Vertical Stack**: $x_i = x_0$, $y_i = y_0 + i \cdot \Delta y$.
- **2-Column Grid**: $col = i \pmod 2, row = \lfloor i / 2 \rfloor$; $x_i = x_0 + col \cdot \Delta x$, $y_i = y_0 + row \cdot \Delta y$.

## 4. Smart Connectors Semantic Inference

Infer directional graph edges by inspecting node roles:
1. `supervisor` ➔ `agent` (`source_port="dispatch"`, `target_port="task_in"`).
2. `agent` ➔ `component` (`source_port="render_out"`, `target_port="view_in"`).

# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_component_sandbox"
# purpose: "Shadow DOM / iframe sandbox component isolation, lifecycle manager, and Supervisor-Worker message bus (DNK-CANVAS-002 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class ComponentLifecycleState(str, Enum):
    IDLE = "idle"
    MOUNTING = "mounting"
    MOUNTED = "mounted"
    UPDATING = "updating"
    ERROR = "error"
    UNMOUNTED = "unmounted"


@dataclass
class SandboxSecurityConfig:
    allow_scripts: bool = True
    allow_same_origin: bool = False
    allow_popups: bool = False
    allow_forms: bool = False
    csp_default_src: str = "'none'"
    csp_script_src: str = "'self' 'unsafe-inline' https://cdn.jsdelivr.net"
    csp_style_src: str = "'self' 'unsafe-inline' https://fonts.googleapis.com"
    csp_img_src: str = "'self' data: https:"


@dataclass
class ComponentInstance:
    instance_id: str
    component_id: str
    node_id: str
    props: Dict[str, Any] = field(default_factory=dict)
    state: ComponentLifecycleState = ComponentLifecycleState.IDLE
    error_message: Optional[str] = None
    mounted_at: Optional[float] = None
    last_updated_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "component_id": self.component_id,
            "node_id": self.node_id,
            "props": self.props,
            "state": self.state.value,
            "error_message": self.error_message,
            "mounted_at": self.mounted_at,
            "last_updated_at": self.last_updated_at
        }


class CanvasComponentSandbox:
    """Manages component sandboxing, isolation envelopes, lifecycle states, and Supervisor-Worker communication."""

    def __init__(self, security_config: Optional[SandboxSecurityConfig] = None):
        self.security_config = security_config or SandboxSecurityConfig()
        self.instances: Dict[str, ComponentInstance] = {}
        self.message_log: List[Dict[str, Any]] = []
        self._listeners: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def generate_iframe_envelope(
        self,
        component_code: str,
        props: Dict[str, Any],
        framework: str = "react",
        instance_id: str = "inst_001"
    ) -> str:
        """
        Generates a secure HTML document envelope for iframe sandboxing.
        """
        csp = (
            f"default-src {self.security_config.csp_default_src}; "
            f"script-src {self.security_config.csp_script_src}; "
            f"style-src {self.security_config.csp_style_src}; "
            f"img-src {self.security_config.csp_img_src};"
        )
        escaped_props = json.dumps(props)

        envelope = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="{csp}">
  <title>Sandbox Component {instance_id}</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, sans-serif;
      background: transparent;
      color: #f8fafc;
      overflow: hidden;
    }}
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="application/json" id="initial-props">{escaped_props}</script>
  <script>
    window.DNK_INSTANCE_ID = "{instance_id}";
    window.addEventListener('message', (event) => {{
      if (event.data && event.data.type === 'UPDATE_PROPS') {{
        console.log('Props updated inside sandbox:', event.data.payload);
      }}
    }});
  </script>
  <!-- Component Payload -->
  <script type="module">
    // Isolated execution module
  </script>
</body>
</html>"""
        return envelope

    def generate_shadow_dom_descriptor(
        self,
        component_name: str,
        css_scoped: str,
        html_template: str
    ) -> Dict[str, Any]:
        """Generates Shadow DOM definition descriptor for native Web Component encapsulation."""
        return {
            "tag_name": f"dnk-{component_name.lower().replace('_', '-')}",
            "mode": "open",
            "scoped_styles": css_scoped,
            "template": html_template,
            "delegates_focus": True
        }

    # ------------------ Lifecycle Management ------------------

    def mount_component(
        self,
        instance_id: str,
        component_id: str,
        node_id: str,
        initial_props: Optional[Dict[str, Any]] = None
    ) -> ComponentInstance:
        """Mounts a new component instance inside the sandbox registry."""
        inst = ComponentInstance(
            instance_id=instance_id,
            component_id=component_id,
            node_id=node_id,
            props=initial_props or {},
            state=ComponentLifecycleState.MOUNTED,
            mounted_at=time.time(),
            last_updated_at=time.time()
        )
        self.instances[instance_id] = inst
        self._emit_event("lifecycle", {"action": "mount", "instance_id": instance_id, "node_id": node_id})
        return inst

    def update_props(self, instance_id: str, new_props: Dict[str, Any]) -> Optional[ComponentInstance]:
        """Updates props for an existing component instance."""
        inst = self.instances.get(instance_id)
        if not inst:
            return None

        inst.props.update(new_props)
        inst.state = ComponentLifecycleState.UPDATING
        inst.last_updated_at = time.time()
        inst.state = ComponentLifecycleState.MOUNTED

        self._emit_event("lifecycle", {"action": "update_props", "instance_id": instance_id, "props": new_props})
        return inst

    def unmount_component(self, instance_id: str) -> bool:
        """Unmounts and removes a component instance."""
        if instance_id not in self.instances:
            return False

        inst = self.instances[instance_id]
        inst.state = ComponentLifecycleState.UNMOUNTED
        del self.instances[instance_id]
        self._emit_event("lifecycle", {"action": "unmount", "instance_id": instance_id})
        return True

    # ------------------ Supervisor-Worker Message Bus ------------------

    def send_message(
        self,
        sender_id: str,
        target_id: str,
        action: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatches an inter-node message (Supervisor -> Worker or Worker -> Supervisor)."""
        msg = {
            "timestamp": time.time(),
            "sender_id": sender_id,
            "target_id": target_id,
            "action": action,
            "payload": payload
        }
        self.message_log.append(msg)
        self._emit_event(f"message:{target_id}", msg)
        self._emit_event("message_all", msg)
        return msg

    def register_listener(self, channel: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Registers a subscriber callback for a channel."""
        if channel not in self._listeners:
            self._listeners[channel] = []
        self._listeners[channel].append(callback)

    def _emit_event(self, channel: str, data: Dict[str, Any]) -> None:
        for callback in self._listeners.get(channel, []):
            try:
                callback(data)
            except Exception:
                pass

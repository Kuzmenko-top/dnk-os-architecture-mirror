# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_init"
# purpose: "Package initializer for API routers"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from . import canvas
from . import agent
from . import artifact
from . import analytics
from . import taskdna
from . import workspace
from . import secrets_vault
from . import admin_security
from . import workspace_collaboration
from . import github
from . import timeline
from . import workspace_analytics
from . import analytics_alerting
from . import analytics_forecasting
from . import worker_management
from . import shopify
from . import video_router
from . import whiteboard_router
from . import product_launch
from . import workflow_composer
from . import swarm_resilience_router
from . import distiller
from . import gcp_rotation_router
from . import canvas_stitch_router
from . import lakehouse_bi_router
from . import shopify_ast_router
from . import task_forest_router
from . import swarm_ws
from . import node_tasks_router

__all__ = [
    "canvas",
    "agent",
    "artifact",
    "analytics",
    "taskdna",
    "workspace",
    "secrets_vault",
    "admin_security",
    "workspace_collaboration",
    "github",
    "timeline",
    "workspace_analytics",
    "analytics_alerting",
    "analytics_forecasting",
    "worker_management",
    "shopify",
    "video_router",
    "whiteboard_router",
    "product_launch",
    "workflow_composer",
    "swarm_resilience_router",
    "distiller",
    "gcp_rotation_router",
    "canvas_stitch_router",
    "lakehouse_bi_router",
    "shopify_ast_router",
    "task_forest_router",
    "swarm_ws",
    "node_tasks_router",
]




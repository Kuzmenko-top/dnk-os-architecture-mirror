# --- DNK-MRH-HEADER ---
# mrh_id: "core/service_registry.py"
# purpose: "Service registry and pluggable service manifest validation engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import os
import yaml
import importlib
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class EndpointModel(BaseModel):
    path: str = Field(..., description="HTTP endpoint path")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    handler: str = Field(..., description="Name of the handler function or module path")

class ServiceManifestModel(BaseModel):
    service_id: str = Field(..., description="Unique service identifier")
    name: str = Field(..., description="Human-friendly service name")
    port: int = Field(..., description="Assigned port number")
    domain: str = Field(..., description="Functional domain of the service")
    status: str = Field(..., description="Service status (Active, Draft, etc.)")
    version: str = Field(..., description="Service semantic version")
    entrypoint: str = Field(..., description="Import path to the main application / FastAPI app")
    endpoints: List[EndpointModel] = Field(default_factory=list, description="List of exposed endpoints")

class ServiceRegistry:
    """
    Pluggable ServiceRegistry for scanning, validating, and managing
    microservices in the DNK OS ecosystem.
    """
    def __init__(self, services_dir: str = None):
        # Default to services/
        if services_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.services_dir = os.path.join(base_dir, "services")
        else:
            self.services_dir = services_dir
            
        self.services: Dict[str, ServiceManifestModel] = {}
        self.scan_and_register_services()

    def validate_manifest(self, manifest_data: dict) -> ServiceManifestModel:
        """Validate raw manifest dictionary against Pydantic model."""
        return ServiceManifestModel(**manifest_data)

    def scan_and_register_services(self) -> int:
        """Scans services directory for service_manifest.yaml files, validates and registers them."""
        if not os.path.exists(self.services_dir):
            return 0
            
        registered_count = 0
        for entry in os.listdir(self.services_dir):
            service_path = os.path.join(self.services_dir, entry)
            if not os.path.isdir(service_path):
                continue
                
            manifest_file = os.path.join(service_path, "service_manifest.yaml")
            if not os.path.exists(manifest_file):
                continue
                
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    # Strip MRH comments before loading YAML
                    lines = f.readlines()
                    yaml_lines = [l for l in lines if not l.strip().startswith("#")]
                    raw_data = yaml.safe_load("".join(yaml_lines))
                    
                if not raw_data:
                    continue
                    
                validated_manifest = self.validate_manifest(raw_data)
                self.services[validated_manifest.service_id] = validated_manifest
                registered_count += 1
            except Exception as e:
                print(f"ServiceRegistry Warning: Failed to register service at {service_path}: {e}")
                
        return registered_count

    def dynamic_import_entrypoint(self, service_id: str) -> Any:
        """Dynamically imports the FastAPI app or entrypoint object of the service."""
        if service_id not in self.services:
            raise KeyError(f"Service {service_id} is not registered.")
            
        manifest = self.services[service_id]
        entrypoint_str = manifest.entrypoint
        
        if ":" not in entrypoint_str:
            raise ValueError(f"Invalid entrypoint format for {service_id}. Expected 'module:object', got '{entrypoint_str}'")
            
        module_path, obj_name = entrypoint_str.split(":", 1)
        
        try:
            module = importlib.import_module(module_path)
            entry_obj = getattr(module, obj_name)
            return entry_obj
        except Exception as e:
            raise ImportError(f"Failed to dynamically import entrypoint '{entrypoint_str}' for service {service_id}: {e}")

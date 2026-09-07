# --- DNK-MRH-HEADER ---
# mrh_id: "core/plugins/plugin_api.py"
# purpose: "FastAPI REST Router for Plugin Installation Lifecycle, Provenance, and Audit"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

import base64
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.plugins.plugin_installer import PluginInstaller
from core.plugins.plugin_manifest import InvalidPluginManifestError
from core.plugins.plugin_models import InvalidPluginInstallTransitionError
from core.plugins.plugin_security_gate import (
    ProductionUnsignedPluginError,
    HashMismatchError,
    InvalidSignatureError,
    UntrustedSigningKeyError,
    PluginQuarantinedError,
    DependencyNotSatisfiedError,
    InstallationRollbackFailedError,
)

router = APIRouter(prefix="/plugins", tags=["plugin-lifecycle"])

# Global singleton installer instance for testing/runtime
global_installer = PluginInstaller()

def get_installer() -> PluginInstaller:
    return global_installer

class InstallPluginRequest(BaseModel):
    manifest: Dict[str, Any]
    package_b64: str
    production_mode: bool = True

class ActivatePluginRequest(BaseModel):
    version: str

class RollbackPluginRequest(BaseModel):
    target_version: Optional[str] = None

class UninstallPluginRequest(BaseModel):
    version: str


@router.post("/install")
def install_plugin(
    req: InstallPluginRequest,
    workspace_id: str = Header(default="default_ws", alias="X-Workspace-ID"),
    actor_id: str = Header(default="system_user", alias="X-Actor-ID"),
    installer: PluginInstaller = Depends(get_installer),
):
    try:
        package_bytes = base64.b64decode(req.package_b64)
        record = installer.install_plugin(
            raw_manifest=req.manifest,
            package_bytes=package_bytes,
            workspace_id=workspace_id,
            actor_id=actor_id,
            production_mode=req.production_mode,
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=record.to_dict())

    except InvalidPluginManifestError as e:
        raise HTTPException(status_code=400, detail={"error": e.error_code, "message": str(e)})
    except ProductionUnsignedPluginError as e:
        raise HTTPException(status_code=403, detail={"error": e.error_code, "message": str(e)})
    except UntrustedSigningKeyError as e:
        raise HTTPException(status_code=403, detail={"error": e.error_code, "message": str(e)})
    except HashMismatchError as e:
        raise HTTPException(status_code=422, detail={"error": e.error_code, "message": str(e)})
    except InvalidSignatureError as e:
        raise HTTPException(status_code=422, detail={"error": e.error_code, "message": str(e)})
    except PluginQuarantinedError as e:
        raise HTTPException(status_code=423, detail={"error": e.error_code, "message": str(e)})
    except ValueError as e:
        if "DUPLICATE_PLUGIN_VERSION" in str(e):
            raise HTTPException(status_code=409, detail={"error": "DUPLICATE_PLUGIN_VERSION", "message": str(e)})
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": str(e)})


@router.get("/installations/{installation_id}")
def get_installation(
    installation_id: str,
    installer: PluginInstaller = Depends(get_installer),
):
    rec = installer.store.get_record_by_id(installation_id)
    if not rec:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"Installation '{installation_id}' not found."})
    return rec.to_dict()


@router.post("/{plugin_id}/activate")
def activate_plugin(
    plugin_id: str,
    req: ActivatePluginRequest,
    workspace_id: str = Header(default="default_ws", alias="X-Workspace-ID"),
    actor_id: str = Header(default="system_user", alias="X-Actor-ID"),
    installer: PluginInstaller = Depends(get_installer),
):
    try:
        rec = installer.activate_plugin(
            workspace_id=workspace_id,
            plugin_id=plugin_id,
            version=req.version,
            actor_id=actor_id,
        )
        return rec.to_dict()

    except InvalidPluginInstallTransitionError as e:
        raise HTTPException(status_code=409, detail={"error": e.error_code, "message": str(e)})
    except DependencyNotSatisfiedError as e:
        raise HTTPException(status_code=424, detail={"error": e.error_code, "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "ACTIVATION_FAILED", "message": str(e)})


@router.post("/{plugin_id}/rollback")
def rollback_plugin(
    plugin_id: str,
    req: RollbackPluginRequest,
    workspace_id: str = Header(default="default_ws", alias="X-Workspace-ID"),
    actor_id: str = Header(default="system_user", alias="X-Actor-ID"),
    installer: PluginInstaller = Depends(get_installer),
):
    try:
        rec = installer.rollback_plugin(
            workspace_id=workspace_id,
            plugin_id=plugin_id,
            target_version=req.target_version,
            actor_id=actor_id,
        )
        return rec.to_dict()
    except InstallationRollbackFailedError as e:
        raise HTTPException(status_code=500, detail={"error": e.error_code, "message": str(e)})


@router.post("/{plugin_id}/uninstall")
def uninstall_plugin(
    plugin_id: str,
    req: UninstallPluginRequest,
    workspace_id: str = Header(default="default_ws", alias="X-Workspace-ID"),
    actor_id: str = Header(default="system_user", alias="X-Actor-ID"),
    installer: PluginInstaller = Depends(get_installer),
):
    success = installer.uninstall_plugin(
        workspace_id=workspace_id,
        plugin_id=plugin_id,
        version=req.version,
        actor_id=actor_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"Plugin '{plugin_id}' v{req.version} not found."})
    return {"status": "uninstalled", "plugin_id": plugin_id, "version": req.version}


@router.get("/{plugin_id}/versions")
def list_versions(
    plugin_id: str,
    workspace_id: str = Header(default="default_ws", alias="X-Workspace-ID"),
    installer: PluginInstaller = Depends(get_installer),
):
    records = installer.store.list_versions(workspace_id, plugin_id)
    return [r.to_dict() for r in records]


@router.get("/{plugin_id}/provenance")
def get_provenance(
    plugin_id: str,
    version: Optional[str] = None,
    workspace_id: str = Header(default="default_ws", alias="X-Workspace-ID"),
    installer: PluginInstaller = Depends(get_installer),
):
    if not version:
        version = installer.store.get_active_version(workspace_id, plugin_id)
    if not version:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "No active version found."})

    rec = installer.store.get_record(workspace_id, plugin_id, version)
    if not rec:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": f"Record for v{version} not found."})

    return {
        "plugin_id": rec.plugin_id,
        "version": rec.version,
        "publisher": rec.publisher,
        "content_hash": rec.content_hash,
        "hash_algorithm": rec.hash_algorithm,
        "signature_fingerprint": rec.signature_fingerprint,
        "key_id": rec.key_id,
        "trust_state": rec.trust_state,
        "installed_at": rec.installed_at,
        "created_by": rec.created_by,
    }


@router.get("/{plugin_id}/audit")
def get_audit_trail(
    plugin_id: str,
    installer: PluginInstaller = Depends(get_installer),
):
    return installer.audit_logger.get_logs_for_plugin(plugin_id)

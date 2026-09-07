# --- DNK-MRH-HEADER ---
# mrh_id: "tests/deployment/test_k8s_manifests.py"
# purpose: "Verification tests for Kubernetes manifests (API versions, security contexts, probes, autoscaling)"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import os
import yaml
import pytest

K8S_DIR = "deployments/k8s"

def get_yaml_docs(filename):
    path = os.path.join(K8S_DIR, filename)
    assert os.path.exists(path), f"File {path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        return list(yaml.safe_load_all(f))

def test_k8s_namespace():
    docs = get_yaml_docs("namespace.yaml")
    assert len(docs) >= 1
    ns = docs[0]
    assert ns.get("kind") == "Namespace"
    assert ns.get("metadata", {}).get("name") == "dnk-os"

def test_k8s_api_deployment():
    docs = get_yaml_docs("api-deployment.yaml")
    assert len(docs) >= 1
    deploy = docs[0]
    assert deploy.get("kind") == "Deployment"
    spec = deploy.get("spec", {})
    assert spec.get("replicas") == 3
    
    # Template container checks
    template = spec.get("template", {})
    pod_spec = template.get("spec", {})
    containers = pod_spec.get("containers", [])
    assert len(containers) >= 1
    api_c = containers[0]
    
    assert "livenessProbe" in api_c
    assert "readinessProbe" in api_c
    assert "startupProbe" in api_c
    assert "resources" in api_c
    
    # Security context
    sec_ctx = pod_spec.get("securityContext", {})
    assert sec_ctx.get("runAsNonRoot") is True
    assert sec_ctx.get("runAsUser") == 10001

def test_k8s_web_deployment():
    docs = get_yaml_docs("web-deployment.yaml")
    assert len(docs) >= 1
    deploy = docs[0]
    assert deploy.get("kind") == "Deployment"
    spec = deploy.get("spec", {})
    assert spec.get("replicas") == 2
    
    containers = spec.get("template", {}).get("spec", {}).get("containers", [])
    assert len(containers) >= 1
    assert "livenessProbe" in containers[0]
    assert "readinessProbe" in containers[0]

def test_k8s_hpa_pdb():
    hpa_docs = get_yaml_docs("hpa.yaml")
    assert len(hpa_docs) >= 1
    hpa_kinds = [d.get("kind") for d in hpa_docs]
    assert "HorizontalPodAutoscaler" in hpa_kinds

    pdb_docs = get_yaml_docs("pdb.yaml")
    assert len(pdb_docs) >= 1
    pdb_kinds = [d.get("kind") for d in pdb_docs]
    assert "PodDisruptionBudget" in pdb_kinds

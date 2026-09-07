# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_gitops_manifest_generator"
# purpose: "GitOps Manifest Generator for ArgoCD Rollouts, ApplicationSets & Flux CD (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import yaml
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GitOpsConfig(BaseModel):
    app_name: str
    namespace: str = "production"
    git_repo_url: str = "https://github.com/dnk-org/dnk-hub.git"
    git_target_revision: str = "HEAD"
    image_repository: str = "ghcr.io/dnk-org/dnk-api"
    current_tag: str = "v1.0.0"
    canary_steps: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"setWeight": 1, "pause": {"duration": "30s"}},
            {"setWeight": 5, "pause": {"duration": "60s"}},
            {"setWeight": 25, "pause": {"duration": "120s"}},
            {"setWeight": 50, "pause": {"duration": "180s"}},
        ]
    )
    traffic_routing_provider: str = "nginx"  # 'nginx' or 'istio'
    ingress_name: str = "dnk-api-ingress"
    virtual_service_name: str = "dnk-api-virtualservice"


class GitOpsManifestGenerator:
    """
    Generates production GitOps manifests for ArgoCD (Rollout, Application, ApplicationSet)
    and Flux CD (Kustomization, HelmRelease) supporting Zero-Downtime Blue/Green and Canary pipelines.
    """

    def __init__(self, config: GitOpsConfig):
        self.config = config

    def generate_argo_rollout(self) -> Dict[str, Any]:
        """
        Generates an Argo Rollouts Custom Resource (argoproj.io/v1alpha1) with automated canary steps.
        """
        traffic_routing: Dict[str, Any] = {}
        if self.config.traffic_routing_provider == "nginx":
            traffic_routing = {
                "nginx": {
                    "stableIngress": self.config.ingress_name,
                    "additionalIngressAnnotations": {
                        "canary-by-header": "X-Canary",
                        "canary-by-header-value": "always",
                    },
                }
            }
        elif self.config.traffic_routing_provider == "istio":
            traffic_routing = {
                "istio": {
                    "virtualService": {
                        "name": self.config.virtual_service_name,
                        "routes": ["primary-route"],
                    },
                    "destinationRule": {
                        "name": f"{self.config.app_name}-destinationrule",
                        "canarySubsetName": "canary",
                        "stableSubsetName": "stable",
                    },
                }
            }

        rollout = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Rollout",
            "metadata": {
                "name": self.config.app_name,
                "namespace": self.config.namespace,
                "labels": {
                    "app.kubernetes.io/name": self.config.app_name,
                    "dnk.io/pipeline": "blue-green-canary",
                },
            },
            "spec": {
                "replicas": 5,
                "strategy": {
                    "canary": {
                        "analysis": {
                            "templates": [{"templateName": f"{self.config.app_name}-slo-analysis"}],
                            "args": [{"name": "service-name", "value": self.config.app_name}],
                        },
                        "steps": self.config.canary_steps,
                        "trafficRouting": traffic_routing,
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app.kubernetes.io/name": self.config.app_name,
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": self.config.app_name,
                                "image": f"{self.config.image_repository}:{self.config.current_tag}",
                                "ports": [{"containerPort": 8000, "name": "http"}],
                                "livenessProbe": {
                                    "httpGet": {"path": "/health/live", "port": 8000},
                                    "initialDelaySeconds": 10,
                                    "periodSeconds": 10,
                                },
                                "readinessProbe": {
                                    "httpGet": {"path": "/health/ready", "port": 8000},
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 5,
                                },
                            }
                        ]
                    },
                },
            },
        }
        return rollout

    def generate_argo_application(self) -> Dict[str, Any]:
        """
        Generates an ArgoCD Application manifest pointing to the GitOps deployment repository.
        """
        app = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": f"{self.config.app_name}-gitops",
                "namespace": "argocd",
                "finalizers": ["resources-finalizer.argocd.argoproj.io"],
            },
            "spec": {
                "project": "default",
                "source": {
                    "repoURL": self.config.git_repo_url,
                    "targetRevision": self.config.git_target_revision,
                    "path": f"k8s/environments/{self.config.namespace}",
                },
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": self.config.namespace,
                },
                "syncPolicy": {
                    "automated": {
                        "prune": True,
                        "selfHeal": True,
                    },
                    "syncOptions": ["CreateNamespace=true"],
                },
            },
        }
        return app

    def generate_flux_kustomization(self) -> Dict[str, Any]:
        """
        Generates a Flux CD Kustomization resource (kustomize.toolkit.fluxcd.io/v1) for continuous reconciliation.
        """
        kustomization = {
            "apiVersion": "kustomize.toolkit.fluxcd.io/v1",
            "kind": "Kustomization",
            "metadata": {
                "name": f"{self.config.app_name}-flux",
                "namespace": "flux-system",
            },
            "spec": {
                "interval": "1m",
                "targetNamespace": self.config.namespace,
                "sourceRef": {
                    "kind": "GitRepository",
                    "name": "dnk-hub-repo",
                },
                "path": f"./k8s/overlays/{self.config.namespace}",
                "prune": True,
                "wait": True,
                "timeout": "3m",
            },
        }
        return kustomization

    def export_all_yaml(self) -> str:
        """
        Exports all GitOps resources separated by Kubernetes YAML document delimiters ('---').
        """
        manifests = [
            self.generate_argo_rollout(),
            self.generate_argo_application(),
            self.generate_flux_kustomization(),
        ]
        return "\n---\n".join(
            yaml.dump(m, sort_keys=False, default_flow_style=False) for m in manifests
        )

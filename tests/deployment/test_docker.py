# --- DNK-MRH-HEADER ---
# mrh_id: "tests/deployment/test_docker.py"
# purpose: "Test suite for Docker deployment configuration and health checks"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import pytest
import yaml
from fastapi.testclient import TestClient
from dnk_os.core.agent import app


class TestDockerDeployment:
    """Test suite for Docker deployment."""

    def test_dockerfile_exists_and_valid(self):
        """Test Dockerfile structure and multi-stage syntax."""
        dockerfile_path = "Dockerfile"
        assert os.path.exists(dockerfile_path)
        with open(dockerfile_path, "r") as f:
            content = f.read()
        assert "FROM python:3.12-slim AS python-builder" in content
        assert "FROM node:24-slim AS node-builder" in content
        assert "HEALTHCHECK" in content
        assert "EXPOSE 8000 3000" in content

    def test_docker_compose_structure(self):
        """Test docker-compose.yml configuration and services."""
        compose_path = "docker-compose.yml"
        assert os.path.exists(compose_path)
        with open(compose_path, "r") as f:
            compose_cfg = yaml.safe_load(f)

        services = compose_cfg.get("services", {})
        assert "dnk-api" in services
        assert "dnk-frontend" in services
        assert "postgres" in services
        assert "redis" in services
        assert "pgvector" in services
        assert "volumes" in compose_cfg

    def test_dockerignore_coverage(self):
        """Test .dockerignore rules for zero host pollution."""
        dockerignore_path = ".dockerignore"
        assert os.path.exists(dockerignore_path)
        with open(dockerignore_path, "r") as f:
            content = f.read()
        assert ".git" in content
        assert "__pycache__" in content
        assert ".venv" in content
        assert "node_modules" in content

    def test_deploy_script_valid(self):
        """Test scripts/deploy.sh exists and is executable."""
        script_path = "scripts/deploy.sh"
        assert os.path.exists(script_path)
        assert os.access(script_path, os.X_OK)
        with open(script_path, "r") as f:
            content = f.read()
        assert "docker-compose build" in content
        assert "docker-compose up -d" in content

    def test_api_health_endpoint(self):
        """Test FastAPI agent health endpoint."""
        assert app is not None
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
        assert response.json()["status"] in ["healthy", "unhealthy", "degraded"]
        assert "services" in response.json()

    def test_postgres_configuration(self):
        """Test PostgreSQL environment configuration in compose."""
        with open("docker-compose.yml", "r") as f:
            compose_cfg = yaml.safe_load(f)
        postgres_env = compose_cfg["services"]["postgres"]["environment"]
        assert any("POSTGRES_USER=dnk" in str(e) for e in postgres_env)
        assert any("POSTGRES_DB=dnk_os" in str(e) for e in postgres_env)

    def test_redis_configuration(self):
        """Test Redis configuration in compose."""
        with open("docker-compose.yml", "r") as f:
            compose_cfg = yaml.safe_load(f)
        redis_srv = compose_cfg["services"]["redis"]
        assert redis_srv["image"] == "redis:7-alpine"
        assert "6379:6379" in redis_srv["ports"]

    def test_backend_dockerfile_structure(self):
        """Test dedicated Dockerfile.backend configuration."""
        dockerfile_path = "Dockerfile.backend"
        assert os.path.exists(dockerfile_path)
        with open(dockerfile_path, "r") as f:
            content = f.read()
        assert "FROM python:3.12-slim" in content
        assert "HEALTHCHECK" in content
        assert "EXPOSE 8000" in content
        assert "pytest" in content

    def test_frontend_dockerfile_structure(self):
        """Test dedicated Dockerfile.frontend and Dockerfile.web configuration without fake-green flags."""
        for dockerfile_path in ("Dockerfile.frontend", "Dockerfile.web", "apps/web/Dockerfile"):
            assert os.path.exists(dockerfile_path), f"Missing {dockerfile_path}"
            with open(dockerfile_path, "r") as f:
                content = f.read()
            assert "FROM node:" in content
            assert "HEALTHCHECK" in content
            assert "EXPOSE 3000" in content
            assert "npm run build || true" not in content, f"{dockerfile_path} contains unsafe || true flag in build stage!"

    def test_docker_compose_backend_frontend_services(self):
        """Test backend and frontend primary services in docker-compose.yml."""
        compose_path = "docker-compose.yml"
        assert os.path.exists(compose_path)
        with open(compose_path, "r") as f:
            compose_cfg = yaml.safe_load(f)
        services = compose_cfg.get("services", {})
        assert "backend" in services
        assert "frontend" in services
        assert "postgres" in services
        assert "redis" in services
        assert "pgvector" in services

    def test_docker_compose_prod_structure(self):
        """Test production docker-compose.prod.yml structure."""
        prod_path = "docker-compose.prod.yml"
        assert os.path.exists(prod_path)
        with open(prod_path, "r") as f:
            prod_cfg = yaml.safe_load(f)
        services = prod_cfg.get("services", {})
        assert "backend" in services
        assert "frontend" in services
        assert "postgres" in services
        assert "redis" in services
        assert "gateway" in services

    def test_docker_setup_documentation(self):
        """Test presence and completeness of docs/deployment/DOCKER_SETUP.md."""
        doc_path = "docs/deployment/DOCKER_SETUP.md"
        assert os.path.exists(doc_path)
        with open(doc_path, "r") as f:
            content = f.read()
        assert "DNK-MRH-HEADER" in content
        assert "docker-compose up -d" in content
        assert "pytest" in content

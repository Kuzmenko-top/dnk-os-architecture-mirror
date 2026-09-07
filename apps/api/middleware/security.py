# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_middleware_security"
# purpose: "Security middleware implementing rate limiting, API Key enforcement, CORS origin verification, and custom encryption utilities"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import base64
import os
import time
from typing import Dict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.config.security_config import (
    SECURITY_RATE_LIMIT,
    SECURITY_CORS_ORIGINS,
    SECURITY_API_KEY_HEADER,
    SECURITY_API_KEY,
    SECURITY_ENCRYPTION_KEY
)

# Simple sliding window/timestamp rate limiter
# Maps client IP to a list of request timestamps
RATE_LIMIT_STORE: Dict[str, list] = {}

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown_client"
        path = request.url.path

        # 1. Rate Limiting Check
        is_testing = bool(os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING") == "1")
        if not is_testing and SECURITY_RATE_LIMIT > 0:
            now = time.time()
            # Clean timestamps older than 60s
            if client_ip in RATE_LIMIT_STORE:
                RATE_LIMIT_STORE[client_ip] = [t for t in RATE_LIMIT_STORE[client_ip] if now - t < 60]
            else:
                RATE_LIMIT_STORE[client_ip] = []

            if len(RATE_LIMIT_STORE[client_ip]) >= SECURITY_RATE_LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too Many Requests. Rate limit exceeded.", "error_type": "RateLimitExceeded"}
                )
            
            # Log this request timestamp
            RATE_LIMIT_STORE[client_ip].append(now)

        # 2. API Key Check (enforced on protected routes starting with /api/)
        # Exclude specific public/workspace-gated MVP routes with granular auth checks
        if (
            path.startswith("/api/")
            and not path.startswith("/api/canvas")
            and not path.startswith("/api/artifact")
            and not path.startswith("/api/agent")
            and not path.startswith("/api/workspaces")
            and not path.startswith("/api/v1")
            and not path.startswith("/api/v3")
            and not path.startswith("/api/tasks")
            and not path.startswith("/api/taskdna")
            and not path.startswith("/api/runs")
            and not path.startswith("/api/events")
            and not path.startswith("/api/approvals")
            and not path.startswith("/api/plugins")
            and not path.startswith("/api/trust")
            and not path.startswith("/api/shopify")
            and not path.startswith("/api/analytics")
            and not path.startswith("/api/health")
            and not path.startswith("/api/cabinet")
        ):
            api_key = request.headers.get(SECURITY_API_KEY_HEADER) or request.query_params.get("api_key")
            if SECURITY_API_KEY and (not api_key or api_key != SECURITY_API_KEY):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized. Missing or invalid API key.", "error_type": "Unauthorized"}
                )

        # 3. CORS Check / Origin validation (restrictive option check)
        if "origin" in request.headers:
            origin = request.headers["origin"]
            if "*" not in SECURITY_CORS_ORIGINS and origin not in SECURITY_CORS_ORIGINS:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Forbidden. CORS origin block.", "error_type": "Forbidden"}
                )

        # Proceed to route execution
        response = await call_next(request)

        # Add generic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response


# High-performance, crash-safe bytes-XOR base64 encryption helpers
def encrypt_data(data: str, key: str = SECURITY_ENCRYPTION_KEY) -> str:
    """Encrypt text using Base64 and bytes XOR key sequence"""
    data_bytes = data.encode('utf-8')
    key_bytes = key.encode('utf-8')
    xored_bytes = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data_bytes))
    return base64.b64encode(xored_bytes).decode('utf-8')

def decrypt_data(cipher_text: str, key: str = SECURITY_ENCRYPTION_KEY) -> str:
    """Decrypt cipher using Base64 and bytes XOR key sequence"""
    cipher_bytes = base64.b64decode(cipher_text.encode('utf-8'))
    key_bytes = key.encode('utf-8')
    xored_bytes = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(cipher_bytes))
    return xored_bytes.decode('utf-8')

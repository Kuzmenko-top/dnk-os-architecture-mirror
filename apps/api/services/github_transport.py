# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_github_transport"
# purpose: "Dedicated transport abstraction for outbound GitHub API read requests with strict timeouts and error mapping"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import os
import json
import socket
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

GITHUB_API_HOST: str = "api.github.com"
DEFAULT_TIMEOUT_SECONDS: float = 5.0


class BaseGitHubTransport(ABC):
    """Abstract transport interface for GitHub API requests."""

    @abstractmethod
    def get(self, path: str) -> Tuple[Optional[Any], int, Optional[str]]:
        """
        Execute a GET request against GitHub API.
        Returns: (data_parsed, status_code, error_code)
        """
        pass


class HttpGitHubTransport(BaseGitHubTransport):
    """Concrete HTTP transport utilizing urllib.request with bounded timeout."""

    def __init__(
        self,
        token: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ):
        self._token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self._timeout = timeout

    def get(self, path: str) -> Tuple[Optional[Any], int, Optional[str]]:
        if os.getenv("FIXTURE_MODE", "false").lower() == "true":
            return None, 503, "connection_error"

        url = f"https://{GITHUB_API_HOST}/{path.lstrip('/')}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DNK-OS-Backend/1.0"
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as response:
                status_code = response.getcode()
                body = response.read().decode("utf-8")
                return json.loads(body), status_code, None
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return None, e.code, "unauthorized"
            elif e.code == 404:
                return None, 404, "not_found"
            elif e.code == 429:
                return None, 429, "rate_limit"
            elif e.code >= 500:
                return None, e.code, "upstream_5xx"
            return None, e.code, f"http_{e.code}"
        except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
            err_str = str(e).lower()
            if "timed out" in err_str:
                return None, 408, "timeout"
            return None, 503, "connection_error"
        except Exception:
            return None, 500, "unknown_error"


class MockGitHubTransport(BaseGitHubTransport):
    """Mock transport for unit tests and offline deterministic fixtures."""

    def __init__(self, responses: Optional[Dict[str, Tuple[Optional[Any], int, Optional[str]]]] = None):
        self._responses = responses or {}

    def set_response(self, path: str, data: Optional[Any], status_code: int, error_code: Optional[str] = None):
        self._responses[path.lstrip('/')] = (data, status_code, error_code)

    def get(self, path: str) -> Tuple[Optional[Any], int, Optional[str]]:
        clean_path = path.lstrip('/')
        if clean_path in self._responses:
            return self._responses[clean_path]
        return None, 404, "not_found"

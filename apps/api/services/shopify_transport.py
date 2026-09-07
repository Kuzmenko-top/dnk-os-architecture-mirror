# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_shopify_transport"
# purpose: "Dedicated transport abstraction for outbound Shopify Admin API read requests with strict timeouts, rate-limit parsing, and zero mutation enforcement"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import os
import re
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import requests

from apps.api.services.shopify_models import ShopifyErrorCode

DEFAULT_TIMEOUT_SECONDS = 5.0
SHOPIFY_API_VERSION = "2024-01"


class BaseShopifyTransport(ABC):
    """Abstract base class for Shopify HTTP/GraphQL transports."""

    @abstractmethod
    def get(
        self,
        store_domain: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> Tuple[Optional[Any], int, Optional[ShopifyErrorCode], Optional[Dict[str, str]]]:
        """Perform a read-only GET request against Shopify Admin API.

        Returns: (data, status_code, error_code, response_headers)
        """
        pass

    @abstractmethod
    def graphql(
        self,
        store_domain: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> Tuple[Optional[Any], int, Optional[ShopifyErrorCode], Optional[Dict[str, str]]]:
        """Perform a read-only GraphQL query against Shopify Admin API.

        Returns: (data, status_code, error_code, response_headers)
        """
        pass


class HttpShopifyTransport(BaseShopifyTransport):
    """Production HTTP transport communicating with Shopify Admin REST/GraphQL APIs."""

    def __init__(self, api_token: Optional[str] = None):
        # Read API token only from server environment if not injected directly
        self._api_token = api_token or os.getenv("SHOPIFY_ADMIN_ACCESS_TOKEN") or os.getenv("SHOPIFY_API_KEY") or ""

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "DNK-OS-Backend/1.0 (ShopifyReadOnlyAdapter)"
        }
        if self._api_token:
            headers["X-Shopify-Access-Token"] = self._api_token
        return headers

    def get(
        self,
        store_domain: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> Tuple[Optional[Any], int, Optional[ShopifyErrorCode], Optional[Dict[str, str]]]:
        # Strict zero-egress check when FIXTURE_MODE is active
        if os.getenv("FIXTURE_MODE", "false").lower() == "true":
            return None, 503, "connection_error", {}

        clean_path = path.lstrip("/")
        url = f"https://{store_domain}/{clean_path}"

        try:
            resp = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=timeout
            )
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}

            if resp.status_code == 200:
                try:
                    return resp.json(), 200, None, resp_headers
                except Exception:
                    return None, 502, "upstream_5xx", resp_headers

            if resp.status_code in (401, 403):
                return None, resp.status_code, "unauthorized", resp_headers
            elif resp.status_code == 404:
                return None, 404, "not_found", resp_headers
            elif resp.status_code == 429:
                return None, 429, "rate_limit", resp_headers
            elif resp.status_code >= 500:
                return None, resp.status_code, "upstream_5xx", resp_headers
            else:
                return None, resp.status_code, "unknown_error", resp_headers

        except requests.Timeout:
            return None, 504, "timeout", None
        except requests.RequestException:
            return None, 503, "connection_error", None
        except Exception:
            return None, 500, "unknown_error", None

    def graphql(
        self,
        store_domain: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> Tuple[Optional[Any], int, Optional[ShopifyErrorCode], Optional[Dict[str, str]]]:
        # Strict zero-egress check when FIXTURE_MODE is active
        if os.getenv("FIXTURE_MODE", "false").lower() == "true":
            return None, 503, "connection_error", {}

        # Strict Zero Mutation Invariant: verify query does not contain mutations
        stripped_query = query.strip()
        if re.search(r"\bmutation\b", stripped_query, re.IGNORECASE):
            return None, 400, "mutation_forbidden", {}

        url = f"https://{store_domain}/admin/api/{SHOPIFY_API_VERSION}/graphql.json"
        payload: Dict[str, Any] = {"query": stripped_query}
        if variables:
            payload["variables"] = variables

        try:
            resp = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=timeout
            )
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}

            if resp.status_code == 200:
                try:
                    json_body = resp.json()
                    if "errors" in json_body and not json_body.get("data"):
                        return None, 400, "upstream_5xx", resp_headers
                    return json_body, 200, None, resp_headers
                except Exception:
                    return None, 502, "upstream_5xx", resp_headers

            if resp.status_code in (401, 403):
                return None, resp.status_code, "unauthorized", resp_headers
            elif resp.status_code == 429:
                return None, 429, "rate_limit", resp_headers
            elif resp.status_code >= 500:
                return None, resp.status_code, "upstream_5xx", resp_headers
            else:
                return None, resp.status_code, "unknown_error", resp_headers

        except requests.Timeout:
            return None, 504, "timeout", None
        except requests.RequestException:
            return None, 503, "connection_error", None
        except Exception:
            return None, 500, "unknown_error", None


class MockShopifyTransport(BaseShopifyTransport):
    """In-memory mock transport for unit testing and deterministic simulation."""

    def __init__(self):
        self.routes: Dict[str, Tuple[Optional[Any], int, Optional[ShopifyErrorCode], Optional[Dict[str, str]]]] = {}
        self.call_count: int = 0
        self.last_path: Optional[str] = None
        self.last_params: Optional[Dict[str, str]] = None

    def register_route(
        self,
        path: str,
        data: Optional[Any],
        status_code: int = 200,
        error_code: Optional[ShopifyErrorCode] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.routes[path.lstrip("/")] = (data, status_code, error_code, headers or {})

    def get(
        self,
        store_domain: str,
        path: str,
        params: Optional[Dict[str, str]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> Tuple[Optional[Any], int, Optional[ShopifyErrorCode], Optional[Dict[str, str]]]:
        self.call_count += 1
        self.last_path = path
        self.last_params = params

        clean_path = path.lstrip("/")
        # Check exact path or query match
        if params and "asset[key]" in params:
            key_path = f"{clean_path}?asset[key]={params['asset[key]']}"
            if key_path in self.routes:
                return self.routes[key_path]

        if clean_path in self.routes:
            return self.routes[clean_path]

        return None, 404, "not_found", {}

    def graphql(
        self,
        store_domain: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS
    ) -> Tuple[Optional[Any], int, Optional[ShopifyErrorCode], Optional[Dict[str, str]]]:
        self.call_count += 1
        if re.search(r"\bmutation\b", query, re.IGNORECASE):
            return None, 400, "mutation_forbidden", {}

        graphql_key = "graphql"
        if graphql_key in self.routes:
            return self.routes[graphql_key]

        return {"data": {"shop": {"name": "Mock Store"}}}, 200, None, {}

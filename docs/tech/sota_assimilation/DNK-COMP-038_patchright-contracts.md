# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-COMP-038_patchright-contracts.md"
# purpose: "Typed Pydantic schemas, ports, and protocol interfaces for Patchright assimilation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🔌 DNK-COMP-038: Patchright Typed Contracts & Port Specifications

## 1. Hexagonal Port Definition (`BrowserStealthPort`)
DNK OS interacts with web environments through a clean hexagonal port interface, isolating swarm agents from the underlying automation driver.

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class StealthBrowserConfig(BaseModel):
    headless: bool = Field(default=True, description="Run browser in headless mode")
    proxy_url: Optional[str] = Field(default=None, description="Residential or datacenter proxy URL")
    user_agent: Optional[str] = Field(default=None, description="Custom realistic User-Agent string")
    viewport_width: int = Field(default=1920, description="Viewport width")
    viewport_height: int = Field(default=1080, description="Viewport height")
    locale: str = Field(default="en-US", description="Browser locale")
    timezone_id: str = Field(default="America/New_York", description="Timezone identifier")
    stealth_mode: bool = Field(default=True, description="Enforce Patchright zero-CDP stealth")
    timeout_ms: int = Field(default=30000, description="Navigation timeout in milliseconds")

class StealthPageResponse(BaseModel):
    url: str
    status_code: int
    title: str
    html_content: str
    cookies: List[Dict[str, Any]] = Field(default_factory=list)
    turnstile_bypassed: bool = False
    datadome_bypassed: bool = False
    execution_time_ms: float

class BrowserStealthPort(ABC):
    @abstractmethod
    async def navigate_stealth(self, url: str, config: Optional[StealthBrowserConfig] = None) -> StealthPageResponse:
        """Navigates to URL using zero-CDP stealth driver."""
        pass

    @abstractmethod
    async def extract_content_stealth(self, url: str, selector: Optional[str] = None) -> Dict[str, Any]:
        """Extracts text or elements without triggering bot defenses."""
        pass

    @abstractmethod
    async def click_and_wait(self, url: str, click_selector: str, wait_selector: str) -> StealthPageResponse:
        """Executes human-like click and waits for condition."""
        pass
```

## 2. Ingestion DTOs for Swarm Agents
- **`dnk_shopify` DTO**: `CompetitorStoreScrapeRequest(store_url: HttpUrl, extract_pricing: bool = True)`
- **`gerych_researcher` DTO**: `StealthDocumentationExtractRequest(target_url: HttpUrl, bypass_waf: bool = True)`

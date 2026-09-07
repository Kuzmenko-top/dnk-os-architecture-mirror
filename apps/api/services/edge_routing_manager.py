# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_edge_routing_manager"
# purpose: "Edge Routing Rule Management & Multi-Cloud Provider Edge Generator (DNK-PLATFORM-SCALE-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


class EdgeRoutingManager:
    """Manages Edge Routing Rules and exports Cloudflare Workers / CloudFront / Cloud CDN code."""

    def __init__(self):
        self._rules: Dict[str, Dict[str, Any]] = {}
        self._seed_default_rules()

    def _seed_default_rules(self):
        default_rules = [
            {
                "id": str(uuid.uuid4()),
                "rule_name": "North America Traffic -> us-east-1",
                "geo_match_type": "continent",
                "geo_values": ["NA"],
                "target_region": "us-east-1",
                "priority": 10,
                "enabled": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "rule_name": "Europe Traffic -> eu-west-1",
                "geo_match_type": "continent",
                "geo_values": ["EU"],
                "target_region": "eu-west-1",
                "priority": 20,
                "enabled": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": str(uuid.uuid4()),
                "rule_name": "Asia Pacific Traffic -> ap-southeast-1",
                "geo_match_type": "continent",
                "geo_values": ["AS", "OC"],
                "target_region": "ap-southeast-1",
                "priority": 30,
                "enabled": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ]
        for r in default_rules:
            self._rules[r["id"]] = r

    def list_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        rules = list(self._rules.values())
        if enabled_only:
            rules = [r for r in rules if r.get("enabled")]
        return sorted(rules, key=lambda x: x.get("priority", 0))

    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        return self._rules.get(rule_id)

    def create_rule(
        self,
        rule_name: str,
        geo_match_type: str,
        geo_values: List[str],
        target_region: str,
        priority: int = 0,
        enabled: bool = True,
    ) -> Dict[str, Any]:
        rule = {
            "id": str(uuid.uuid4()),
            "rule_name": rule_name,
            "geo_match_type": geo_match_type,  # 'country', 'continent', 'latency'
            "geo_values": geo_values,
            "target_region": target_region,
            "priority": priority,
            "enabled": enabled,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._rules[rule["id"]] = rule
        return rule

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        rule = self._rules.get(rule_id)
        if not rule:
            return None
        for k, v in updates.items():
            if k in rule and k != "id":
                rule[k] = v
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def match_rule(self, country: Optional[str] = None, continent: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Evaluates active routing rules against user location and returns matched rule object."""
        country_code = (country or "").upper()
        continent_code = (continent or "").upper()

        active_rules = sorted(
            [r for r in self._rules.values() if r.get("enabled")],
            key=lambda x: x.get("priority", 0),
            reverse=True,
        )

        for rule in active_rules:
            match_type = rule.get("geo_match_type")
            geo_values = [v.upper() for v in rule.get("geo_values", [])]

            if match_type == "country" and country_code in geo_values:
                return rule
            elif match_type == "continent" and continent_code in geo_values:
                return rule

        return None

    def evaluate_geo_match(self, country: Optional[str] = None, continent: Optional[str] = None) -> Optional[str]:
        """Evaluates active routing rules against user location and returns target region."""
        country_code = (country or "").upper()
        continent_code = (continent or "").upper()

        active_rules = self.list_rules(enabled_only=True)
        for rule in active_rules:
            m_type = rule.get("geo_match_type")
            values = [v.upper() for v in rule.get("geo_values", [])]

            if m_type == "country" and country_code in values:
                return rule["target_region"]
            elif m_type == "continent" and continent_code in values:
                return rule["target_region"]

        return None

    def generate_cloudflare_worker_script(self) -> str:
        """Generates Cloudflare Worker JavaScript snippet for Edge Routing."""
        return """
// Cloudflare Worker Edge Router - Auto-generated by DNK OS Edge Routing Manager
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const country = request.headers.get('CF-IPCountry') || (request.cf ? request.cf.country : 'US');
  const continent = request.cf ? request.cf.continent : 'NA';
  
  let targetRegion = 'us-east-1';
  if (['EU'].includes(continent)) {
    targetRegion = 'eu-west-1';
  } else if (['AS', 'OC'].includes(continent)) {
    targetRegion = 'ap-southeast-1';
  }
  
  const originUrl = new URL(request.url);
  originUrl.hostname = `${targetRegion}.origin.dnk.internal`;
  
  const newRequest = new Request(originUrl, request);
  newRequest.headers.set('X-DNK-Edge-Region', targetRegion);
  return fetch(newRequest);
}
"""

# Monitoring, Alerting & Hardening Reference Guide

## 1. Environment Configuration

```bash
# Slack Incoming Webhook
SLACK_ALERT_WEBHOOK_URL="https://hooks.slack.com.example/services/REDACTED_MOCK_WEBHOOK"

# PagerDuty Events API v2 (Routing Key for Critical alerts)
PAGERDUTY_ROUTING_KEY="pd-integration-routing-key"

# SMTP Email Configuration
SMTP_HOST="smtp.example.com"
SMTP_PORT=587
SMTP_USER="alerts@example.com"
SMTP_PASSWORD="secret-app-password"
SMTP_USE_TLS=true
ALERT_EMAIL_FROM="alerts@example.com"
ALERT_EMAIL_TO="oncall@example.com,devops@example.com"

# Cooldown Settings
ALERT_COOLDOWN_SECONDS=300

# Redis & Rate Limiting
REDIS_URL="redis://localhost:6379/0"
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

## 2. Prometheus Scraping & Alert Rules

### Prometheus Scrape Configuration (`prometheus.yml`)
```yaml
scrape_configs:
  - job_name: 'dnk-os-api'
    scrape_interval: 15s
    scrape_timeout: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['api:8000']
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Core Alert Rules (`alert_rules.yml`)
```yaml
groups:
  - name: dnk_os_critical_alerts
    rules:
      - alert: HighErrorRate
        expr: (rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) * 100 > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "API Error rate exceeds 5%"

      - alert: HighLatency
        expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency exceeds 1 second"

      - alert: DatabaseConnectionPoolExhausted
        expr: (pg_stat_activity_count / pg_settings_max_connections) * 100 > 90
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL connection pool > 90%"
```

## 3. Multi-Channel Alert Payload Schemas

### Slack Block Kit Payload
```json
{
  "text": "[CRITICAL] Database Connection Pool Exhausted",
  "attachments": [
    {
      "color": "#D32F2F",
      "blocks": [
        {
          "type": "header",
          "text": {"type": "plain_text", "text": "🚨 [CRITICAL] Database Connection Pool Exhausted"}
        },
        {
          "type": "section",
          "fields": [
            {"type": "mrkdwn", "text": "*Service:* `dnk-api`"},
            {"type": "mrkdwn", "text": "*Component:* `db_pool`"},
            {"type": "mrkdwn", "text": "*Timestamp:* `2026-09-05T12:00:00Z`"}
          ]
        }
      ]
    }
  ]
}
```

### PagerDuty Events API v2 Payload
```json
{
  "routing_key": "pd-integration-routing-key",
  "event_action": "trigger",
  "dedup_key": "dnk-api:db_pool:connection_exhausted",
  "payload": {
    "summary": "[CRITICAL] Database connection pool > 90%",
    "source": "dnk-os-production",
    "severity": "critical",
    "component": "database",
    "group": "infra",
    "custom_details": {
      "pool_utilization": "94%",
      "active_connections": 188
    }
  }
}
```

## 4. Sliding Window Rate Limiting (Redis Pattern)

```python
import time
from typing import Tuple

def check_sliding_window_limit(
    redis_client,
    key: str,
    max_requests: int = 100,
    window_seconds: int = 60
) -> Tuple[bool, int, int]:
    """
    Returns (is_allowed, remaining_quota, reset_time_seconds).
    Uses atomic Redis pipeline with sorted sets (ZSET).
    """
    now = time.time()
    window_start = now - window_seconds
    pipeline = redis_client.pipeline()
    pipeline.zremrangebyscore(key, 0, window_start)
    pipeline.zcard(key)
    pipeline.zadd(key, {str(now): now})
    pipeline.expire(key, window_seconds + 5)
    _, current_count, _, _ = pipeline.execute()

    if current_count >= max_requests:
        return False, 0, int(window_seconds)
    return True, max_requests - (current_count + 1), int(window_seconds)
```

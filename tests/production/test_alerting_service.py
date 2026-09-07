# --- DNK-MRH-HEADER ---
# mrh_id: "tests/production/test_alerting_service.py"
# purpose: "Unit tests for Production Alerting Service (PagerDuty + Slack + deduplication)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from services.alerting_service import Alert, AlertingService


@pytest.mark.asyncio
async def test_send_critical_alert():
    service = AlertingService()
    alert = Alert(
        severity="critical",
        title="Database Down",
        description="PostgreSQL is not responding",
        source="postgres",
        timestamp="2026-09-05T19:45:00Z",
    )

    result = await service.send_alert(alert)
    assert result is True


@pytest.mark.asyncio
async def test_send_warning_alert():
    service = AlertingService()
    alert = Alert(
        severity="warning",
        title="High Memory Usage",
        description="Memory usage is 85%",
        source="node",
        timestamp="2026-09-05T19:45:00Z",
    )

    result = await service.send_alert(alert)
    assert result is True


@pytest.mark.asyncio
async def test_deduplication():
    service = AlertingService()
    alert = Alert(
        severity="critical",
        title="Test Alert",
        description="Testing deduplication",
        source="test",
        timestamp="2026-09-05T19:45:00Z",
    )

    # First send
    result1 = await service.send_alert(alert)
    assert result1 is True

    # Second send (deduplicated)
    result2 = await service.send_alert(alert)
    assert result2 is False

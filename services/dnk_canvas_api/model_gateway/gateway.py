# --- DNK-MRH-HEADER ---
# mrh_id: "model_gateway/gateway.py"
# purpose: "DNK Model Gateway orchestrating routing, budgeting, retry policies, sanitization, and shadow testing."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Dict, Any, Optional

from .routing import ModelRoutingManager
from .budgets import BudgetManager
from .retries import ModelGatewayRetrier
from .redaction import SecurityRedactor
from .telemetry import GatewayTelemetryTracker
from ..providers.factory import factory
from ..providers.types import ProviderResult, UsageMetrics

logger = logging.getLogger("model_gateway")

class DNKModelGateway:
    @staticmethod
    async def request_generation(
        db,
        supervisor_run_id: str,
        system_prompt: str,
        messages: list,
        response_schema: Dict[str, Any],
        tools: Optional[list] = None
    ) -> ProviderResult:
        logger.info(f"Model Gateway request initiated for run {supervisor_run_id}")

        # 1. Redact inputs
        sanitized_messages = SecurityRedactor.sanitize_messages(messages)

        # 2. Routing Resolution
        provider_name, model_name = ModelRoutingManager.resolve_provider_and_model()

        # 3. Budget Check (Estimate cost at 0.01$ for check)
        # Fetch spent tokens for this run if any exists, but we verify here
        BudgetManager.check_and_track_budget(current_spent_usd=0.0, expected_call_cost_usd=0.01)

        # 4. Record Telemetry Request
        request_db_id = GatewayTelemetryTracker.record_request(
            db,
            supervisor_run_id=supervisor_run_id,
            provider=provider_name,
            model=model_name,
            system_prompt=system_prompt,
            messages=sanitized_messages
        )

        async def make_call() -> ProviderResult:
            prov = factory.get_provider(provider_name)
            return await prov.generate_structured(
                model=model_name,
                system_prompt=system_prompt,
                messages=sanitized_messages,
                response_schema=response_schema,
                tools=tools
            )

        async def fallback_call() -> ProviderResult:
            # Fallback to Claude if primary fails
            prov = factory.get_provider("anthropic_claude")
            return await prov.generate_structured(
                model="claude-3-5-sonnet",
                system_prompt=system_prompt,
                messages=sanitized_messages,
                response_schema=response_schema,
                tools=tools
            )

        # 5. Execute with retry guard
        try:
            result = await ModelGatewayRetrier.execute_with_retry_and_fallback(
                make_call,
                fallback_call,
                max_retries=2,
                timeout_seconds=5
            )
            
            # Record response success
            GatewayTelemetryTracker.record_response(
                db,
                request_id=request_db_id,
                status="success",
                output_data=result.output,
                input_tokens=result.usage.input_tokens,
                output_tokens=result.usage.output_tokens,
                latency_ms=result.latency_ms,
                cost_estimate=result.usage.cost_usd
            )
            return result
        except Exception as e:
            logger.error(f"Model Gateway call failed: {e}")
            GatewayTelemetryTracker.record_response(
                db,
                request_id=request_db_id,
                status="failed",
                output_data=None,
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                cost_estimate=0.0,
                error_code=str(e)[:64]
            )
            raise e

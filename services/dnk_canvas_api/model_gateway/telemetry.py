# --- DNK-MRH-HEADER ---
# mrh_id: "model_gateway/telemetry.py"
# purpose: "Record LLM request logs, outputs, and provider usage metrics into the database."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import json
import hashlib
from uuid import uuid4
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..main import LlmRequest, LlmOutput, ProviderUsage, ModelToolCall

class GatewayTelemetryTracker:
    @staticmethod
    def record_request(
        db,
        supervisor_run_id: str,
        provider: str,
        model: str,
        system_prompt: str,
        messages: list,
    ) -> str:
        # Calculate input hash
        input_data = {
            "system_prompt": system_prompt,
            "messages": messages
        }
        input_str = json.dumps(input_data, sort_keys=True)
        input_hash = hashlib.sha256(input_str.encode("utf-8")).hexdigest()

        req = LlmRequest(
            id=str(uuid4()),
            supervisor_run_id=supervisor_run_id,
            provider=provider,
            model=model,
            request_id=f"req-{str(uuid4())[:8]}",
            status="pending",
            input_hash=input_hash
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req.id

    @staticmethod
    def record_response(
        db,
        request_id: str,
        status: str,
        output_data: Optional[Dict[str, Any]],
        input_tokens: int,
        output_tokens: int,
        latency_ms: int,
        cost_estimate: float,
        error_code: Optional[str] = None
    ):
        req = db.query(LlmRequest).filter(LlmRequest.id == request_id).first()
        if not req:
            return

        req.status = status
        db.commit()

        # Save output hash
        output_str = json.dumps(output_data, sort_keys=True) if output_data else "{}"
        output_hash = hashlib.sha256(output_str.encode("utf-8")).hexdigest()

        if output_data:
            out = LlmOutput(
                id=str(uuid4()),
                llm_request_id=req.id,
                status=status,
                output_hash=output_hash,
                output_json=output_data
            )
            db.add(out)

        # Save Usage metrics
        usage = ProviderUsage(
            id=str(uuid4()),
            llm_request_id=req.id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_estimate=cost_estimate,
            error_code=error_code
        )
        db.add(usage)
        db.commit()

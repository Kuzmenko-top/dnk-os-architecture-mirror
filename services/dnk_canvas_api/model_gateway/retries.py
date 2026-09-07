# --- DNK-MRH-HEADER ---
# mrh_id: "model_gateway/retries.py"
# purpose: "Implement retry policy, timeout handling, and fallback routing from primary to secondary provider."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import logging
import asyncio
from typing import Callable, Any

logger = logging.getLogger("gateway_retries")

class ModelGatewayRetrier:
    @staticmethod
    async def execute_with_retry_and_fallback(
        fn: Callable, 
        fallback_fn: Callable,
        max_retries: int = 2,
        timeout_seconds: int = 10
    ) -> Any:
        attempts = 0
        while attempts < max_retries:
            try:
                # Execute primary provider call with explicit timeout guard
                return await asyncio.wait_for(fn(), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                attempts += 1
                logger.warning(f"Primary provider timeout on attempt {attempts}/{max_retries}. Retrying...")
            except Exception as e:
                attempts += 1
                logger.warning(f"Primary provider error on attempt {attempts}/{max_retries}: {e}. Retrying...")
                await asyncio.sleep(0.5)

        # Fallback to secondary provider after max retries are exhausted
        logger.warning("Primary provider exhausted. Falling back to secondary provider...")
        return await asyncio.wait_for(fallback_fn(), timeout=timeout_seconds)

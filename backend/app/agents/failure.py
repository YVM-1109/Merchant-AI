"""
FailureAgent — Error recovery and retry logic.

Handles transient failures in the agent graph:
- Retry Razorpay API calls with exponential backoff
- Queue failed operations for later retry
- Notify user of persistent failures
"""
import asyncio
import logging
from uuid import uuid4
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class FailureAgent:
    """Retry wrapper with exponential backoff for transient errors."""

    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds

    @staticmethod
    async def retry_async(
        func: Callable,
        *args,
        max_retries: int = MAX_RETRIES,
        **kwargs,
    ) -> Optional[object]:
        """Retry an async function with exponential backoff.

        Args:
            func: The async function to call.
            *args: Positional arguments for func.
            max_retries: Maximum number of retry attempts.
            **kwargs: Keyword arguments for func.

        Returns:
            The result of func, or None if all retries fail.
        """
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                last_error = exc
                delay = FailureAgent.BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    f"Attempt {attempt}/{max_retries} failed: {exc}. Retrying in {delay}s..."
                )
                if attempt < max_retries:
                    await asyncio.sleep(delay)

        logger.error(f"All {max_retries} retries failed. Last error: {last_error}")
        return None

    @staticmethod
    async def queue_for_retry(
        action_type: str,
        payload: dict,
        reason: str,
        delay_seconds: int = 300,
    ) -> dict:
        """Queue a failed action for retry via Redis.

        Uses Redis as a delayed task queue.
        """
        import json
        import redis.asyncio as aioredis
        from app.config import settings

        redis = aioredis.from_url(settings.REDIS_URL)
        task_key = f"retry:{action_type}:{uuid4().hex[:8]}"

        task = {
            "action_type": action_type,
            "payload": payload,
            "reason": reason,
            "attempt": 1,
        }

        await redis.setex(task_key, delay_seconds, json.dumps(task))
        await redis.close()

        return {"queued": True, "task_key": task_key}

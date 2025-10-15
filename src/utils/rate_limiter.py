"""Rate limiting utilities for Google Workspace API calls."""

import asyncio
import time
from typing import Dict, Optional
from collections import deque
from .logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    """Rate limiter for API calls with sliding window algorithm."""

    def __init__(
        self,
        max_requests: int = 100,
        time_window: int = 60,
        burst_limit: int = 10
    ):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds
            burst_limit: Maximum consecutive requests without delay
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_limit = burst_limit
        self.requests: deque = deque()
        self.lock = asyncio.Lock()

    async def acquire(self, service: str = "default") -> bool:
        """Acquire permission to make an API call.

        Args:
            service: Service name for tracking

        Returns:
            True if request is allowed, False otherwise
        """
        async with self.lock:
            now = time.time()

            # Remove expired requests from window
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()

            # Check if limit exceeded
            if len(self.requests) >= self.max_requests:
                wait_time = self.requests[0] + self.time_window - now
                logger.warning(
                    f"Rate limit reached for {service}. "
                    f"Waiting {wait_time:.2f}s"
                )
                await asyncio.sleep(wait_time)
                return await self.acquire(service)

            # Check burst limit
            if len(self.requests) >= self.burst_limit:
                recent_requests = [
                    r for r in self.requests
                    if r > now - 1.0  # Last second
                ]
                if len(recent_requests) >= self.burst_limit:
                    await asyncio.sleep(0.1)  # Small delay

            # Record request
            self.requests.append(now)
            return True

    def get_stats(self) -> Dict[str, any]:
        """Get current rate limiter statistics.

        Returns:
            Dictionary with statistics
        """
        now = time.time()
        active_requests = [
            r for r in self.requests
            if r > now - self.time_window
        ]

        return {
            "active_requests": len(active_requests),
            "max_requests": self.max_requests,
            "time_window": self.time_window,
            "utilization": len(active_requests) / self.max_requests
        }


# Global rate limiter instances per service
_rate_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(service: str, **kwargs) -> RateLimiter:
    """Get or create rate limiter for a service.

    Args:
        service: Service name
        **kwargs: RateLimiter initialization parameters

    Returns:
        RateLimiter instance
    """
    if service not in _rate_limiters:
        _rate_limiters[service] = RateLimiter(**kwargs)
    return _rate_limiters[service]


async def rate_limited_call(service: str, func, *args, **kwargs):
    """Execute a function with rate limiting.

    Args:
        service: Service name for rate limiting
        func: Function to execute
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Result of func execution
    """
    limiter = get_rate_limiter(service)
    await limiter.acquire(service)

    if asyncio.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return func(*args, **kwargs)

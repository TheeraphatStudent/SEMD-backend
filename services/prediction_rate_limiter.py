"""Redis-backed fixed-window limits for anonymous prediction requests."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from redis.exceptions import RedisError

from services.client.redis_client import redis_client


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int


class RateLimiterUnavailableError(RuntimeError):
    """Raised when the shared limiter cannot protect the endpoint."""


class PredictionRateLimiter:
    """Count requests per hashed caller key in a shared Redis window."""

    def __init__(
        self,
        client=None,
        *,
        max_requests: int = 20,
        window_seconds: int = 60,
    ) -> None:
        if max_requests < 1:
            raise ValueError('max_requests must be at least 1')
        if window_seconds < 1:
            raise ValueError('window_seconds must be at least 1')

        self.client = client or redis_client.client
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    def check(self, client_identifier: str) -> RateLimitResult:
        key = self._key(client_identifier)
        try:
            request_count = self.client.incr(key)
            if request_count == 1:
                self.client.expire(key, self.window_seconds)

            remaining_window = self.client.ttl(key)
            if remaining_window < 1:
                self.client.expire(key, self.window_seconds)
                remaining_window = self.window_seconds
        except RedisError as error:
            raise RateLimiterUnavailableError(
                'prediction rate limiter unavailable') from error

        return RateLimitResult(
            allowed=request_count <= self.max_requests,
            retry_after_seconds=remaining_window,
        )

    @staticmethod
    def _key(client_identifier: str) -> str:
        digest = sha256(client_identifier.encode('utf-8')).hexdigest()
        return f"prediction-rate-limit:{digest}"

"""Redis client for caching and queue operations."""

import json
from typing import Optional, Any

import redis

from config.settings import settings


class RedisClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisClient, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'client'):
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                db=settings.redis_db,
                decode_responses=True,
            )

    def push_to_queue(self, queue_name: str, data: dict) -> int:
        """Push data to a Redis queue (list)."""
        return self.client.lpush(queue_name, json.dumps(data))

    def pop_from_queue(self, queue_name: str, timeout: int = 0) -> Optional[dict]:
        """Pop data from a Redis queue (blocking)."""
        result = self.client.brpop(queue_name, timeout=timeout)
        if result:
            _, data = result
            return json.loads(data)
        return None

    def get_cache(self, key: str) -> Optional[dict]:
        """Get cached data by key."""
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def set_cache(self, key: str, data: Any, ttl: int = 3600) -> bool:
        """Set cached data with TTL (default 1 hour)."""
        return self.client.setex(key, ttl, json.dumps(data))

    def delete_cache(self, key: str) -> int:
        """Delete cached data by key."""
        return self.client.delete(key)


redis_client = RedisClient()

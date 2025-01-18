import json
from typing import Any, Optional, Union


from pomdapi.core.types import TResponse
from pomdapi.core.api import EndpointDefinitionGen
from pomdapi.core.caching import Cache

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

class RedisBackend:

    def __init__(self, host: str = "127.0.0.1", port: int = 6379):
        self._host = host
        self._port = port

        # Synchronous redis client
        self._sync_client = Redis(host=host, port=port)

        # Asynchronous aioredis client
        self._async_client = AsyncRedis(host=host, port=port)

    def _serialize(self, value: Any) -> bytes:
        """
        Convert a dictionary or string to bytes for storing in Redis.
        """
        return json.dumps(value).encode("utf-8")

    def _deserialize(self, raw_data: Optional[bytes]) -> Optional[Union[dict[str, Any], str]]:
        """
        Convert raw bytes from Redis into either a dict or a string.
        Returns None if data is None.
        """
        if raw_data is None:
            return None
        text = raw_data.decode("utf-8", errors="replace")
        # Attempt to parse JSON; if it fails, treat as plain string.
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def delete(self, key: str) -> None:
        """Delete a key from the cache (sync)."""
        self._sync_client.delete(key)

    def get(self, key: str) -> Any:
        """Get a key from the cache (sync)."""
        raw_data = self._sync_client.get(key)
        return self._deserialize(raw_data)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a key in the cache with an optional TTL (sync).
        TTL is in seconds; memcache.Client.set uses 'time' for expiry.
        """
        data = self._serialize(value)
        self._sync_client.set(key, data, ex=ttl if ttl else 0)

    async def adelete(self, key: str) -> None:
        """Delete a key from the cache (async)."""
        await self._async_client.delete(key)

    async def aget(self, key: str) -> Any:
        """Get a key from the cache (async)."""
        raw_data = await self._async_client.get(key)
        return self._deserialize(raw_data)

    async def aset(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a key in the cache with an optional TTL (async).
        aiomcache.Client.set uses 'exptime' for expiry in seconds.
        """
        data = self._serialize(value)
        exptime = ttl if ttl else 0
        await self._async_client.set(key, data, ex=exptime)


class RedisCache(Cache[EndpointDefinitionGen, TResponse]):  
    """
    A Cache class that uses the RedisBackend for both sync and async caching.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 6379, ttl: int = 60):
        super().__init__(_backend=RedisBackend(host=host, port=port), _ttl=ttl)

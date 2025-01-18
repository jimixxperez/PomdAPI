import json
from dataclasses import dataclass
from typing import Any, Optional, Generic, Union


from pomdapi.core.types import TResponse
from pomdapi.core.api import EndpointDefinitionGen
from pomdapi.core.caching import Cache


@dataclass
class CachedItem(Generic[TResponse]):
    value: TResponse
    ttl: Optional[int]
    timestamp: int


class MemcachedBackend:
    """
    A Memcached-based cache backend
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 11211):
        self._host = host
        self._port = port

        # Synchronous memcache client
        self._sync_client = memcache.Client([f"{host}:{port}"])

        # Asynchronous aiomcache client
        self._async_client = aiomcache.Client(host.encode("utf-8"), port)

    def _serialize(self, value: Union[dict[str, Any], str]) -> bytes:
        """
        Convert a dictionary or string to bytes for storing in Memcached.
        """
        if isinstance(value, dict):
            # Store as JSON
            return json.dumps(value).encode("utf-8")
        elif isinstance(value, str):
            return value.encode("utf-8")
        else:
            raise TypeError("Value must be a dict or a string.")

    def _deserialize(self, raw_data: Optional[bytes]) -> Optional[Union[dict[str, Any], str]]:
        """
        Convert raw bytes from Memcached into either a dict or a string.
        Returns None if data is None.
        """
        if raw_data is None:
            return None
        text = raw_data.decode("utf-8", errors="replace")
        # Attempt to parse JSON; if it fails, treat as plain string.
        try:
#            return json.loads(text)
        except json.JSONDecodeError:
            return text

    # ----------------------------
    # Synchronous methods
    # ----------------------------
    def delete(self, key: str) -> None:
        """Delete a key from the cache (sync)."""
        self._sync_client.delete(key)

    def get(self, key: str) -> Optional[Union[dict[str, Any], str]]:
        """Get a key from the cache (sync)."""
        raw_data = self._sync_client.get(key)
        return self._deserialize(raw_data)

    def set(self, key: str, value: Union[dict[str, Any], str], ttl: Optional[int] = None) -> None:
        """
        Set a key in the cache with an optional TTL (sync).
        TTL is in seconds; memcache.Client.set uses 'time' for expiry.
        """
        data = self._serialize(value)
        self._sync_client.set(key, data, time=ttl if ttl else 0)

    # ----------------------------
    # Asynchronous methods
    # ----------------------------
    async def adelete(self, key: str) -> None:
        """Delete a key from the cache (async)."""
        await self._async_client.delete(key.encode("utf-8"))

    async def aget(self, key: str) -> Optional[Union[dict[str, Any], str]]:
        """Get a key from the cache (async)."""
        raw_data = await self._async_client.get(key.encode("utf-8"))
        return self._deserialize(raw_data)

    async def aset(self, key: str, value: Union[dict[str, Any], str], ttl: Optional[int] = None) -> None:
        """
        Set a key in the cache with an optional TTL (async).
        aiomcache.Client.set uses 'exptime' for expiry in seconds.
        """
        data = self._serialize(value)
        exptime = ttl if ttl else 0
        await self._async_client.set(key.encode("utf-8"), data, exptime=exptime)


class MemcachedCache(Cache[EndpointDefinitionGen, TResponse]):
    """
    A Cache class that uses the MemcachedBackend for both sync and async caching.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 11211):
        super().__init__(_backend=MemcachedBackend(host=host, port=port))




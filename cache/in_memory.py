import time
from dataclasses import dataclass
from typing import Any, Generic, Optional
from core.types import (
    TResponse,
)
from core.api import EndpointDefinitionGen
from core.caching import Cache

@dataclass
class CachedItem(Generic[TResponse]):
    value: TResponse
    ttl: Optional[int]
    timestamp: int


class InMemoryBackend:
    """In memory cache backend."""
    def __init__(self):
        self._store: dict[str, CachedItem[dict[str, Any] | str]] = {}

    def delete(self, key: str) -> None:
        """"Delete a key from the cache."""
        try:
            del self._store[key]
        except KeyError:
            print("key not found")

    async def adelete(self, key: str) -> None:
        """"Delete a key from the cache."""
        return self.delete(key)

    def get(self, key: str) -> Optional[dict[str, Any] | str]:
        """"Get a key from the cache."""
        cached_item = self._store.get(key)
        if cached_item is None:
            return None

        if cached_item.ttl is None or cached_item.timestamp is None:
            return cached_item.value

        timestamp = cached_item.timestamp
        ttl = cached_item.ttl
        req = cached_item.value
        if timestamp + ttl < time.time():
            self.delete(key)
            return None
        return req


    async def aget(self, key: str) -> Optional[dict[str, Any] | str]:
        """"Get a key from the cache."""
        return self.get(key)

    def set(self, key: str, value: dict[str, Any] | str, ttl: Optional[int] = None) -> None:
        """"Set a key in the cache."""
        self._store[key] = CachedItem(value, ttl, int(time.time()))

    async def aset(self, key: str, value: dict[str, Any] | str, ttl: Optional[int] = None) -> None:
        """"Set a key in the cache."""
        self.set(key, value, ttl)


class InMemoryCache(Cache[EndpointDefinitionGen, TResponse]):
    def __init__(self):
        super().__init__(_backend=InMemoryBackend())

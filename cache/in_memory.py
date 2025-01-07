from dataclasses import dataclass
from typing import Generic, Iterable, Optional
from core.types import (
    SyncCachingStrategy,
    AyncCachingStrategy,
    TResponse,
    Tag,
)
from core.api import EndpointDefinitionGen
from core.caching import Cache


class InMemoryBackend(Generic[TResponse]):
    def __init__(self):
        self._store: dict[str, TResponse] = {}

    def delete(self, key: str) -> None:
        del self._store[key]

    async def adelete(self, key: str) -> None:
        return self.delete(key)

    def get(self, key: str) -> Optional[TResponse]:
        return self._store.get(key)

    async def aget(self, key: str) -> Optional[TResponse]:
        return self.get(key)

    def set(self, key: str, value: TResponse, ttl: Optional[int] = None) -> None:
        self._store[key] = value

    async def aset(self, key: str, value: TResponse, ttl: Optional[int] = None) -> None:
        self.set(key, value)


class InMemoryCache(Cache[EndpointDefinitionGen, TResponse]):
    def __init__(self):
        super().__init__(_backend=InMemoryBackend[TResponse]())

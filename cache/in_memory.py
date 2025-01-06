from dataclasses import dataclass
from typing import Generic, Iterable, Optional
from core.types import (
    SyncCachingStrategy,
    AyncCachingStrategy,
    EndpointDefinitionGen,
    TResponse,
    Tag,
)


class InMemoryKVStore(Generic[TResponse]):
    def __init__(self):
        self._store: dict[str, TResponse] = {}

    def delete(self, key: str) -> None:
        del self._store[key]

    def get(self, key: str) -> Optional[TResponse]:
        return self._store.get(key)

    async def aget(self, key: str) -> Optional[TResponse]:
        return self.get(key)

    def set(self, key: str, value: TResponse) -> None:
        self._store[key] = value

    def aset(self, key: str, value: TResponse) -> None:
        self.set(key, value)


@dataclass
class InMemoryCache(
    Generic[EndpointDefinitionGen, TResponse],
):
    _cache: dict[str, TResponse]

    def get(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
        tags: Iterable[str | Tag],
    ) -> Optional[TResponse]: ...

    def aget(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
        tags: Iterable[str | Tag],
    ): ...

    async def aset(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
        response: TResponse,
        tags: Iterable[str | Tag],
    ) -> None: ...

    def invalidate_tags(self, tags: Iterable[str | Tag]) -> None: ...

    async def ainvalidate_tags(self, tags: Iterable[str | Tag]) -> None: ...

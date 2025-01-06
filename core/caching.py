from dataclasses import dataclass
from typing import Generic, Iterable, Protocol, Optional

from core.api import EndpointDefinitionGen
from core.types import TResponse, Tag


class CacheBackend(Protocol[TResponse]):
    def delete(self, key: str) -> None: ...

    def get(self, key: str) -> Optional[TResponse]: ...

    async def aget(self, key: str) -> Optional[TResponse]: ...

    def set(self, key: str, value: TResponse, ttl: Optional[int] = None) -> None: ...

    def aset(self, key: str, value: TResponse, ttl: Optional[int] = None) -> None: ...


@dataclass
class Cache(Generic[EndpointDefinitionGen, TResponse]):
    _backend: CacheBackend[TResponse]

    def get_by_request(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
    ) -> Optional[TResponse]:
        key = f"{endpoint_name}/{request}"
        return self._backend.get(key)

    def get_by_tags(
        self,
        endpoint_name: str,
        tags: Iterable[str | Tag],
    ) -> Optional[TResponse]:
        for tag in tags:
            key = f"{endpoint_name}/tags/{tag}"
            if response := self._backend.get(key):
                return response

import asyncio
from dataclasses import dataclass, field
from typing import Generic, Iterable, Protocol, Optional

from core.types import TResponse, Tag, EndpointDefinitionGen
from core.rw_lock import AsyncRWLock


class CacheBackend(Protocol[TResponse]):
    def delete(self, key: str) -> None: ...

    async def adelete(self, key: str) -> None: ...

    def get(self, key: str) -> Optional[TResponse]: ...

    async def aget(self, key: str) -> Optional[TResponse]: ...

    def set(self, key: str, value: TResponse, ttl: Optional[int] = None) -> None: ...

    async def aset(
        self, key: str, value: TResponse, ttl: Optional[int] = None
    ) -> None: ...


@dataclass
class Cache(Generic[EndpointDefinitionGen, TResponse]):
    _backend: CacheBackend[TResponse]

    @staticmethod
    def key_from_req(endpoint_name: str, request: EndpointDefinitionGen) -> str:
        return f"{endpoint_name}/{request}"

    @staticmethod
    def key_from_tag(endpoint_name: str, tag: str | Tag) -> str:
        return f"{endpoint_name}/tag/{tag}"

    def get_by_request(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
    ) -> Optional[TResponse]:
        key = self.key_from_req(endpoint_name, request)
        return self._backend.get(key)

    async def aget_by_request(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
    ) -> Optional[TResponse]:
        """Get a response from the cache by request."""
        key = self.key_from_req(endpoint_name, request)
        return await self._backend.aget(key)

    def get_by_tags(
        self,
        endpoint_name: str,
        tags: Iterable[str | Tag],
    ) -> Optional[TResponse]:
        """Get a response from the cache by tags."""
        for tag in tags:
            key = self.key_from_tag(endpoint_name, tag)
            if response := self._backend.get(key):
                return response

    async def aget_by_tags(
        self,
        endpoint_name: str,
        tags: Iterable[str | Tag],
    ) -> Optional[TResponse]:
        """Get a response from the cache by tags."""
        for tag in tags:
            key = self.key_from_tag(endpoint_name, tag)
            if response := await self._backend.aget(key):
                return response

    async def aset(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
        tags: Iterable[str | Tag],
        response: TResponse,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a response in the cache."""
        key = self.key_from_req(endpoint_name, request)
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._backend.aset(key, response, ttl=ttl))
            for tag in tags:
                key = self.key_from_tag(endpoint_name, tag)
                tg.create_task(self._backend.aset(key, response, ttl=ttl))

    def invalidate_tags(self, endpoint_name: str, tags: Iterable[str | Tag]) -> None:
        """Invalidate a response from the cache by tags."""
        for tag in tags:
            key = self.key_from_tag(endpoint_name, tag)
            self._backend.delete(key)

    async def ainvalidate_tags(
        self, endpoint_name: str, tags: Iterable[str | Tag]
    ) -> None:
        """Invalidate a response from the cache by tags."""
        async with asyncio.TaskGroup() as tg:
            for tag in tags:
                key = self.key_from_tag(endpoint_name, tag)
                tg.create_task(self._backend.adelete(key))


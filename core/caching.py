import asyncio
from dataclasses import dataclass, field
from typing import Any, Generic, Iterable, Protocol, Optional

from core.types import TResponse, Tag, EndpointDefinitionGen
from core.rw_lock import AsyncRWLock


class CacheBackend(Protocol):
    def delete(self, key: str) -> None: ...

    async def adelete(self, key: str) -> None: ...

    def get(self, key: str) -> Optional[Any]: ...

    async def aget(self, key: str) -> Optional[Any]: ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None: ...

    async def aset(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None: ...


@dataclass
class Cache(Generic[EndpointDefinitionGen, TResponse]):
    _backend: CacheBackend

    @staticmethod
    def key_from_req(endpoint_name: str, request: EndpointDefinitionGen) -> str:
        return f"{endpoint_name}/{request}"

    @staticmethod
    def key_from_tag(tag: str | Tag) -> str:
        return f"tag/{tag}"

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
            key = self.key_from_tag(tag)
            if response := self._backend.get(key):
                return response

    async def aget_by_tags(
        self,
        endpoint_name: str,
        tags: Iterable[str | Tag],
    ) -> Optional[TResponse]:
        """Get a response from the cache by tags."""
        for tag in tags:
            key = self.key_from_tag(tag)
            if response := await self._backend.aget(key):
                return response

    def set(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
        tags: Iterable[str | Tag],
        response: TResponse,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a response in the cache."""
        request_key = self.key_from_req(endpoint_name, request)
        self._backend.set(request_key, response, ttl=ttl)
        for tag in tags:
            key = self.key_from_tag(tag)
            self._backend.set(key, request_key, ttl=ttl)

    async def aset(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
        tags: Iterable[str | Tag],
        response: TResponse,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a response in the cache."""
        request_def_key = self.key_from_req(endpoint_name, request)
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._backend.aset(request_def_key, response, ttl=ttl))
            for tag in tags:
                key = self.key_from_tag(tag)
                tg.create_task(self._backend.aset(key, request_def_key, ttl=ttl))

    def invalidate_tags(self, endpoint_name: str, tags: Iterable[str | Tag]) -> None:
        """Invalidate a response from the cache by tags."""
        for i, tag in enumerate(tags):
            tag_key = self.key_from_tag(tag)
            if i == 0:
                if (request_key := self._backend.get(tag_key)):
                    self._backend.delete(request_key)
            self._backend.delete(tag_key)

    async def ainvalidate_tags(
        self, endpoint_name: str, tags: Iterable[str | Tag]
    ) -> None:
        """Invalidate a response from the cache by tags."""
        async with asyncio.TaskGroup() as tg:
            for i, tag in enumerate(tags):
                tag_key = self.key_from_tag(tag)
                if i == 0:
                    if (request_key := await self._backend.aget(tag_key)):
                        tg.create_task(self._backend.adelete(request_key))
                tg.create_task(self._backend.adelete(tag_key))


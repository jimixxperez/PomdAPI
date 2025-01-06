from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Generic,
    Optional,
    Protocol,
    Required,
    TypeVar,
    TypedDict,
)

TResponse = TypeVar("TResponse")
EndpointDefinitionGen = TypeVar("EndpointDefinitionGen", contravariant=True)

from typing import Iterable, ParamSpec

ReqDefinition = TypeVar("ReqDefinition")
P = ParamSpec("P")


@dataclass
class Tag:
    type: str
    id: Optional[str] = None


ProvidesTags = (
    tuple[ReqDefinition, (str | Tag | Iterable[str | Tag])]
    | tuple[ReqDefinition, Callable[P, str | Tag | Iterable[str | Tag]]]
)


@dataclass
class BaseQueryConfig:
    """Defines the base query configuration for the API."""

    base_url: Optional[str] = None
    prepare_headers: Callable[[dict[str, str]], dict[str, str]] = field(
        default_factory=lambda: lambda header: header
    )


@dataclass
class EndpointDefinition(Generic[EndpointDefinitionGen, P]):
    """Defines an endpoint for the API."""

    request_fn: (
        Callable[..., EndpointDefinitionGen]
        | Callable[..., ProvidesTags[EndpointDefinitionGen, P]]
    )
    is_query_endpoint: bool = True

    @property
    def is_query(self) -> bool:
        """Returns True if the endpoint is a query endpoint."""
        return self.is_query_endpoint

    @property
    def is_mutation(self) -> bool:
        """Returns True if the endpoint is a mutation endpoint."""
        return not self.is_query_endpoint


@dataclass
class CacheEntry(Generic[TResponse]):
    response: TResponse
    tags: list[str]
    timestamp: float


class SyncCachingStrategy(Protocol[EndpointDefinitionGen, TResponse]):
    """Defines a caching strategy for the API."""

    def get(
        self, endpoint_name: str, request: EndpointDefinitionGen
    ) -> Optional[TResponse]: ...

    def set(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
        response: TResponse,
        tags: list[str],
    ) -> None: ...

    def invalidate_tags(self, tags: list[str]) -> None: ...


class AyncCachingStrategy(Protocol[EndpointDefinitionGen, TResponse]):
    """Defines a caching strategy for the API."""

    def get(
        self, endpoint_name: str, request: EndpointDefinitionGen
    ) -> Optional[TResponse]: ...

    def aset(
        self,
        endpoint_name: str,
        request: EndpointDefinitionGen,
        response: TResponse,
        tags: list[str],
    ) -> None: ...

    def invalidate_tags(self, tags: list[str]) -> None: ...

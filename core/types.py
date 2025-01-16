from dataclasses import dataclass, field
from typing import (
    Callable,
    Generic,
    Optional,
    Protocol,
    TypeVar,
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
    tuple[EndpointDefinitionGen, (str | Tag | Iterable[str | Tag])]
    | tuple[EndpointDefinitionGen, Callable[P, str | Tag | Iterable[str | Tag]]]
)


@dataclass
class BaseQueryConfig:
    """Defines the base configuration for all API requests.
    
    This class holds common configuration that applies to all requests made through
    the API, such as base URL and header preparation.

    Attributes:
        base_url: The base URL for all API requests. If provided, this will be
                 prepended to all request paths.
        prepare_headers: A callable that takes and returns a headers dictionary.
                       Use this to add authentication, content-type, or other
                       headers to all requests.

    Example:
        ```python
        config = BaseQueryConfig(
            base_url="https://api.example.com/v1",
            prepare_headers=lambda headers: {
                **headers,
                "Authorization": f"Bearer {token}"
            }
        )
        ```
    """
    base_url: Optional[str] = None
    prepare_headers: Callable[[dict[str, str]], dict[str, str]] = field(
        default_factory=lambda: lambda header: header
    )


@dataclass
class EndpointDefinition(Generic[EndpointDefinitionGen]):
    """Defines an endpoint for the API."""

    request_fn: (
        Callable[..., EndpointDefinitionGen]
        | Callable[..., ProvidesTags[EndpointDefinitionGen, ...]]
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


class yncCachingStrategy(Protocol[EndpointDefinitionGen, TResponse]):
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

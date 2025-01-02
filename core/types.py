from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, Protocol, Required, TypeVar, TypedDict

TResponse = TypeVar('TResponse')
EndpointDefinitionGen = TypeVar("EndpointDefinitionGen")

@dataclass
class BaseQueryConfig:
    """Defines the base query configuration for the API."""
    base_url: Optional[str] = None
    prepare_headers: Callable[[dict[str, str]], dict[str, str]] = field(default_factory=lambda: lambda header: header)


@dataclass
class EndpointDefinition(Generic[EndpointDefinitionGen]):
    """Defines an endpoint for the API."""
    request_fn: Callable[..., EndpointDefinitionGen]
    provides_tags: list[str] = field(default_factory=list)
    invalidates_tags: list[str] = field(default_factory=list)
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

class CachingStrategy(Protocol[EndpointDefinitionGen, TResponse]):
    """Defines a caching strategy for the API."""
    def get(self, endpoint_name: str, request: EndpointDefinitionGen) -> Optional[TResponse]:
        raise NotImplementedError

    def set(self, endpoint_name: str, request: EndpointDefinitionGen, response: TResponse, tags: list[str]) -> None:
        raise NotImplementedError

    def invalidate_tags(self, tags: list[str]) -> None:
        raise NotImplementedError

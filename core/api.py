from dataclasses import dataclass
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Callable,
    Generic,
    Literal,
    Optional,
    ParamSpec,
    Protocol,
    Type,
    TypeVar,
    Concatenate,
)

from pydantic import BaseModel, field

from .types import (
    TResponse,
    BaseQueryConfig,
    EndpointDefinition,
    CachingStrategy,
    RequestDefinition,
)


QueryParam = ParamSpec("QueryParam")
QueryResponse = TypeVar("QueryResponse", bound=BaseModel)


import asyncio
from typing import overload, Awaitable


def decorator(
    fn: Callable[QueryParam, RequestDefinition]
) -> Callable[Concatenate[bool, QueryParam], asyncio.Future[str] | str]:
    async def _arun() -> str:
        ...

    def _run() -> str:
        ...

    @overload
    def _call(
        is_async: Literal[False], *args: QueryParam.args, **kwargs: QueryParam.kwargs
    ) -> str:
        ...

    @overload
    def _call(
        is_async: Literal[True], *args: QueryParam.args, **kwargs: QueryParam.kwargs
    ) -> asyncio.Future[str]:
        ...

    @overload
    def _call(
        is_async: bool, *args: QueryParam.args, **kwargs: QueryParam.kwargs
    ) -> asyncio.Future[str] | str:
        ...

    def _call(
        is_async: bool = False, *args: QueryParam.args, **kwargs: QueryParam.kwargs
    ) -> asyncio.Future[str] | str:
        if is_async:
            req_def = fn(*args, **kwargs)
            return asyncio.ensure_future(_arun())
        return _run()

    return _call


@decorator
def fn(a: str, b: int) -> RequestDefinition:
    ...


fn(True, "2", 1)


RequestDefinitionCallable = Callable[QueryParam, RequestDefinition]


class SyncAsync(Protocol[QueryParam, QueryResponse]):
    @overload
    def __call__(
        self,
        is_async: Literal[False],
        *args: QueryParam.args,
        **kwargs: QueryParam.kwargs,
    ) -> QueryResponse:
        ...

    @overload
    def __call__(
        self,
        is_async: Literal[True],
        *args: QueryParam.args,
        **kwargs: QueryParam.kwargs,
    ) -> asyncio.Future[QueryResponse]:
        ...

    @overload
    def __call__(
        self,
        is_async: bool,
        *args: QueryParam.args,
        **kwargs: QueryParam.kwargs,
    ) -> asyncio.Future[QueryResponse] | QueryResponse:
        ...


EndpointDefinitionGen = TypeVar("EndpointDefinitionGen", covariant=True)


@dataclass
class Api(Generic[EndpointDefinitionGen, TResponse]):
    """
    The Api class is the main entry point for interacting with the API.
    It provides a simple interface for defining query and mutation endpoints.
    """

    base_query_config: BaseQueryConfig
    base_query_fn_handler: Optional[
        Callable[[BaseQueryConfig, EndpointDefinitionGen], TResponse]
    ] = None
    base_query_fn_handler_async: Optional[
        Callable[[BaseQueryConfig, EndpointDefinitionGen], asyncio.Future[TResponse]]
    ] = None
    endpoints: dict[str, EndpointDefinition] = field(default_factory=dict)
    cache_strategy: Optional[CachingStrategy[TResponse]] = None

    def base_query_fn(
        self, fn: Callable[[BaseQueryConfig, EndpointDefinitionGen], TResponse]
    ) -> Callable[[BaseQueryConfig, EndpointDefinitionGen], TResponse]:
        """Decorator to register a base query function."""
        if not self.base_query_fn_handler:
            self.base_query_fn_handler = fn
        return fn

    def query(
        self,
        name: str,
        response_type: Type[QueryResponse],
        provides_tags: Optional[list[str]] = None,
    ) -> Callable[
        [Callable[QueryParam, EndpointDefinitionGen]],
        SyncAsync[QueryParam, QueryResponse],
    ]:
        """Decorator to register a query endpoint.
        The decorated function will execute the query and return the response.
        """

        def decorator(
            fn: Callable[QueryParam, EndpointDefinitionGen]
        ) -> SyncAsync[QueryParam, QueryResponse]:

            endpoint = EndpointDefinition(
                request_fn=fn,
                provides_tags=provides_tags or [],
                is_query_endpoint=True,
            )
            self.endpoints[name] = endpoint

            if TYPE_CHECKING:

                @overload
                def wrapper(
                    is_async: Literal[False],
                    *args: QueryParam.args,
                    **kwargs: QueryParam.kwargs,
                ) -> QueryResponse:
                    return response_type.model_validate(
                        self.run_query(name, *args, **kwargs)
                    )

                @overload
                def wrapper(
                    is_async: Literal[True],
                    *args: QueryParam.args,
                    **kwargs: QueryParam.kwargs,
                ) -> asyncio.Future[QueryResponse]:
                    return response_type.model_validate(
                        self.run_query(name, *args, **kwargs)
                    )

                @overload
                def wrapper(
                    is_async: bool, *args: QueryParam.args, **kwargs: QueryParam.kwargs
                ) -> asyncio.Future[QueryResponse] | QueryResponse:
                    ...

            @wraps(fn)
            def wrapper(
                is_async: bool,
                *args: QueryParam.args,
                **kwargs: QueryParam.kwargs,
            ) -> asyncio.Future[QueryResponse] | QueryResponse:
                if is_async:
                    return response_type.model_validate(
                        self.run_query(name, *args, **kwargs)
                    )

                async def _run() -> QueryResponse:
                    response = await self.arun_query(name, *args, **kwargs)
                    return response_type.model_validate(response)

                return asyncio.ensure_future(_run())

            return wrapper

        return decorator

    async def arun_query(self, endpoint_name: str, *args, **kwargs) -> TResponse:
        ...

    def mutation(self, name: str, invalidates_tags: Optional[list[str]] = None):
        """Decorator to register a mutation endpoint.
        The decorated function will execute the mutation and return the response.
        """

        def decorator(fn: Callable[..., RequestDefinition]):
            endpoint = EndpointDefinition(
                request_fn=fn,
                invalidates_tags=invalidates_tags or [],
                is_query_endpoint=False,
            )
            self.endpoints[name] = endpoint

            @wraps(fn)
            def wrapper(*args, **kwargs):
                return self.run_mutation(name, *args, **kwargs)

            return wrapper

        return decorator

    def run_query(self, endpoint_name: str, *args, **kwargs) -> TResponse:
        if self.base_query_fn is None:
            raise ValueError("base_query function is not set.")

        endpoint = self.endpoints.get(endpoint_name)
        if endpoint is None or not endpoint.is_query:
            raise ValueError(f"No query endpoint named '{endpoint_name}' found.")

        request_def = endpoint.request_fn(*args, **kwargs)

        if self.cache_strategy:
            cached_response = self.cache_strategy.get(endpoint_name, request_def)
            if cached_response is not None:
                return cached_response

        assert self.base_query_fn_handler
        response = self.base_query_fn_handler(self.base_query_config, request_def)

        if self.cache_strategy:
            self.cache_strategy.set(
                endpoint_name, request_def, response, endpoint.provides_tags
            )
        return response

    def run_mutation(self, endpoint_name: str, *args, **kwargs) -> TResponse:
        if self.base_query_fn is None:
            raise ValueError("base_query function is not set.")

        endpoint = self.endpoints.get(endpoint_name)
        if endpoint is None or not endpoint.is_mutation:
            raise ValueError(f"No mutation endpoint named '{endpoint_name}' found.")

        request_def = endpoint.request_fn(*args, **kwargs)
        assert self.base_query_fn_handler
        response = self.base_query_fn_handler(self.base_query_config, request_def)

        if endpoint.invalidates_tags and self.cache_strategy:
            self.cache_strategy.invalidate_tags(endpoint.invalidates_tags)
        return response

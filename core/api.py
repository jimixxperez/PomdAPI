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
    Coroutine,
)

from pydantic import BaseModel, Field

from .types import (
    TResponse,
    BaseQueryConfig,
    EndpointDefinition,
    CachingStrategy,
)


QueryParam = ParamSpec("QueryParam")
ResponseType = TypeVar("ResponseType", bound=BaseModel)
QueryResponse = TypeVar("QueryResponse")


import asyncio
from typing import overload, Awaitable


class SyncAsync(Protocol[QueryParam, QueryResponse]):
    @overload
    def __call__(
        self,
        is_async: Literal[False],
        *args: QueryParam.args,
        **kwargs: QueryParam.kwargs,
    ) -> QueryResponse: ...

    @overload
    def __call__(
        self,
        is_async: Literal[True] = True,
        *args: QueryParam.args,
        **kwargs: QueryParam.kwargs,
    ) -> asyncio.Future[QueryResponse]: ...

    @overload
    def __call__(
        self,
        is_async: bool = True,
        *args: QueryParam.args,
        **kwargs: QueryParam.kwargs,
    ) -> asyncio.Future[QueryResponse] | QueryResponse: ...


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
        Callable[
            [BaseQueryConfig, EndpointDefinitionGen], Coroutine[None, None, TResponse]
        ]
    ] = None
    endpoints: dict[str, EndpointDefinition[EndpointDefinitionGen]] = Field(
        default_factory=dict
    )
    cache_strategy: Optional[CachingStrategy[EndpointDefinitionGen, TResponse]] = None

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
        response_type: Type[ResponseType],
        provides_tags: Optional[list[str]] = None,
    ) -> Callable[
        [Callable[QueryParam, EndpointDefinitionGen]],
        SyncAsync[QueryParam, ResponseType],
    ]:
        """Decorator to register a query endpoint.
        The decorated function will execute the query and return the response.
        """

        def decorator(
            fn: Callable[QueryParam, EndpointDefinitionGen],
        ) -> SyncAsync[QueryParam, ResponseType]:
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
                ) -> ResponseType:
                    return response_type.model_validate(
                        self.run_query(
                            is_async=False, endpoint_name=name, *args, **kwargs
                        )
                    )

                @overload
                def wrapper(
                    is_async: Literal[True] = True,
                    *args: QueryParam.args,
                    **kwargs: QueryParam.kwargs,
                ) -> asyncio.Future[ResponseType]: ...

                @overload
                def wrapper(
                    is_async: bool = True,
                    *args: QueryParam.args,
                    **kwargs: QueryParam.kwargs,
                ) -> asyncio.Future[ResponseType] | ResponseType: ...

            @wraps(fn)
            def wrapper(
                is_async: bool = True,
                *args: QueryParam.args,
                **kwargs: QueryParam.kwargs,
            ) -> asyncio.Future[ResponseType] | ResponseType:
                if is_async:
                    return response_type.model_validate(
                        self.run_query(
                            is_async=False, endpoint_name=name, *args, **kwargs
                        )
                    )

                async def _run() -> ResponseType:
                    response = await self.run_query(
                        is_async=True, endpoint_name=name, *args, **kwargs
                    )
                    return response_type.model_validate(response)

                return asyncio.ensure_future(_run())

            return wrapper

        return decorator

    def mutation(
        self,
        name: str,
        invalidates_tags: Optional[list[str]] = None,
        response_type: Type[ResponseType] | None = None,
    ) -> Callable[
        [Callable[QueryParam, EndpointDefinitionGen]],
        SyncAsync[QueryParam, (ResponseType | None)],
    ]:
        """Decorator to register a mutation endpoint.
        The decorated function will execute the mutation and return the response.
        """

        def decorator(
            fn: Callable[QueryParam, EndpointDefinitionGen],
        ) -> SyncAsync[QueryParam, (ResponseType | None)]:
            endpoint = EndpointDefinition(
                request_fn=fn,
                invalidates_tags=invalidates_tags or [],
                is_query_endpoint=False,
            )
            self.endpoints[name] = endpoint

            if TYPE_CHECKING:

                @overload
                def wrapper(
                    is_async: Literal[False],
                    *args: QueryParam.args,
                    **kwargs: QueryParam.kwargs,
                ) -> ResponseType | None: ...

                @overload
                def wrapper(
                    is_async: Literal[True] = True,
                    *args: QueryParam.args,
                    **kwargs: QueryParam.kwargs,
                ) -> asyncio.Future[ResponseType | None]: ...

                @overload
                def wrapper(
                    is_async: bool = True,
                    *args: QueryParam.args,
                    **kwargs: QueryParam.kwargs,
                ) -> asyncio.Future[ResponseType | None] | (ResponseType | None): ...

            @wraps(fn)
            def wrapper(is_async: bool, *args, **kwargs) -> asyncio.Future[
                ResponseType | None
            ] | (ResponseType | None):
                if is_async:

                    async def _run() -> ResponseType | None:
                        response = await self.run_mutation(
                            is_async=True, endpoint_name=name, *args, **kwargs
                        )
                        if response_type is None:
                            return None
                        return response_type.model_validate(response)

                response = self.run_mutation(
                    is_async=False, endpoint_name=name, *args, **kwargs
                )
                if response_type is None:
                    return None
                return response_type.model_validate(response)

            return wrapper

        return decorator

    @overload
    def run_query(
        self, is_async: Literal[False], endpoint_name: str, *args, **kwargs
    ) -> TResponse: ...

    @overload
    def run_query(
        self, is_async: Literal[True], endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse]: ...

    @overload
    def run_query(
        self, is_async: bool, endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse] | TResponse: ...

    def run_query(
        self, is_async: bool, endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse] | TResponse:
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
        if is_async:

            async def _run() -> TResponse:
                assert self.base_query_fn_handler_async is not None
                response = await self.base_query_fn_handler_async(
                    self.base_query_config, request_def
                )

                if self.cache_strategy:
                    self.cache_strategy.set(
                        endpoint_name, request_def, response, endpoint.provides_tags
                    )
                return response

            return asyncio.ensure_future(_run())

        response = self.base_query_fn_handler(self.base_query_config, request_def)
        if self.cache_strategy:
            self.cache_strategy.set(
                endpoint_name, request_def, response, endpoint.provides_tags
            )
        return response

    @overload
    def run_mutation(
        self, is_async: Literal[False], endpoint_name: str, *args, **kwargs
    ) -> TResponse: ...

    @overload
    def run_mutation(
        self, is_async: Literal[True], endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse]: ...

    @overload
    def run_mutation(
        self, is_async: bool, endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse] | TResponse: ...

    def run_mutation(
        self, is_async: bool, endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse] | TResponse:
        if self.base_query_fn is None:
            raise ValueError("base_query function is not set.")

        endpoint = self.endpoints.get(endpoint_name)
        if endpoint is None or not endpoint.is_mutation:
            raise ValueError(f"No mutation endpoint named '{endpoint_name}' found.")

        request_def = endpoint.request_fn(*args, **kwargs)
        assert self.base_query_fn_handler
        if is_async:

            async def _run() -> TResponse:
                assert self.base_query_fn_handler_async is not None
                response = await self.base_query_fn_handler_async(
                    self.base_query_config, request_def
                )
                if endpoint.invalidates_tags and self.cache_strategy:
                    self.cache_strategy.invalidate_tags(endpoint.invalidates_tags)
                return response

            return asyncio.ensure_future(_run())

        response = self.base_query_fn_handler(self.base_query_config, request_def)

        if endpoint.invalidates_tags and self.cache_strategy:
            self.cache_strategy.invalidate_tags(endpoint.invalidates_tags)
        return response

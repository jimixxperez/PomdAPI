import inspect
from dataclasses import dataclass, field
from functools import wraps
from typing import (
    TYPE_CHECKING,
    Callable,
    Generic,
    Iterable,
    Literal,
    Optional,
    ParamSpec,
    Protocol,
    Type,
    TypeAlias,
    TypeVar,
    Coroutine,
    cast,
)
    
from typing_extensions import TypeIs

from pydantic import BaseModel, TypeAdapter

from pomdapi.core.caching import Cache
from pomdapi.core.types import (
    EndpointDefinition,
    ProvidesTags,
)


QueryParam = ParamSpec("QueryParam")
ResponseType = TypeVar("ResponseType")
QueryResponse = TypeVar("QueryResponse")
BaseQueryConfig = TypeVar("BaseQueryConfig", contravariant=True)


import asyncio
from typing import overload


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
        is_async: Literal[True] = True,
        *args: QueryParam.args,
        **kwargs: QueryParam.kwargs,
    ) -> asyncio.Future[QueryResponse]:
        ...

    @overload
    def __call__(
        self,
        is_async: bool = True,
        *args: QueryParam.args,
        **kwargs: QueryParam.kwargs,
    ) -> asyncio.Future[QueryResponse] | QueryResponse:
        ...


EndpointDefinitionGen = TypeVar("EndpointDefinitionGen", contravariant=True)
TResponse = TypeVar("TResponse", covariant=True)
EndpointName: TypeAlias = str

BaseQueryFnArity2 = Callable[[BaseQueryConfig, EndpointDefinitionGen], TResponse]
BaseQueryFnArity3 = Callable[[BaseQueryConfig, EndpointDefinitionGen, EndpointName], TResponse]
BaseQueryFn = BaseQueryFnArity2[BaseQueryConfig, EndpointDefinitionGen, TResponse] | BaseQueryFnArity3[BaseQueryConfig, EndpointDefinitionGen, TResponse]

BaseQueryFnAsyncArity2 = Callable[
    [BaseQueryConfig, EndpointDefinitionGen], Coroutine[None, None, TResponse]
]
BaseQueryFnAsyncArity3 = Callable[
    [BaseQueryConfig, EndpointDefinitionGen, EndpointName],
    Coroutine[None, None, TResponse],
]

BaseQueryFnAsync: TypeAlias = BaseQueryFnAsyncArity2[BaseQueryConfig, EndpointDefinitionGen, TResponse] | BaseQueryFnAsyncArity3[BaseQueryConfig, EndpointDefinitionGen, TResponse]


def is_base_query_fn_arity_2(
    fn: BaseQueryFn[BaseQueryConfig, EndpointDefinitionGen, TResponse]
) -> TypeIs[Callable[[BaseQueryConfig, EndpointDefinitionGen], TResponse]]:
    return isinstance(fn, Callable) and len(inspect.signature(fn).parameters) == 2


def is_base_query_fn_async_arity_2(
    fn: BaseQueryFnAsync[BaseQueryConfig, EndpointDefinitionGen, TResponse]
) -> TypeIs[
    BaseQueryFnAsyncArity2[BaseQueryConfig, EndpointDefinitionGen, TResponse]
]:
    return isinstance(fn, Callable) and len(inspect.signature(fn).parameters) == 3


@dataclass
class Api(Generic[EndpointDefinitionGen, BaseQueryConfig, TResponse]):
    """
    The Api class is the main entry point for interacting with the API.
    It provides a simple interface for defining query and mutation endpoints.

    This class is generic over two type parameters:
    - EndpointDefinitionGen: The type of request definition (e.g., HTTP request, RPC request)
    - TResponse: The type of response returned by the API

    Attributes:
        base_query_config: Configuration for all API requests
        base_query_fn_handler: Synchronous function to execute requests
        base_query_fn_handler_async: Asynchronous function to execute requests
        endpoints: Dictionary mapping endpoint names to their definitions
        cache: Optional cache implementation for responses

    Example:
        ```python
        api = Api(
            base_query_config=BaseQueryConfig(base_url="https://api.example.com"),
            cache=InMemoryCache()
        )

        @api.query("getUser", response_type=User)
        def get_user(id: str):
            return {"path": f"/users/{id}"}
        ```
    """

    base_query_config: BaseQueryConfig
    base_query_fn_handler: BaseQueryFn[
        BaseQueryConfig, EndpointDefinitionGen, TResponse
    ] | None = None
    base_query_fn_handler_async: Optional[
        BaseQueryFnAsync[BaseQueryConfig, EndpointDefinitionGen, TResponse]
    ] = None
    endpoints: dict[str, EndpointDefinition[EndpointDefinitionGen]] = field(
        default_factory=dict
    )
    cache: Optional[Cache[EndpointDefinitionGen, TResponse]] = None

    def base_query_fn(
        self, fn: BaseQueryFn[BaseQueryConfig, EndpointDefinitionGen, TResponse]
    ) -> BaseQueryFn[BaseQueryConfig, EndpointDefinitionGen, TResponse]:
        """Decorator to register a base query function."""
        if not self.base_query_fn_handler:
            self.base_query_fn_handler = fn
        return fn

    def query(
        self,
        name: str,
        response_type: Type[ResponseType],
    ) -> Callable[
        [
            Callable[QueryParam, EndpointDefinitionGen]
            | Callable[QueryParam, ProvidesTags[EndpointDefinitionGen, QueryParam]]
        ],
        SyncAsync[QueryParam, ResponseType],
    ]:
        """Decorator to register a query endpoint.
        The decorated function will execute the query and return the response.
        """

        def decorator(
            fn: Callable[QueryParam, EndpointDefinitionGen]
            | Callable[QueryParam, ProvidesTags[EndpointDefinitionGen, QueryParam]],
        ) -> SyncAsync[QueryParam, ResponseType]:
            endpoint = EndpointDefinition(
                request_fn=fn,
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
                    ...

                @overload
                def wrapper(
                    is_async: Literal[True] = True,
                    *args: QueryParam.args,
                    **kwargs: QueryParam.kwargs,
                ) -> asyncio.Future[ResponseType]:
                    ...

                @overload
                def wrapper(
                    is_async: bool = True,
                    *args: QueryParam.args,
                    **kwargs: QueryParam.kwargs,
                ) -> asyncio.Future[ResponseType] | ResponseType:
                    ...

            @wraps(fn)
            def wrapper(
                is_async: bool = True,
                *args: QueryParam.args,
                **kwargs: QueryParam.kwargs,
            ) -> asyncio.Future[ResponseType] | ResponseType:
                if is_async:

                    async def _run() -> ResponseType:
                        response = await self.run_query(
                            is_async=True, endpoint_name=name, *args, **kwargs
                        )
                        if isinstance(response_type, BaseModel):
                            return response_type.model_validate(response)
                        adapter = TypeAdapter(response_type)
                        return adapter.validate_python(response)

                    return asyncio.ensure_future(_run())

                response = self.run_query(
                    is_async=False, endpoint_name=name, *args, **kwargs
                )

                if isinstance(response_type, BaseModel):
                    return response_type.model_validate(response)
                adapter = TypeAdapter(response_type)
                return adapter.validate_python(response)

            return wrapper

        return decorator

    @overload
    def mutation(
        self,
        name: str,
        response_type: Type[ResponseType],
    ) -> Callable[
        [
            Callable[QueryParam, EndpointDefinitionGen]
            | Callable[QueryParam, ProvidesTags[EndpointDefinitionGen, QueryParam]]
        ],
        SyncAsync[QueryParam, ResponseType],
    ]:
        ...

    @overload
    def mutation(
        self,
        name: str,
        response_type: Literal[None] = None,
    ) -> Callable[
        [
            Callable[QueryParam, EndpointDefinitionGen]
            | Callable[QueryParam, ProvidesTags[EndpointDefinitionGen, QueryParam]]
        ],
        SyncAsync[QueryParam, None],
    ]:
        ...

    @overload
    def mutation(
        self,
        name: str,
        response_type: Type[ResponseType] | None = None,
    ) -> Callable[
        [
            Callable[QueryParam, EndpointDefinitionGen]
            | Callable[QueryParam, ProvidesTags[EndpointDefinitionGen, QueryParam]]
        ],
        SyncAsync[QueryParam, ResponseType] | SyncAsync[QueryParam, None],
    ]:
        ...

    def mutation(
        self,
        name: str,
        response_type: Type[ResponseType] | None = None,
    ) -> Callable[
        [
            Callable[QueryParam, EndpointDefinitionGen]
            | Callable[QueryParam, ProvidesTags[EndpointDefinitionGen, QueryParam]]
        ],
        SyncAsync[QueryParam, ResponseType] | SyncAsync[QueryParam, None],
    ]:
        """Decorator to register a mutation endpoint.
        The decorated function will execute the mutation and return the response.
        """

        def decorator(
            fn: Callable[QueryParam, EndpointDefinitionGen]
            | Callable[QueryParam, ProvidesTags[EndpointDefinitionGen, QueryParam]],
        ) -> SyncAsync[QueryParam, ResponseType] | SyncAsync[QueryParam, None]:
            endpoint = EndpointDefinition(
                request_fn=fn,
                is_query_endpoint=False,
            )
            self.endpoints[name] = endpoint

            if response_type is None:
                if TYPE_CHECKING:

                    @overload
                    def none_wrapper(
                        is_async: Literal[False],
                        *args: QueryParam.args,
                        **kwargs: QueryParam.kwargs,
                    ) -> None:
                        ...

                    @overload
                    def none_wrapper(
                        is_async: Literal[True] = True,
                        *args: QueryParam.args,
                        **kwargs: QueryParam.kwargs,
                    ) -> asyncio.Future[None]:
                        ...

                    @overload
                    def none_wrapper(
                        is_async: bool = True,
                        *args: QueryParam.args,
                        **kwargs: QueryParam.kwargs,
                    ) -> asyncio.Future[None] | None:
                        ...

                @wraps(fn)
                def none_wrapper(
                    is_async: bool, *args, **kwargs
                ) -> asyncio.Future[None] | (None):
                    if is_async:

                        async def _run() -> None:
                            await self.run_mutation(
                                is_async=True, endpoint_name=name, *args, **kwargs
                            )
                            return None

                        return asyncio.ensure_future(_run())

                    self.run_mutation(
                        is_async=False, endpoint_name=name, *args, **kwargs
                    )
                    return None

                return none_wrapper

            else:
                if TYPE_CHECKING:

                    @overload
                    def wrapper(
                        is_async: Literal[False],
                        *args: QueryParam.args,
                        **kwargs: QueryParam.kwargs,
                    ) -> ResponseType:
                        ...

                    @overload
                    def wrapper(
                        is_async: Literal[True] = True,
                        *args: QueryParam.args,
                        **kwargs: QueryParam.kwargs,
                    ) -> asyncio.Future[ResponseType]:
                        ...

                    @overload
                    def wrapper(
                        is_async: bool = True,
                        *args: QueryParam.args,
                        **kwargs: QueryParam.kwargs,
                    ) -> asyncio.Future[ResponseType] | (ResponseType):
                        ...

                @wraps(fn)
                def wrapper(
                    is_async: bool, *args, **kwargs
                ) -> asyncio.Future[ResponseType] | (ResponseType):
                    if is_async:

                        async def _run() -> ResponseType:
                            response = await self.run_mutation(
                                is_async=True, endpoint_name=name, *args, **kwargs
                            )

                            if isinstance(response_type, BaseModel):
                                return response_type.model_validate(response)

                            adapter = TypeAdapter(response_type)
                            return adapter.validate_python(response)

                        return asyncio.ensure_future(_run())

                    response = self.run_mutation(
                        is_async=False, endpoint_name=name, *args, **kwargs
                    )

                    if isinstance(response_type, BaseModel):
                        return response_type.model_validate(response)

                    adapter = TypeAdapter(response_type)
                    return adapter.validate_python(response)

                return wrapper

        return decorator

    @overload
    def run_query(
        self, is_async: Literal[False], endpoint_name: str, *args, **kwargs
    ) -> TResponse:
        ...

    @overload
    def run_query(
        self, is_async: Literal[True], endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse]:
        ...

    @overload
    def run_query(
        self, is_async: bool, endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse] | TResponse:
        ...

    def run_query(
        self, is_async: bool, endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse] | TResponse:
        if self.base_query_fn is None:
            raise ValueError("base_query function is not set.")

        endpoint = self.endpoints.get(endpoint_name)
        if endpoint is None or not endpoint.is_query:
            raise ValueError(f"No query endpoint named '{endpoint_name}' found.")

        request_def_and_tags = endpoint.request_fn(*args, **kwargs)
        tags = None
        if isinstance(request_def_and_tags, tuple):
            request_def, tags = request_def_and_tags
            if callable(tags):
                tags = tags(*args, **kwargs)
            if not isinstance(tags, Iterable):
                tags = [tags]
        else:
            request_def = cast(EndpointDefinitionGen, request_def_and_tags)

        if self.cache:
            cached_response = self.cache.get_by_request(endpoint_name, request_def)
            if cached_response is not None:
                return cached_response

        assert self.base_query_fn_handler
        if is_async:

            async def _run() -> TResponse:
                assert self.base_query_fn_handler_async is not None
                if is_base_query_fn_async_arity_2(self.base_query_fn_handler_async):
                    response = await self.base_query_fn_handler_async(
                        self.base_query_config, request_def
                    )
                else:
                    response = await self.base_query_fn_handler_async(
                        self.base_query_config, request_def, endpoint_name # type: ignore
                    ) 

                if self.cache:
                    await self.cache.aset(
                        endpoint_name=endpoint_name,
                        request=request_def,
                        response=response,
                        tags=tags and tags or [],
                    )
                return response

            return asyncio.ensure_future(_run())

        # GET Number of parameters
        # fn_sig = inspect.signature(self.base_query_fn_handler)
        if is_base_query_fn_arity_2(self.base_query_fn_handler):
            response = self.base_query_fn_handler(self.base_query_config, request_def)
        else:
            response = self.base_query_fn_handler(
                self.base_query_config, request_def, endpoint_name # type: ignore
            )
        # if len(fn_sig.parameters) == 3:
        #    fn = cast(Callable[[BaseQueryConfig, EndpointDefinitionGen, str], TResponse], self.base_query_fn_handler)
        #    response = fn(self.base_query_config, request_def, endpoint_name)
        # else:
        #    fn = cast(Callable[[BaseQueryConfig, EndpointDefinitionGen], TResponse], self.base_query_fn_handler)
        #    response = fn(self.base_query_config, request_def)

        if self.cache:
            self.cache.set(
                endpoint_name=endpoint_name,
                request=request_def,
                response=response,
                tags=tags and tags or [],
            )
        return response

    @overload
    def run_mutation(
        self, is_async: Literal[False], endpoint_name: str, *args, **kwargs
    ) -> TResponse:
        ...

    @overload
    def run_mutation(
        self, is_async: Literal[True], endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse]:
        ...

    @overload
    def run_mutation(
        self, is_async: bool, endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse] | TResponse:
        ...

    def run_mutation(
        self, is_async: bool, endpoint_name: str, *args, **kwargs
    ) -> asyncio.Future[TResponse] | TResponse:
        if self.base_query_fn is None:
            raise ValueError("base_query function is not set.")

        endpoint = self.endpoints.get(endpoint_name)
        if endpoint is None or not endpoint.is_mutation:
            raise ValueError(f"No mutation endpoint named '{endpoint_name}' found.")

        request_def_and_tags = endpoint.request_fn(*args, **kwargs)
        tags = None
        if isinstance(request_def_and_tags, tuple):
            request_def, tags = request_def_and_tags
            if callable(tags):
                tags = tags(*args, **kwargs)
            if not isinstance(tags, Iterable):
                tags = [tags]
        else:
            request_def = cast(EndpointDefinitionGen, request_def_and_tags)
        assert self.base_query_fn_handler
        if is_async:

            async def _run() -> TResponse:
                assert self.base_query_fn_handler_async is not None
                if is_base_query_fn_async_arity_2(self.base_query_fn_handler_async):
                    response = await self.base_query_fn_handler_async(
                        self.base_query_config,
                        request_def,
                    )
                else:
                    response = await self.base_query_fn_handler_async(
                        self.base_query_config,
                        request_def,
                        endpoint_name, # type: ignore
                    )
                if self.cache and tags:
                    await self.cache.ainvalidate_tags(
                        endpoint_name=endpoint_name,
                        tags=tags,
                    )
                return response

            return asyncio.ensure_future(_run())

        if is_base_query_fn_arity_2(self.base_query_fn_handler):
            response = self.base_query_fn_handler(self.base_query_config, request_def)
        else:
            response = self.base_query_fn_handler(
                self.base_query_config, request_def, endpoint_name # type: ignore
            )

        if self.cache and tags:
            self.cache.invalidate_tags(
                endpoint_name=endpoint_name,
                tags=tags,
            )
        return response

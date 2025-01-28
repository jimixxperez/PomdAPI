import httpx
import urllib.parse

from dataclasses import dataclass, field
from typing import Callable, Optional, Any, Literal
from pomdapi.core.api import Api
from pomdapi.core.caching import Cache


@dataclass
class RequestDefinition:
    """Defines a request for the API.
    
    Attributes:
        method: The HTTP method for the request.
        path: The path for the request.
        body: The request body.
        headers: The request headers.
    example:
        ```python
        RequestDefinition(
            method="GET",
            path="/users",
            headers={"Authorization": "Bearer <token>"}
        )
        ```
    """

    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = field()
    path: str
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)

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
    base_url: str 
    prepare_headers: Callable[[dict[str, str]], dict[str, str]] = field(
        default_factory=lambda: lambda header: header
    )



def base_query_fn(config: BaseQueryConfig, req: RequestDefinition) -> Any:
    # Prepare the final URL. If it's relative, prepend base_url.
    url = urllib.parse.urljoin(base=config.base_url, url=req.path)

    prepared_headers = (
        config.prepare_headers(req.headers) if config.prepare_headers else req.headers
    )

    response = httpx.request(
        method=req.method,
        url=url,
        json=req.body,
        headers=prepared_headers,
    )
    response.raise_for_status()
    return response.json()


async def abase_query_fn(config: BaseQueryConfig, req: RequestDefinition) -> Any:
    url = urllib.parse.urljoin(base=config.base_url, url=req.path)

    prepared_headers = (
        config.prepare_headers(req.headers) if config.prepare_headers else req.headers
    )

    async with httpx.AsyncClient() as client:
        request = client.build_request(
            method=req.method,
            url=url,
            json=req.body,
            headers=prepared_headers,
        )
        response = await client.send(request)

    response.raise_for_status()
    return response.json()


class HttpApi(Api[RequestDefinition, BaseQueryConfig, Any]):
    @classmethod
    def from_defaults(
        cls,
        base_query_config: BaseQueryConfig,
        cache: Optional[Cache[RequestDefinition, Any]] = None,
    ):
        return cls(
            base_query_config=base_query_config,
            base_query_fn_handler=base_query_fn,
            base_query_fn_handler_async=abase_query_fn,
            cache=cache,
        )

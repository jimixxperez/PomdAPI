import httpx

from dataclasses import dataclass, field
from typing import TypedDict, Required, Optional, Any, Literal
from core.api import Api
from core.caching import Cache
from core.types import BaseQueryConfig


@dataclass
class RequestDefinition:
    """Defines a request for the API."""

    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    url: str
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)


def base_query_fn(config: BaseQueryConfig, req: RequestDefinition) -> Any:
    # Prepare the final URL. If it's relative, prepend base_url.
    if config.base_url and not req.url.startswith("http"):
        req_url = f"{config.base_url}{req.url}"
    else:
        req_url = req.url

    prepared_headers = (
        config.prepare_headers(req.headers) if config.prepare_headers else req.headers
    )

    response = httpx.request(
        method=req.method,
        url=req_url,
        json=req.body,
        headers=prepared_headers,
    )
    response.raise_for_status()
    return response.json()


async def abase_query_fn(config: BaseQueryConfig, req: RequestDefinition) -> Any:
    # Prepare the final URL. If it's relative, prepend base_url.
    if config.base_url and not req.url.startswith("http"):
        req_url = f"{config.base_url}{req.url}"
    else:
        req_url = req.url

    prepared_headers = (
        config.prepare_headers(req.headers) if config.prepare_headers else req.headers
    )

    async with httpx.AsyncClient() as client:
        request = client.build_request(
            method=req.method,
            url=req_url,
            json=req.body,
            headers=prepared_headers,
        )
        response = await client.send(request)

    response.raise_for_status()
    return response.json()


class HttpApi(Api[RequestDefinition, Any]):
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

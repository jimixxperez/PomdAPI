import httpx

from typing import TypedDict, Required, Optional, Any
from core.api import Api
from core.types import BaseQueryConfig, CachingStrategy

class RequestDefinition(TypedDict, total=False):
    """Defines a request for the API."""
    method: Required[str]
    url: Required[str]
    body: Optional[Any]
    headers: Optional[dict[str, str]]

def base_query_fn(config: BaseQueryConfig, req: RequestDefinition) -> Any:
    # Prepare the final URL. If it's relative, prepend base_url.
    if config.base_url and not req["url"].startswith("http"):
        req_url = f"{config.base_url}{req["url"]}"
    else:
        req_url = req["url"]

    headers = req.get("headers", {})
    assert headers is not None
    prepared_headers = config.prepare_headers(headers) if config.prepare_headers else headers

    response = httpx.request(
        method=req["method"],
        url=req_url,
        json=req.get("body"),
        headers=prepared_headers
    )
    response.raise_for_status()
    return response.json()

async def abase_query_fn(config: BaseQueryConfig, req: RequestDefinition) -> Any:
    # Prepare the final URL. If it's relative, prepend base_url.
    if config.base_url and not req["url"].startswith("http"):
        req_url = f"{config.base_url}{req["url"]}"
    else:
        req_url = req["url"]

    headers = req.get("headers", {})
    assert headers is not None
    prepared_headers = config.prepare_headers(headers) if config.prepare_headers else headers

    async with httpx.AsyncClient() as client:
        request = client.build_request(
            method=req["method"],
            url=req_url,
            json=req.get("body"),
            headers=prepared_headers
        )
        response = await client.send(request)

    response.raise_for_status()
    return response.json()

class HttpApi(Api[RequestDefinition, Any]):
    
    @classmethod
    def from_defaults(cls, base_query_config: BaseQueryConfig, caching_strategy: Optional[CachingStrategy[RequestDefinition, Any]] = None,):
        return cls(
            base_query_config=base_query_config,
            base_query_fn_handler=base_query_fn,
            base_query_fn_handler_async=abase_query_fn,
        )






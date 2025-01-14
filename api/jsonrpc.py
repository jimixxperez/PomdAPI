import httpx
from typing import TypeAlias, TypedDict, Required, Any, Optional

from pydantic import BaseModel, HttpUrl, TypeAdapter

from core.api import Api
from core.caching import Cache


RequestDefinition: TypeAlias = dict[str, Any] | list[Any]


class BaseQueryConfig(BaseModel):
    """Defines the base configuration for all API requests."""

    base_url: HttpUrl


JSONRPCId: TypeAlias = Optional[str | int]


class JSONRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Any
    id: JSONRPCId


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    id: JSONRPCId


def base_query_fn(
    config: BaseQueryConfig, req: RequestDefinition, endpoint_name: str
) -> Any:
    req_url = config.base_url
    assert req_url is not None
    json_payload = JSONRPCRequest(
        jsonrpc="2.0",
        id=1,
        method=endpoint_name,
        params=req,
    ).model_dump()
    # import pdb; pdb.set_trace()
    response = httpx.request(
        method="POST",
        url=str(req_url),
        json=json_payload,
    )
    response.raise_for_status()
    jsonrpc_response = JSONRPCResponse(**response.json())
    return jsonrpc_response.result


async def abase_query_fn(
    config: BaseQueryConfig, req: RequestDefinition, endpoint_name: str
):
    req_url = config.base_url
    assert req_url is not None
    async with httpx.AsyncClient() as client:
        request = client.build_request(
            method="POST",
            url=str(req_url),
            json=JSONRPCRequest(
                jsonrpc="2.0",
                id=1,
                method=endpoint_name,
                params=req,
            ).model_dump(),
        )
        response = await client.send(request)

    response.raise_for_status()
    jsonrpc_response = JSONRPCResponse(**response.json())
    return jsonrpc_response.result


class JSONRPCApi(Api[RequestDefinition, BaseQueryConfig, Any]):
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

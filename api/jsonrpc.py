import httpx
from typing import TypeAlias, TypedDict, Required, Any, Optional

from pydantic import BaseModel

from core.api import Api
from core.types import BaseQueryConfig, CachingStrategy


class RequestDefinition(TypedDict, total=False):
    """Defines a request for the JSON-RPC API"""

    id: Optional[int]
    method: Required[str]
    params: Required[dict[str, Any] | list[Any]]


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


def base_query_fn(config: BaseQueryConfig, req: RequestDefinition):
    req_url = config.base_url
    assert req_url is not None
    json_payload = JSONRPCRequest(
                jsonrpc="2.0",
                id=1,
                method=req["method"],
                params=req["params"],
            ).model_dump()
    #import pdb; pdb.set_trace()
    response = httpx.request(
        method="POST",
        url=req_url,
        json=json_payload,
    )
    response.raise_for_status()
    jsonrpc_response = JSONRPCResponse(**response.json())
    return jsonrpc_response.result


async def abase_query_fn(config: BaseQueryConfig, req: RequestDefinition):
    req_url = config.base_url
    assert req_url is not None
    async with httpx.AsyncClient() as client:
        request = client.build_request(
            method="POST",
            url=req_url,
            json=JSONRPCRequest(
                jsonrpc="2.0",
                id=1,
                method=req["method"],
                params=req["params"],
            ).model_dump(),
        )
        response = await client.send(request)

    response.raise_for_status()
    jsonrpc_response = JSONRPCResponse(**response.json())
    return jsonrpc_response.result


class JSONRPCApi(Api[RequestDefinition, Any]):
    @classmethod
    def from_defaults(
        cls,
        base_query_config: BaseQueryConfig,
        caching_strategy: Optional[
            CachingStrategy[RequestDefinition, Any]
        ] = None,
    ):
        return cls(
            base_query_config=base_query_config,
            base_query_fn_handler=base_query_fn,
            base_query_fn_handler_async=abase_query_fn,
        )

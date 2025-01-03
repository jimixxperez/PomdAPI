from httpx import Request
from api.jsonrpc import RequestDefinition, JSONRPCApi
from core.types import BaseQueryConfig

from pydantic import BaseModel, TypeAdapter

ethereum_api = JSONRPCApi.from_defaults(
    base_query_config=BaseQueryConfig(
        base_url="https://oauth.reddit.com",
    ),
)

Balance = TypeAdapter(int)


@ethereum_api.query(name="eth_getBalance", response_type=Balance)
def get_balance(data: bytes, quantity_tag: str) -> RequestDefinition:
    return {"method": "eth_getBalance", "params": [data, quantity_tag]}

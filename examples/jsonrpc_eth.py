from typing import Optional

from core.types import BaseQueryConfig
from api.jsonrpc import RequestDefinition, JSONRPCApi

ethereum_api = JSONRPCApi.from_defaults(
    base_query_config=BaseQueryConfig(
        base_url="https://docs-demo.quiknode.pro",
    ),
)

@ethereum_api.query(name="getBalance", response_type=bytes)
def get_balance(eth_address: str, quantity_tag: str = "latest") -> RequestDefinition:
    """Gets the balance of an address"""
    return {"method": "eth_getBalance", "params": [eth_address, quantity_tag]}


@ethereum_api.query(name="call", response_type=str)
def call(_from: bytes, _to: bytes, gas: Optional[int] = None, gas_prices: Optional[int] = None, ) -> RequestDefinition:
    """Calls a contract"""
    return {
        "method": "eth_call", 
        "params": {
            "from": _from,
            "to": _to,
            "gas": gas,
            "gas_prices": gas_prices,
        }
    }

@ethereum_api.query(name="getGasPrice", response_type=str)
def get_gas_price() -> RequestDefinition:
    """Gets the current gas price"""
    return {"method": "eth_gasPrice", "params": []}

if __name__ == "__main__":
    balance = get_balance(
        is_async=False,
        eth_address="0x8D97689C9818892B700e27F316cc3E41e17fBeb9",
        quantity_tag="latest",
    )

    gas_price = int(get_gas_price(is_async=False), 16)

    import pdb; pdb.set_trace()

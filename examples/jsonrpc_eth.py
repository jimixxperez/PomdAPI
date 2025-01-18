from typing import Optional

from pomdapi.api.jsonrpc import JSONRPCApi, BaseQueryConfig

ethereum_api = JSONRPCApi.from_defaults(
    base_query_config=BaseQueryConfig(
        base_url="https://docs-demo.quiknode.pro",
    ),
)
print("""
    In this setup, the endpoint_name corresponds to jsonrpc method
    and decorated function should return the parameters
""")

# NOTE: Endpoint name  corresponds to jsonrpc method
@ethereum_api.query(name="eth_getBalance", response_type=bytes)
def get_balance(eth_address: str, quantity_tag: str = "latest"):
    """Gets the balance of an address"""
    return [eth_address, quantity_tag]


@ethereum_api.query(name="eth_Call", response_type=str)
def call(
    _from: bytes,
    _to: bytes,
    gas: Optional[int] = None,
    gas_prices: Optional[int] = None,
):
    """Calls a contract"""
    return {
        "from": _from,
        "to": _to,
        "gas": gas,
        "gas_prices": gas_prices,
    }


@ethereum_api.query(name="eth_gasPrice", response_type=str)
def get_gas_price():
    """Gets the current gas price"""
    return []


if __name__ == "__main__":
    balance = get_balance(
        is_async=False,
        eth_address="0x8D97689C9818892B700e27F316cc3E41e17fBeb9",
        quantity_tag="latest",
    )
    print("balance:", balance)

    gas_price = int(get_gas_price(is_async=False), 16)
    print("current gas_price:", gas_price)


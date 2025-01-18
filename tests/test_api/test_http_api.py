import pytest
from pomdapi.api.http import HttpApi, BaseQueryConfig, RequestDefinition
from pydantic import BaseModel

class TestResponse(BaseModel):
    message: str
    code: int

@pytest.mark.parametrize("config,expected_base_url", [
    (BaseQueryConfig(base_url="https://api.test.com"), "https://api.test.com"),
    (BaseQueryConfig(base_url="http://localhost:8000"), "http://localhost:8000"),
])
def test_http_api_initialization(config: BaseQueryConfig, expected_base_url: str):
    api = HttpApi.from_defaults(base_query_config=config)
    assert api.base_query_config.base_url == expected_base_url

@pytest.mark.parametrize("endpoint_name,response_type", [
    ("test_query", TestResponse),
    ("another_query", dict),
])
def test_http_api_query_decorator(endpoint_name: str, response_type: type):
    api = HttpApi.from_defaults(base_query_config=BaseQueryConfig(base_url="https://api.test.com"))
    
    @api.query(endpoint_name, response_type=response_type)
    def test_query(param: str) -> RequestDefinition:
        return RequestDefinition(
            method="GET",
            url=f"/test/{param}"
        )
    
    assert endpoint_name in api.endpoints
    assert api.endpoints[endpoint_name].is_query_endpoint

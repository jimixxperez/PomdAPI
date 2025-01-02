import requests
from xml.etree import ElementTree as ET
from typing import Callable, Generic, Required, Self, Type, TypeVar, Dict, List, Optional, Any, Tuple, TypedDict, cast
from dataclasses import dataclass, field
from time import time
from functools import wraps

#TResponse = TypeVar('TResponse')
#
#
#@dataclass
#class BaseQueryConfig:
#    base_url: Optional[str] = None
#    prepare_headers: Callable[[Dict[str, str]], Dict[str, str]] = field(default_factory=lambda: lambda header: header)
#
#
#
#class RequestDefinition(TypedDict, total=False):
#    method: Required[str]
#    url: Required[str]
#    body: Optional[Any]
#    headers: Optional[Dict[str, str]]
#
#@dataclass
#class EndpointDefinition:
##    request_fn: Callable[..., RequestDefinition]
#    provides_tags: List[str] = field(default_factory=list)
#    invalidates_tags: List[str] = field(default_factory=list)
#    is_query_endpoint: bool = True
#
#    @property
#    def is_query(self) -> bool:
#        return self.is_query_endpoint
#
#    @property
#    def is_mutation(self) -> bool:
#        return not self.is_query_endpoint
#
#
#@dataclass
#class CacheEntry(Generic[TResponse]):
#    response: TResponse
#    tags: List[str]
#    timestamp: float
#
#class CachingStrategy(Generic[TResponse]):
#    def get(self, endpoint_name: str, request: RequestDefinition) -> Optional[TResponse]:
#        raise NotImplementedError
#
#    def set(self, endpoint_name: str, request: RequestDefinition, response: TResponse, tags: List[str]) -> None:
#        raise NotImplementedError
#
#    def invalidate_tags(self, tags: List[str]) -> None:
#        raise NotImplementedError
#
#class InMemoryCacheStrategy(CachingStrategy[TResponse]):
#    def __init__(self, ttl: Optional[float] = 60.0):
#        self._cache: Dict[Tuple[str, str], CacheEntry[TResponse]] = {}
#        self.ttl = ttl
#
#    def _make_key(self, endpoint_name: str, request: RequestDefinition) -> Tuple[str, str]:
#        method = request.get("method", "")
#        url = request.get("url", "")
#        body = str(request.get("body", None))
#        headers = request.get("headers", {})
#        request_key = (
#            method,
#            url,
#            body,
#            str(sorted(headers.items()) if headers else [])
#        )
#        return (endpoint_name, str(request_key))
#
#    def get(self, endpoint_name: str, request: RequestDefinition) -> Optional[TResponse]:
#        key = self._make_key(endpoint_name, request)
#        entry = self._cache.get(key)
#        if entry is not None:
#            if self.ttl is not None and (time() - entry.timestamp) > self.ttl:
#                del self._cache[key]
#                return None
#            return entry.response
#        return None
#
#    def set(self, endpoint_name: str, request: RequestDefinition, response: TResponse, tags: List[str]) -> None:
#        key = self._make_key(endpoint_name, request)
#        self._cache[key] = CacheEntry(response=response, tags=tags, timestamp=time())
#
#    def invalidate_tags(self, tags: List[str]) -> None:
#        if not tags:
#            return
#        keys_to_remove = []
#        for key, entry in self._cache.items():
#            if any(tag in entry.tags for tag in tags):
#                keys_to_remove.append(key)
#        for k in keys_to_remove:
#            del self._cache[k]
#
#from pydantic import BaseModel 
#
#from typing import ParamSpec, cast
#QueryParam = ParamSpec("QueryParam")
#
#QueryResponse = TypeVar("QueryResponse", bound=BaseModel)
#
#@dataclass
#class Api(Generic[TResponse]):
#    base_query_config: BaseQueryConfig
#    base_query_fn_handler: Optional[Callable[[BaseQueryConfig,RequestDefinition], TResponse]] = None
#    endpoints: Dict[str, EndpointDefinition] = field(default_factory=dict)
#    cache_strategy: CachingStrategy[TResponse] = field(default_factory=lambda: InMemoryCacheStrategy())
#
#    def base_query_fn(self, fn: Callable[[BaseQueryConfig, RequestDefinition], TResponse]) -> Callable[[BaseQueryConfig, RequestDefinition], TResponse]:
#        """Decorator to register a base query function."""
#        if not self.base_query_fn_handler:
#            self.base_query_fn_handler = fn
#        return fn
#
#    def query(self, name: str, response_type: Type[QueryResponse], provides_tags: Optional[List[str]] = None, ) -> Callable[[Callable[QueryParam,RequestDefinition]], Callable[QueryParam, QueryResponse]]:
#        """Decorator to register a query endpoint.
#           The decorated function will execute the query and return the response.
#        """
#        def decorator(fn: Callable[QueryParam, RequestDefinition]) -> Callable[QueryParam, QueryResponse]:
#            endpoint = EndpointDefinition(
#                request_fn=fn,
#                provides_tags=provides_tags or [],
#                is_query_endpoint=True
#            )
#            self.endpoints[name] = endpoint
#
#            @wraps(fn)
#            def wrapper(*args: QueryParam.args, **kwargs: QueryParam.kwargs) -> QueryResponse:
#                return response_type.model_validate(self.run_query(name, *args, **kwargs))
#
#            return wrapper
#        return decorator
#
#    def mutation(self, name: str, invalidates_tags: Optional[List[str]] = None):
#        """Decorator to register a mutation endpoint.
#           The decorated function will execute the mutation and return the response.
#        """
#        def decorator(fn: Callable[..., RequestDefinition]):
#            endpoint = EndpointDefinition(
#                request_fn=fn,
#                invalidates_tags=invalidates_tags or [],
#                is_query_endpoint=False
#            )
#            self.endpoints[name] = endpoint
#
#            @wraps(fn)
#            def wrapper(*args, **kwargs):
#                return self.run_mutation(name, *args, **kwargs)
#
#            return wrapper
#        return decorator
#
#    def run_query(self, endpoint_name: str, *args, **kwargs) -> TResponse:
#        if self.base_query_fn is None:
#            raise ValueError("base_query function is not set.")
#
#        endpoint = self.endpoints.get(endpoint_name)
#        if endpoint is None or not endpoint.is_query:
#            raise ValueError(f"No query endpoint named '{endpoint_name}' found.")
#
#        request_def = endpoint.request_fn(*args, **kwargs)
#        cached_response = self.cache_strategy.get(endpoint_name, request_def)
#        if cached_response is not None:
#            return cached_response
#
#        assert self.base_query_fn_handler
#        response = self.base_query_fn_handler(self.base_query_config, request_def)
#        self.cache_strategy.set(endpoint_name, request_def, response, endpoint.provides_tags)
#        return response
#
#    def run_mutation(self, endpoint_name: str, *args, **kwargs) -> TResponse:
#        if self.base_query_fn is None:
#            raise ValueError("base_query function is not set.")
#
#        endpoint = self.endpoints.get(endpoint_name)
#        if endpoint is None or not endpoint.is_mutation:
#            raise ValueError(f"No mutation endpoint named '{endpoint_name}' found.")
#
#        request_def = endpoint.request_fn(*args, **kwargs)
#        assert self.base_query_fn_handler
#        response = self.base_query_fn_handler(self.base_query_config, request_def)
#        if endpoint.invalidates_tags:
#            self.cache_strategy.invalidate_tags(endpoint.invalidates_tags)
#        return response
#
# For more info on Reddit API rules, see: https://github.com/reddit-archive/reddit/wiki/API
REDDIT_USER_AGENT = "MyRedditClient/0.1 by YourUsername"
OAUTH_TOKEN = "your_oauth_token_here"  # Replace with a valid token if needed

from pydantic import BaseModel

from core.api import Api
from core.types import BaseQueryConfig, RequestDefinition

reddit_api = Api[RequestDefinition, Any](
        base_query_config=BaseQueryConfig(
            base_url="https://oauth.reddit.com",
            prepare_headers=lambda headers: {
                    **headers,
                    "User-Agent": REDDIT_USER_AGENT,
                    "Authorization": f"bearer {OAUTH_TOKEN}"
            }
        ),
        #cache_strategy=InMemoryCacheStrategy()
    )



@reddit_api.base_query_fn
def reddit_base_query(config: BaseQueryConfig, req: RequestDefinition) -> Any:
    # Prepare the final URL. If it's relative, prepend base_url.
    if config.base_url and not req["url"].startswith("http"):
        req_url = f"{config.base_url}{req["url"]}"
    else:
        req_url = req["url"]

    headers = req.get("headers", {})
    assert headers is not None
    prepared_headers = config.prepare_headers(headers) if config.prepare_headers else headers

    response = requests.request(
        method=req["method"],
        url=req_url,
        json=req.get("body"),
        headers=prepared_headers
    )
    response.raise_for_status()
    return response.json()

# -------------------------
# Example Endpoints
# -------------------------
class HotSubreddit(BaseModel):
    hot: str


@reddit_api.query("getSubredditHot", provides_tags=["SubredditPosts"], response_type=HotSubreddit)
def get_subreddit_hot(subreddit: str, limit: int = 10) -> RequestDefinition:
    """Get the hot posts for a given subreddit."""
    return RequestDefinition(
        method="GET",
        url=f"/r/{subreddit}/hot.json?limit={limit}"
    )

async def a():
    a = await get_subreddit_hot(is_async=False, subreddit="python", limit=10)





class UserInfo(BaseModel):
    hot: str

@reddit_api.query("getUserInfo", provides_tags=["UserInfo"], response_type=UserInfo)
def get_user_info(username: str) -> RequestDefinition:
    """Get information about a Reddit user."""
    return RequestDefinition(
        method="GET",
        url=f"/user/{username}/about.json"
    )


@reddit_api.mutation("savePost", invalidates_tags=["SubredditPosts"])
def save_post(post_fullname: str) -> RequestDefinition:
    """Save a post (requires authenticated user and correct scopes)."""
    return RequestDefinition(
        method="POST",
        url="/api/save",
        body={"id": post_fullname}
    )

save_post(post_fullname="t3_9i1r7")



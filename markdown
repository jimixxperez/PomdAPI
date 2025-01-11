# Core API Reference

The core API module provides the base functionality for creating and managing APIs with built-in caching support.

## Api Class

::: core.api.Api
    options:
      show_root_heading: true
      show_source: true

The `Api` class is the main entry point for interacting with the API. It provides decorators for defining query and mutation endpoints.

### Query Decorator

```python
@api.query(
    name: str,
    response_type: Type[ResponseType],
    provides_tags: Optional[list[str]] = None
)
```

Parameters:

- `name`: The name of the query endpoint
- `response_type`: The expected return type of the query
- `provides_tags`: Optional list of cache tags this query provides

Example:

```python
@api.query("getUser", response_type=User)
def get_user(user_id: str):
    return {"path": f"/users/{user_id}"}
```

### Mutation Decorator

```python
@api.mutation(
    name: str,
    response_type: Optional[Type[ResponseType]] = None,
    invalidates_tags: Optional[list[str]] = None
)
```

Parameters:

- `name`: The name of the mutation endpoint
- `response_type`: Optional return type of the mutation
- `invalidates_tags`: Optional list of cache tags this mutation invalidates

Example:

```python
@api.mutation("createUser", response_type=User)
def create_user(data: CreateUserInput):
    return {
        "path": "/users",
        "method": "POST",
        "body": data.dict()
    }
```

## BaseQueryConfig

::: core.types.BaseQueryConfig
    options:
      show_root_heading: true
      show_source: true

The `BaseQueryConfig` class holds the configuration for API requests.

## EndpointDefinition

::: core.types.EndpointDefinition
    options:
      show_root_heading: true
      show_source: true

The `EndpointDefinition` class represents a single endpoint in the API.
# HTTP API Reference

The HTTP API module provides implementation for RESTful HTTP APIs.

## HttpApi Class

::: api.http.HttpApi
    options:
      show_root_heading: true
      show_source: true

The `HttpApi` class extends the base `Api` class with HTTP-specific functionality.

### Creating an Instance

```python
from api.http import HttpApi
from core.types import BaseQueryConfig

api = HttpApi.from_defaults(
    base_query_config=BaseQueryConfig(
        base_url="https://api.example.com"
    )
)
```

### Request Definition

The HTTP API uses a `RequestDefinition` class to define requests:

```python
@dataclass
class RequestDefinition:
    path: str
    method: str = "GET"
    headers: Optional[dict[str, str]] = None
    params: Optional[dict[str, Any]] = None
    body: Optional[Any] = None
```

### Example Usage

```python
@api.query("getUsers", response_type=List[User])
def get_users(page: int = 1):
    return {
        "path": "/users",
        "params": {"page": page}
    }

@api.mutation("createUser", response_type=User)
def create_user(user_data: CreateUserInput):
    return {
        "path": "/users",
        "method": "POST",
        "body": user_data.dict()
    }
```
# Core API Reference

This section covers the core components of the API library.

## Api Class

The `Api` class is the main entry point for creating and managing APIs. It provides decorators for defining query and mutation endpoints with built-in caching support.

### Key Features

- Type-safe endpoint definitions
- Built-in caching support
- Async/sync operation support
- Automatic response validation

### Example Usage

```python
from api.http import HttpApi
from core.types import BaseQueryConfig

api = HttpApi.from_defaults(
    base_query_config=BaseQueryConfig(
        base_url="https://api.example.com"
    )
)

@api.query("getUser", response_type=User)
def get_user(id: str):
    return {"path": f"/users/{id}"}
```

## BaseQueryConfig

The `BaseQueryConfig` class holds common configuration for all API requests.

### Attributes

- `base_url`: Base URL for all API requests
- `prepare_headers`: Function to modify request headers

### Example

```python
config = BaseQueryConfig(
    base_url="https://api.example.com/v1",
    prepare_headers=lambda headers: {
        **headers,
        "Authorization": f"Bearer {token}"
    }
)
```

## EndpointDefinition

The `EndpointDefinition` class represents a single API endpoint.

### Properties

- `is_query`: True if endpoint is a query
- `is_mutation`: True if endpoint is a mutation
- `request_fn`: Function that generates the request definition

## Cache

The `Cache` class provides caching functionality for API responses.

### Key Features

- Tag-based cache invalidation
- Support for TTL (Time To Live)
- Async/sync operations

### Example

```python
from cache.in_memory import InMemoryCache

cache = InMemoryCache()
api = HttpApi.from_defaults(
    base_query_config=config,
    cache=cache
)
```

## CacheBackend

The `CacheBackend` protocol defines the interface for cache implementations.

### Required Methods

- `get`/`aget`: Retrieve cached items
- `set`/`aset`: Store items in cache
- `delete`/`adelete`: Remove items from cache

### Available Implementations

- `InMemoryCache`: Simple in-memory caching
- `MemcachedCache`: Distributed caching with Memcached
- `RedisCache`: Redis-based caching
# HTTP API Reference

## HttpApi

::: api.http.HttpApi

## Request Models

::: api.http.RequestDefinition
# JSON-RPC API Reference

## JSONRPCRequest

::: api.jsonrpc.JSONRPCRequest

## JSONRPCResponse

::: api.jsonrpc.JSONRPCResponse

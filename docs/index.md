# API Library Documentation

# Papperlapi

**Papperlapi** is a lightweight, Pythonic solution for creating strongly-typed API clients. 
It supports synchronous and asynchronous calls out of the box, offers powerful tag-based caching 
to manage invalidations, and integrates seamlessly with frameworks like Pydantic for request/response models.

## Key Features

-  🎯 **Easy Definition of Endpoints**: Decorate query and mutation functions to define your API calls. 
- **🚀 Support for multiple API protocols**: HTTP, JSON-RPC or any custom protocol.
- 🔒 **Typed Responses**: Use `pydantic.BaseModel` or native Python types to ensure strict typing.
- ⚡ **Automatic Sync/Async**: The same function can be called synchronously or asynchronously, no code duplication required.
- 🔖 **Tag-Based Caching**: Invalidate entire lists or single items via tags.
- 💾 **Extensible Caching Backends**: In-memory, Memcached, Redis, or any custom backend implementing `CacheBackend`.

Whether you’re building a small prototype or a large-scale service, these features help keep your code clean, consistent, and reliable. For more hands-on guides, check out our Getting Started page or explore the Examples of how you can integrate papperlapi into real-world projects.

To learn more about each feature, check out our [Features](features.md) page or dive straight into the [Getting Started](getting-started.md) guide.


## Installation

```bash
pip install your-package-name
```

## Quick Start

```python
from api.http import HttpApi
from cache.in_memory import InMemoryCache

# Create an API instance with in-memory caching
api = HttpApi.from_defaults(
    base_query_config=BaseQueryConfig(base_url="https://api.example.com"),
    cache=InMemoryCache()
)

# Define a query endpoint
@api.query("getUserProfile", response_type=UserProfile)
def get_user_profile(user_id: str):
    return {"path": f"/users/{user_id}"}

# Use the API
async def main():
    profile = await get_user_profile(is_async=True, user_id="123")
    print(profile)
```
## Motiviation

Modern web applications often rely on data from remote APIs, and keeping that data in sync with the server can be challenging. You need to track loading states, prevent duplicate requests, handle optimistic updates, and manage cache lifetimes, among many other tasks. This library, inspired in part by RTK Query’s philosophy, aims to simplify data fetching and caching so you can focus on building features instead of reinventing boilerplate or manually handling these complexities.
Why This Library?

Historically, Python-based solutions for fetching data and caching within a UI or application have required significant custom logic: you’d write manual request handling, caching layers, and code to invalidate or refetch data. This library abstracts those common requirements:

 - **Declarative Endpoints**
  Define your endpoints (queries and mutations) in one place. For example, you might describe how to fetch GitHub issues or an Ethereum account balance, without worrying about repetitive request code each time.

 - **Built-In Caching**
    Reduce unneeded requests and handle partial data updates through out-of-the-box caching. You can choose among in-memory, Memcached, or Redis backends to fit your caching needs.

 - **Sync or Async**
    APIs and cache operations can be run synchronously or asynchronously, powered by Python’s async/await. This means you can integrate the library into both traditional blocking contexts (like simple scripts) and async-based web frameworks.

 - **Pluggable Protocols**
    The library includes handlers for multiple request protocols such as HTTP, JSON-RPC, and XML-RPC, with easy patterns to add more. Each API type uses the same Api base, so you can take advantage of a consistent interface regardless of protocol.

 - **Type-Safe**
    Built using Python’s type hints and Pydantic models, so you get compile-time checks and runtime validation. This reduces bugs and makes the data structures you pass around more predictable.

FastAPI vs. PomdAPI: An Inversion

FastAPI is a server framework that uses parameter decorators to build endpoints. For example, you write code like:

```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/item/{item_id}")
def read_user(item_id: int):
  ...
```
Here, FastAPI uses the function signature (e.g., item_id, q) to parse incoming requests, inject them as arguments, and produce a server response.

PomdAPI, by contrast, does the client-side inverse. You define a function that takes parameters (like item_id, q), and the library uses them to build the outgoing request to a server. For example:

```python
from pomdapi.api.http import HttpApi

api = HttpApi(...)

@api.query("getItem")
def get_item(item_id: str, q: str | None = None):
    return RequestDefinition(
        method="GET",
        url="/items/{item_id}",
    )
  )
```
|   | FastAPI (Server) | PomdAPI (Client) |
|---|---|---|
| **What it does?** | Exposes a path like /items/{item_id}. The function runs when that path is requested. | Parametrizes a client call to that path (or another remote service). The function returns a “request definition” that includes how to fetch or mutate data. |
| **Parameter usage** | Extract request parameters from path/query, injecting them into the function signature. | Use function parameters to dynamically build the request config—URL, method, etc. The library then executes the request and returns (or caches) the response. |
| **Result** | A server-side function that runs for incoming requests. | A client-side function that makes requests to a remote server, with caching and tagging built-in. |




Key Features

    Request Lifecycle Management
    Handle the lifecycle of requests with minimal boilerplate—track loading states, catch errors, and refetch data as needed.

    Cache Invalidation
    Automatically (or manually) invalidate cache entries when you perform state-changing operations, so your application is always up to date.

    Optimistic Updates
    Implement patterns like "optimistic UI", where you update your local state immediately for a snappy UI, then roll back if the server update fails.

    Expandable Architecture
    Extend the library’s approach to new protocols or custom caching strategies if needed, thanks to well-defined interfaces and protocols in the core.

Putting It All Together

At a high level, you create a new Api (for instance, an HttpApi) by providing:

    A base query configuration (e.g., endpoint URLs or default headers).
    Optional cache configuration (like an in-memory or Memcached backend).
    Define queries (for reads) and mutations (for writes) with decorators that specify the request details and expected response types.
    Call these query/mutation endpoints in your code (synchronously or asynchronously), and let the library handle request logic, caching, and invalidation.

Conclusion

By removing the heavy lifting typically associated with data fetching and caching logic, this library lets you focus on delivering value to your users. It leverages a modular and type-friendly architecture, supports multiple transport protocols, and offers both sync and async flows to fit a variety of Python use cases—all in one cohesive package.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

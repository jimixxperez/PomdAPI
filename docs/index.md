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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

# API Library Documentation

A powerful and flexible API library with built-in caching support for HTTP, JSON-RPC, and XML-RPC protocols.

## Features

- 🚀 Support for multiple API protocols
- 💾 Built-in caching with multiple backends
- ⚡ Async and sync operations
- 🔒 Type-safe API definitions
- 🎯 Easy to use decorators for queries and mutations

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

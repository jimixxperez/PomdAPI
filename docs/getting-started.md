# Getting Started

This guide will help you get started with the API library.

## Installation

First, install the package using pip:

```bash
pip install your-package-name
```

## Basic Usage

### Creating an API Instance

```python
from api.http import HttpApi
from core.types import BaseQueryConfig

api = HttpApi.from_defaults(
    base_query_config=BaseQueryConfig(
        base_url="https://api.example.com"
    )
)
```

### Defining Queries

```python
from typing import List
from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    email: str

@api.query("getUsers", response_type=List[User])
def get_users():
    return {"path": "/users"}
```

### Using Mutations

```python
@api.mutation("createUser", response_type=User)
def create_user(name: str, email: str):
    return {
        "path": "/users",
        "method": "POST",
        "body": {"name": name, "email": email}
    }
```

### Adding Caching

```python
from cache.in_memory import InMemoryCache

api = HttpApi.from_defaults(
    base_query_config=BaseQueryConfig(
        base_url="https://api.example.com"
    ),
    cache=InMemoryCache()
)
```

## Next Steps

- Check out the [API Reference](../api-reference/core.md) for detailed documentation
- See [Examples](../examples/github.md) for practical use cases
- Learn about [Caching](../caching/overview.md) options

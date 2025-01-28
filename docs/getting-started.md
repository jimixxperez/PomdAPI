# Getting Started

This guide will help you get started with the API library.

## Installation

First, install the package using pip:

```bash
pip install papperlapi 
```

## Basic Usage
### Api

The Api builds the scaffold of PomDAPI and links the data fetching, caching and type definitions together.
You can either use the Api provided by PomdAPI directly or create your own API. See the [API Reference](references/api_http.md).

#### Creating an API

To create an API, you need to define a BaseQueryConfig and pass it to the API constructor.

The base query config holds the base URL for all requests and any additional headers that need to be added to all requests.

You can also pass a cache instance to the API constructor to enable caching.


### Query
#### Overview

This is the most common use case for PomdAPI. A query operation can be performed with any data fetching library of your choice, but the general recommendation is that you only use queries for requests that retrieve data. For anything that alters data on the server or will possibly invalidate the cache, you should use a Mutation.

By default, PomdAPI Query ships with fetchBaseQuery, which is a lightweight fetch wrapper that automatically handles request headers and response parsing in a manner similar to common libraries like axios. See Customizing Queries if fetchBaseQuery does not handle your requirements.

#### Defining Query Endpoints

Query endpoints are defined by returning an object inside the endpoints section of createApi, and defining the fields using the builder.query() method.

Query endpoints should define either a query callback that constructs the URL (including any URL query params), or a queryFn callback that may do arbitrary async logic and return a result.

If the query callback needs additional data to generate the URL, it should be written to take a single argument. If you need to pass in multiple parameters, pass them formatted as a single "options object".

Query endpoints may also modify the response contents before the result is cached, define "tags" to identify cache invalidation, and provide cache entry lifecycle callbacks to run additional logic as cache entries are added and removed.

When used with TypeScript, you should supply generics for the return type and the expected query argument: build.query<ReturnType, ArgType>. If there is no argument, use void for the arg type instead.

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

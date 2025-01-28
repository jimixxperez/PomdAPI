# Hands-On Overview

 This document introduces the main concepts and shows you how to build and call queries/mutations with the built-in HTTP implementation.

---

## 1. Basic Concepts

### 1.1 The `Api` Class

- The central building block in **PomdAPI**.  
- Manages:
    1. **Endpoint definitions** (query vs. mutation)
    2. **Base query config** (common settings, like a base URL or default headers)
    3. **Base query function** (the function actually performing requests)
    4. **Caching** (tag-based invalidation, optional but powerful)

### 1.2 HTTP Implementation

- **`HttpApi`** is a subclass of `Api` specialized for HTTP calls.
  - Uses [httpx](https://www.python-httpx.org/) under the hood.
  - Exposes decorators `@http_api.query(...)` and `@http_api.mutation(...)` to define endpoints.
  - A typical request is described by a `RequestDefinition`: method, path, body, and headers.

### 1.3 Tag-Based Caching

- You can attach one or more **tags** to an endpoint’s response.  
- **Queries** _provide_ tags, so their responses are cached under those tags.  
- **Mutations** _invalidate_ tags, telling the cache to discard any data associated with them.

> **Why use tags?**  
> Fine-grained cache invalidation. For example, an endpoint returning `Issue #42` can be tagged with `type=Issue, id=42`. Later, a mutation that updates issue #42 can automatically invalidate that single entry.

---

## 2. Setting Up an HTTP Api

Below is a minimal example for GitHub’s REST API. We’ll create a `HttpApi` with a base URL and optional caching.

```python
from pomdapi.api.http import HttpApi, BaseQueryConfig
from pomdapi.cache.in_memory import InMemoryCache

# 1) Define your base config
config = BaseQueryConfig(
    base_url="https://api.github.com",
    # Optionally inject extra headers
    prepare_headers=lambda headers: {
        "Accept": "application/vnd.github.v3+json",
        **headers
    }
)

# 2) (Optional) Create a cache
cache = InMemoryCache()

# 3) Instantiate the HttpApi
github_api = HttpApi.from_defaults(
    base_query_config=config,
    cache=cache
)


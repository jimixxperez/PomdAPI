# Api

## Introduction

In pomdapi, the [`Api`](./references/api_http.md) class is the foundation for defining and calling endpoints. It can be extended to build Api such the HttpApi.

This document dissects the main concepts:

| Concept| Description|
| --------| ----------|
| **Endpoint definition** | Captures how your function transforms parameters into a request |
| **BaseQueryConfig** | holds global configuration for your API calls (e.g., a base URL or shared headers). | 
|**BaseQueryConfig** | the low-level sync/async functions that actually peform the network operation  |

Read on for deeper understanding of how these piece fit together.

## 1. The `Api` class (Core)

### 1.1 Generic Type Parameters

```python

@datclass
class Api(Generic[RequestDefinitionGen, BaseQueryConfig, TResponse]):
    ...
```

1. **EndpointDefinitionGen**: The shape or structure your endpoint returns. For an HTTP API, this is a RequestDefinition (i.e., which method, path, body, headers).

2. **BaseQueryConfig**: A configuration object that’s available to all endpoints. For HTTP, this might store the base_url or a function to prepare headers.

3. **TResponse** : The type your endpoint’s responses will produce.

The `Api` class uses these generics to remain flexible: it doesn’t know or care how you’ll do your network calls—it only provides the structure for defining endpoints and optionally caching responses.

### 1.2 Storing Endpoints
The `Api` class has a dictionary:

```python 
endpoints: dict[str, EndpointDefinition[EndpointDefinitionGen]] = field(default_factory=dict)
```


- each endpoint is keyed by name (e.g., "getRepoIssue")
- the value is an `EndpointDefinition`, which includes:
    - `request_fn`: The user's decorated fucntion that builds a RequestDefinition
    - `is_query_endpoint`: a flag inidcation query vs mutation
```

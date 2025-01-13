Papperlapi helps you build typed API clients with out-of-the-box support for both synchronous and asynchronous usage, powerful caching, and intuitive configuration. Below are the major features that set Papperlapi apart.

### Synchronous & Asynchronous Calls

One of papperlapi’s standout features is that **any** query or mutation endpoint can be used synchronously or asynchronously—**no** separate code paths required!

**Example**:

```python
from papperlapi.core.types import Tag
from papperlapi.api.http import HttpApi, RequestDefinition
from papperlapi.cache.in_memory import InMemoryCache

api = HttpApi.from_defaults(..., cache=InMemoryCache())

@api.query("getData", response_type=dict)
def get_data(param: str):
    return RequestDefinition(
        method="GET",
        url=f"/data?param={param}",
    )

# Synchronous usage:
result_sync = get_data(is_async=False, param="test")
print("Sync result:", result_sync)

# Asynchronous usage:
import asyncio

async def main():
    result_async = await get_data(param="async-test")
    print("Async result:", result_async)

asyncio.run(main())
```
What’s happening:

- `@api.query(...)` registers an endpoint named "getData".
- We invoke `get_data(is_async=False, ...)` to run it synchronously.
- We then invoke `await get_data(...)` for the asynchronous version—no extra code needed.

### Typed Endpoints with Pydantic

papperlapi integrates neatly with Pydantic, ensuring your API responses match a specified schema. If the JSON from the server doesn’t match your model, a validation error is raised—preventing silent failures.


```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str

@api.query("getUser", response_type=User)
def get_user(user_id: int):
    return RequestDefinition(
        method="GET",
        url=f"/users/{user_id}",
    )

# Let's make a synchronous call for demonstration
user = get_user(is_async=False, user_id=42)
print("User:", user)
print("User type:", type(user))  # <class '__main__.User'>
```

### Tag-Based Caching and Invalidation

papperlapi uses tags to track cached items. Queries “provide” tags, mutations “invalidate” them—so it’s easy to refetch only what’s needed when data changes.


```python
from papperlapi.core.types import Tag

@api.query("getRepoIssue", response_type=dict)
def get_repo_issue(owner: str, repo: str, issue_number: int):
    # Provide a tag for this issue
    return (
        RequestDefinition(
            method="GET",
            url=f"/repos/{owner}/{repo}/issues/{issue_number}",
        ),
        Tag(type="Issue", id=str(issue_number))
    )

@api.mutation("closeIssue")
def close_issue(owner: str, repo: str, issue_number: int):
    # Invalidate the single-issue tag
    return (
        RequestDefinition(
            method="PATCH",
            url=f"/repos/{owner}/{repo}/issues/{issue_number}",
            body={"state": "closed"},
        ),
        Tag(type="Issue", id=str(issue_number))
    )

# Now, if we call close_issue, papperlapi invalidates that specific issue in the cache
close_issue(is_async=False, owner="octocat", repo="hello-world", issue_number=42)

```

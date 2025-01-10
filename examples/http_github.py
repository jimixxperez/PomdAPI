import os
from typing import Literal
from pydantic import BaseModel
from core.types import Tag
from api.http import HttpApi, RequestDefinition
from cache.in_memory import InMemoryCache
from core.types import BaseQueryConfig

GITHUB_BASE_URL = "https://api.github.com"
GITHUB_TOKEN =   os.environ["GITHUB_TOKEN"]

github_api = HttpApi.from_defaults(
    base_query_config=BaseQueryConfig(
        base_url=GITHUB_BASE_URL,
        # Automatically attach common headers
        prepare_headers=lambda headers: {
            **headers,
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        },
    ),
    cache=InMemoryCache(),
)


class Issue(BaseModel):
    id: int
    number: int
    title: str
    state: str
    body: str | None = None
    # ... other fields returned by GitHub if you like


@github_api.query("getRepoIssues", response_type=list[Issue])
def get_repo_issues(owner: str, repo: str, state: str = "open"):
    """
    Fetch issues for a given owner/repo.
    This query 'provides' a tag for the list of issues, typically 'Issue/LIST'.
    """
    return (
        RequestDefinition(
            method="GET",
            url=f"/repos/{owner}/{repo}/issues?state={state}",
        ),
        Tag(type="Issue", id="LIST"),  # Represent the entire list of issues
    )


@github_api.query("getRepoIssue", response_type=Issue)
def get_repo_issue(owner: str, repo: str, issue_number: int):
    """
    Fetch a single issue for a repository by its issue number.
    This query 'provides' a tag for the specific issue.

    Notes
    -----
        - We attach a unique tag for each issue, e.g Tag(type="Issue", id="123")
        - Whenever you mutate or invalidate that tag, this specific issue will be invalidated

    """
    return (
        RequestDefinition(
            method="GET",
            url=f"/repos/{owner}/{repo}/issues/{issue_number}",
        ),
        Tag(type="Issue", id=str(issue_number)),
    )


class CreateIssueRequest(BaseModel):
    title: str
    body: str | None = None
    assignees: list[str] | None = None

class CreateIssueResponse(BaseModel):
    id: int
    number: int

@github_api.mutation("createIssue", response_type=CreateIssueResponse)
def create_issue(owner: str, repo: str, issue_data: CreateIssueRequest):
    """
    Create a new issue in the repo.

    Notes:
    -----
        - on success, we invalidate the list of issues

    """
    return (
        RequestDefinition(
            method="POST",
            url=f"/repos/{owner}/{repo}/issues",
            body=issue_data.model_dump(exclude_none=True),
        ),
        Tag(type="Issue", id="LIST"),  # Invalidate the issues list
    )


class UpdateIssueRequest(BaseModel):
    title: str | None = None
    body: str | None = None
    state: Literal["open", "closed"] | None = None


@github_api.mutation("updateIssue")
def update_issue(
    owner: str, repo: str, issue_number: int, update_data: UpdateIssueRequest
):
    """
    Update an issue (title, body, or state).

    Notes
    -----
        We invalidate the specific issue's tag so that 'getRepoIssue' will be refetched if it was previously cached.
    """
    return (
        RequestDefinition(
            method="PATCH",
            url=f"/repos/{owner}/{repo}/issues/{issue_number}",
            body=update_data.model_dump(exclude_none=True),
        ),
        Tag(type="Issue", id=str(issue_number)),
    )


@github_api.mutation("lockIssue")
def lock_issue(owner: str, repo: str, issue_number: int):
    """
    Locks an issue from further comments.Aq

    Notes:
    -----
        This may or may not affect the issue's visible fields,
        so we can choose to invalidate both the single issue and the entire list.
    """
    return (
        RequestDefinition(
            method="PUT",
            url=f"/repos/{owner}/{repo}/issues/{issue_number}/lock",
        ),
        (
            Tag(type="Issue", id=str(issue_number)),
            Tag(type="Issue", id="LIST"),
        ),
    )

if __name__ == "__main__":
    print("""
     BEHIND THE SCENES
     - Creating an issue invalidates the 'LIST' tag →  refetch when calling `get_repo_issues`.
     - Updating an issue invalidates the single-issue tag → refetch when calling `get_repo_issue`.
     - Locking/deleting an issue might invalidate both the single-issue tag and the 'LIST.'
    """)
    print("Synchronous usage")
    open_issues = get_repo_issues(is_async=False, owner="octocat", repo="Hello-World")
    first_issue = get_repo_issue(is_async=False, owner="octocat", repo="Hello-World", issue_number=1)
    print(f"first issue: {first_issue}")

    print("Mutation example")
    new_issue = create_issue(
        is_async=False,
        owner="octocat",
        repo="Hello-World",
        issue_data=CreateIssueRequest(title="New Issue from Python", body="Hello from my script", assignees=["octocat"]),
    )
    print(f"new issue: {new_issue}")

    print("Asynchronous usage out of the box - `is_async` flag defaults to `True`") 
    import asyncio

    async def main():
        await update_issue(
            is_async=True,
            owner="octocat",
            repo="Hello-World",
            issue_number=new_issue.number,
            update_data=UpdateIssueRequest(state="closed")
        )
        print("`get_repo_issue` will refetch the issue")
        print("note that we are calling the same function again, but this time with `is_async=True`")
        new_updated_issue = await get_repo_issue(
            is_async=True, 
            owner="octocat", 
            repo="Hello-World", 
            issue_number=new_issue.number,
        )
        print("Updated Issue:", new_updated_issue)

    asyncio.run(main())


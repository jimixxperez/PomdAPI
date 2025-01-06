from httpx import Request
from pydantic import BaseModel

from api.http import HttpApi, RequestDefinition
from core.types import BaseQueryConfig

# For more info on Reddit API rules, see: https://github.com/reddit-archive/reddit/wiki/API
REDDIT_USER_AGENT = "MyRedditClient/0.1 by YourUsername"
OAUTH_TOKEN = "your_oauth_token_here"  # Replace with a valid token if needed

reddit_api = HttpApi.from_defaults(
    base_query_config=BaseQueryConfig(
        base_url="https://oauth.reddit.com",
        prepare_headers=lambda headers: {
            **headers,
            "User-Agent": REDDIT_USER_AGENT,
            "Authorization": f"bearer {OAUTH_TOKEN}",
        },
    ),
)


class HotSubreddit(BaseModel):
    hot: str


@reddit_api.query(
    "getSubredditHot", provides_tags=["SubredditPosts"], response_type=HotSubreddit
)
def get_subreddit_hot(subreddit: str, limit: int = 10) -> RequestDefinition:
    """Get the hot posts for a given subreddit."""
    return RequestDefinition("")


class UserInfo(BaseModel):
    """
    User info
    """

    hot: str


from core.types import Tag


@reddit_api.query("getUserInfo", response_type=UserInfo)
def get_user_info(username: str):
    """Get information about a Reddit user."""
    return (
        RequestDefinition(
            method="GET",
            url=f"/user/{username}/about.json",
        ),
        Tag(type="UserInfo", id=username),
    )


@reddit_api.mutation("savePost")
def save_post(post_fullname: str):
    """Save a post (requires authenticated user and correct scopes)."""
    return RequestDefinition(
        method="POST",
        url="/api/save",
        body={"id": post_fullname},
    ), Tag("Post", id=post_fullname)


if __name__ == "__main__":
    # sync version
    hot_subreddits = get_subreddit_hot(is_async=False, subreddit="reddit", limit=20)
    user_info = get_user_info(is_async=False, username="test")

    import asyncio

    loop = asyncio.get_event_loop()
    hot_subreddits = loop.run_until_complete(
        get_subreddit_hot(subreddit="data_science", limit=10)
    )
    hot_subreddits = loop.run_until_complete(
        get_subreddit_hot(is_async=True, subreddit="data_science", limit=10)
    )

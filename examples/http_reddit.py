from pydantic import BaseModel

from api.http import RequestDefinition, HttpApi
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
    return {"method": "GET", "url": f"/r/{subreddit}/hot.json?limit={limit}"}


class UserInfo(BaseModel):
    hot: str


@reddit_api.query("getUserInfo", provides_tags=["UserInfo"], response_type=UserInfo)
def get_user_info(username: str) -> RequestDefinition:
    """Get information about a Reddit user."""
    return {
        "method": "GET",
        "url": f"/user/{username}/about.json",
    }


@reddit_api.mutation("savePost", invalidates_tags=["SubredditPosts"])
def save_post(post_fullname: str) -> RequestDefinition:
    """Save a post (requires authenticated user and correct scopes)."""
    return {
        "method": "POST",
        "url": "/api/save",
        "body": {"id": post_fullname},
    }


if __name__ == "__main__":
    # sync version
    hot_subreddits = get_subreddit_hot(is_async=False, subreddit="reddit", limit=20)

    import asyncio

    loop = asyncio.get_event_loop()
    hot_subreddits = loop.run_until_complete(
        get_subreddit_hot(subreddit="data_science", limit=10)
    )
    hot_subreddits = loop.run_until_complete(
        get_subreddit_hot(is_async=True, subreddit="data_science", limit=10)
    )

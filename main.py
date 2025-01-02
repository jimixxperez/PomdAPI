import requests
from xml.etree import ElementTree as ET
from typing import Callable, Generic, Required, Self, Type, TypeVar, Dict, List, Optional, Any, Tuple, TypedDict, cast
from dataclasses import dataclass, field
from time import time
from functools import wraps

#
# For more info on Reddit API rules, see: https://github.com/reddit-archive/reddit/wiki/API
REDDIT_USER_AGENT = "MyRedditClient/0.1 by YourUsername"
OAUTH_TOKEN = "your_oauth_token_here"  # Replace with a valid token if needed

from pydantic import BaseModel

from core.api import Api
from core.types import BaseQueryConfig, RequestDefinition

reddit_api = Api[RequestDefinition, Any](
        base_query_config=BaseQueryConfig(
            base_url="https://oauth.reddit.com",
            prepare_headers=lambda headers: {
                    **headers,
                    "User-Agent": REDDIT_USER_AGENT,
                    "Authorization": f"bearer {OAUTH_TOKEN}"
            }
        ),
        #cache_strategy=InMemoryCacheStrategy()
    )






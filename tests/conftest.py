import pytest
from pomdapi.cache.in_memory import InMemoryCache
from pomdapi.cache.memcached import MemcachedCache

@pytest.fixture
def in_memory_cache():
    return InMemoryCache()

@pytest.fixture
def memcached_cache():
    return MemcachedCache(host="localhost", port=11211)

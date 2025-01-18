import pytest
from pomdapi.cache.memcached import MemcachedBackend
from typing import Optional, Any

@pytest.mark.parametrize("key,value,ttl", [
    ("memcached_key", {"data": "test"}, None),
    ("memcached_str", "string_value", 60),
    ("memcached_empty", {}, 30),
])
def test_memcached_backend_set_get(key: str, value: dict[str, Any] | str, ttl: Optional[int]):
    backend = MemcachedBackend()
    backend.set(key, value, ttl)
    result = backend.get(key)
    assert result == value

@pytest.mark.parametrize("key", [
    "nonexistent_memcached",
    "",
    "deleted_memcached"
])
def test_memcached_backend_get_nonexistent(key: str):
    backend = MemcachedBackend()
    result = backend.get(key)
    assert result is None

@pytest.mark.asyncio
@pytest.mark.parametrize("key,value,ttl", [
    ("async_memcached", {"data": "async_test"}, None),
    ("another_async_memcached", "async_string", 60),
])
async def test_memcached_backend_async_operations(key: str, value: dict[str, Any] | str, ttl: Optional[int]):
    backend = MemcachedBackend()
    await backend.aset(key, value, ttl)
    result = await backend.aget(key)
    assert result == value
    
    await backend.adelete(key)
    result = await backend.aget(key)
    assert result is None

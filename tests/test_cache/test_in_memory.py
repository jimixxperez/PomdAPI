import pytest
from pomdapi.cache.in_memory import InMemoryCache, InMemoryBackend
from typing import Optional, Any

@pytest.mark.parametrize("key,value,ttl", [
    ("test_key", {"data": "test"}, None),
    ("another_key", "string_value", 60),
    ("empty_dict", {}, 30),
])
def test_in_memory_backend_set_get(key: str, value: dict[str, Any] | str, ttl: Optional[int]):
    backend = InMemoryBackend()
    backend.set(key, value, ttl)
    result = backend.get(key)
    assert result == value

@pytest.mark.parametrize("key", [
    "nonexistent_key",
    "",
    "deleted_key"
])
def test_in_memory_backend_get_nonexistent(key: str):
    backend = InMemoryBackend()
    result = backend.get(key)
    assert result is None

@pytest.mark.asyncio
@pytest.mark.parametrize("key,value,ttl", [
    ("async_key", {"data": "async_test"}, None),
    ("another_async_key", "async_string", 60),
])
async def test_in_memory_backend_async_operations(key: str, value: dict[str, Any] | str, ttl: Optional[int]):
    backend = InMemoryBackend()
    await backend.aset(key, value, ttl)
    result = await backend.aget(key)
    assert result == value
    
    await backend.adelete(key)
    result = await backend.aget(key)
    assert result is None

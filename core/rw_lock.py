import asyncio
from dataclasses import dataclass, field


@dataclass
class AsyncRWLock:
    _readers: int = 0
    _readers_lock: asyncio.Lock = asyncio.Lock()
    _resource_lock: asyncio.Lock = asyncio.Lock()

    async def read(self) -> "_ReaderContext":
        return _ReaderContext(self)

    async def write(self) -> "_WriterContext":
        return _WriterContext(self)

    async def acquire_reader(self):
        # First, acquire the _readers_lock to adjust count
        async with self._readers_lock:
            self._readers += 1
            # If you're the first reader, acquire the resource lock
            if self._readers == 1:
                await self._resource_lock.acquire()

    async def release_reader(self):
        async with self._readers_lock:
            self._readers -= 1
            # If no more readers, release the resource lock
            if self._readers == 0:
                self._resource_lock.release()

    async def acquire_writer(self):
        # Writers must acquire the resource lock exclusively
        await self._resource_lock.acquire()

    def release_writer(self):
        self._resource_lock.release()


@dataclass
class _ReaderContext:
    _lock: AsyncRWLock

    async def __aenter__(self):
        await self._lock.acquire_reader()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._lock.release_reader()


@dataclass
class _WriterContext:
    _lock: AsyncRWLock

    async def __aenter__(self):
        await self._lock.acquire_writer()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._lock.release_writer()

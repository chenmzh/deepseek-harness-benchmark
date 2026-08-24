import asyncio
import unittest

from singleflight import AsyncCache


class AsyncCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_fresh_value_is_reused(self):
        calls = 0

        async def loader(key):
            nonlocal calls
            calls += 1
            return {"key": key, "call": calls}

        cache = AsyncCache(loader, ttl=10, stale_ttl=5)
        first = await cache.get("a", 0)
        second = await cache.get("a", 9)
        self.assertEqual(first, second)
        self.assertEqual(calls, 1)

    async def test_concurrent_miss_is_coalesced(self):
        gate = asyncio.Event()
        calls = 0

        async def loader(key):
            nonlocal calls
            calls += 1
            await gate.wait()
            return key

        cache = AsyncCache(loader, ttl=10, stale_ttl=0)
        first = asyncio.create_task(cache.get("a", 0))
        second = asyncio.create_task(cache.get("a", 0))
        await asyncio.sleep(0)
        gate.set()
        self.assertEqual(await asyncio.gather(first, second), ["a", "a"])
        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()

class AsyncCache:
    def __init__(self, loader, ttl, stale_ttl):
        self.loader = loader
        self.ttl = ttl
        self.stale_ttl = stale_ttl
        self.values = {}

    async def get(self, key, now):
        if key not in self.values:
            self.values[key] = await self.loader(key)
        return self.values[key]

    def invalidate(self, key):
        self.values.pop(key, None)

    def clear(self):
        self.values.clear()

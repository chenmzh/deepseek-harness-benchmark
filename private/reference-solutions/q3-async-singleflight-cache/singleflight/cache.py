from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import dataclass
from numbers import Real
from typing import Any


@dataclass
class _Entry:
    value: Any
    fresh_until: float
    stale_until: float


class AsyncCache:
    def __init__(self, loader, ttl, stale_ttl):
        for value, name in ((ttl, "ttl"), (stale_ttl, "stale_ttl")):
            if isinstance(value, bool) or not isinstance(value, Real) or value < 0:
                raise ValueError(f"{name} must be a non-negative number")
        if not callable(loader):
            raise ValueError("loader must be callable")
        self.loader = loader
        self.ttl = float(ttl)
        self.stale_ttl = float(stale_ttl)
        self._entries: dict[Any, _Entry] = {}
        self._inflight: dict[Any, asyncio.Task] = {}
        self._generations: dict[Any, int] = {}
        self._epoch = 0

    @staticmethod
    def _time(now):
        if isinstance(now, bool) or not isinstance(now, Real) or now < 0:
            raise ValueError("now must be a non-negative number")
        return float(now)

    def _consume(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        try:
            task.exception()
        except asyncio.CancelledError:
            pass

    async def _run_load(self, key, now: float, generation: int, epoch: int):
        try:
            loaded = await self.loader(key)
            cached = deepcopy(loaded)
            if self._epoch == epoch and self._generations.get(key, 0) == generation:
                fresh_until = now + self.ttl
                self._entries[key] = _Entry(cached, fresh_until, fresh_until + self.stale_ttl)
            return deepcopy(loaded)
        finally:
            current = asyncio.current_task()
            if self._inflight.get(key) is current:
                del self._inflight[key]

    def _start(self, key, now: float) -> asyncio.Task:
        task = self._inflight.get(key)
        if task is None:
            task = asyncio.create_task(
                self._run_load(key, now, self._generations.get(key, 0), self._epoch)
            )
            task.add_done_callback(self._consume)
            self._inflight[key] = task
        return task

    async def get(self, key, now):
        current = self._time(now)
        entry = self._entries.get(key)
        if entry is not None and current < entry.fresh_until:
            return deepcopy(entry.value)
        if entry is not None and current < entry.stale_until:
            self._start(key, current)
            return deepcopy(entry.value)
        task = self._start(key, current)
        return deepcopy(await asyncio.shield(task))

    def invalidate(self, key):
        self._entries.pop(key, None)
        self._generations[key] = self._generations.get(key, 0) + 1

    def clear(self):
        self._entries.clear()
        self._epoch += 1

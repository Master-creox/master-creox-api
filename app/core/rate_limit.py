"""Basic in-memory rate limiting (Phase 2).

Fixed-window per identity (API key if present, else client IP). Redis-backed
limiting arrives with the Phase 3 data upgrade.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, limit_per_minute: int):
        self.limit = limit_per_minute
        self._hits: dict[str, deque] = defaultdict(deque)

    def allow(self, identity: str) -> bool:
        now = time.time()
        window_start = now - 60
        q = self._hits[identity]
        while q and q[0] < window_start:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True

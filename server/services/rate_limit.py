"""
简单固定窗口限流（进程内）。多 gunicorn worker 时各进程独立计数，生产可换 Redis。
"""

from __future__ import annotations

from collections import deque
from threading import Lock
from time import monotonic


class FixedWindowLimiter:
    def __init__(self, max_events: int, window_sec: float) -> None:
        self.max_events = max_events
        self.window_sec = window_sec
        self._lock = Lock()
        self._events: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        now = monotonic()
        with self._lock:
            q = self._events.setdefault(key, deque())
            while q and now - q[0] > self.window_sec:
                q.popleft()
            if len(q) >= self.max_events:
                return False
            q.append(now)
            return True

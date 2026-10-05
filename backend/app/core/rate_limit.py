import time
from collections import defaultdict, deque

from fastapi import HTTPException, status


class LoginLimiter:
    """5 échecs max par IP + email sur 15 minutes."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        self.max = max_attempts
        self.window = window_seconds
        self.failures = defaultdict(deque)

    def _prune(self, key: str) -> deque:
        q = self.failures[key]
        now = time.monotonic()
        while q and now - q[0] > self.window:
            q.popleft()
        return q

    def check(self, key: str) -> None:
        if len(self._prune(key)) >= self.max:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Trop de tentatives. Réessayez dans quelques minutes.",
            )

    def fail(self, key: str) -> None:
        self._prune(key).append(time.monotonic())

    def reset(self, key: str) -> None:
        self.failures.pop(key, None)


login_limiter = LoginLimiter()
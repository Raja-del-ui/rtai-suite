"""Retry policy with exponential backoff + jitter, clock-injectable for tests."""

import random
import time
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class RetryPolicy:
    attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    retry_on: tuple[type[BaseException], ...] = (
        ConnectionError, TimeoutError, OSError)
    _sleeper: Callable[[float], None] = field(default=time.sleep)

    def should_retry(self, exc: BaseException, attempt: int) -> bool:
        return attempt < self.attempts and isinstance(exc, self.retry_on)

    def delay_for(self, attempt: int) -> float:
        ceiling = min(self.max_delay, self.base_delay * (2 ** attempt))
        return ceiling * random.uniform(0.5, 1.0)

    def run(self, operation: Callable, *args, **kwargs):
        last_error: BaseException | None = None
        for attempt in range(self.attempts):
            try:
                return operation(*args, **kwargs)
            except self.retry_on as exc:  # type: ignore[misc]
                last_error = exc
                if attempt + 1 >= self.attempts:
                    raise
                self._sleeper(self.delay_for(attempt))
        if last_error is not None:
            raise last_error
        raise RuntimeError("retry loop exited without result or error")

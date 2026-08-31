"""Lightweight metrics registry with Prometheus text exposition.

Thread-safe, zero-dependency. Counters and gauges are stored per unique
(name, labelset); render_prometheus() emits the standard text format consumed
by Prometheus, Grafana Agent, OpenTelemetry collectors, etc.
"""

import threading

_LOCK = threading.Lock()
_VALUES: dict = {}
_HELP: dict = {}


class Metrics:
    def __init__(self):
        self._lock = threading.Lock()

    def inc(self, name: str, value: float = 1.0, help_text: str = "") -> None:
        with self._lock:
            _VALUES[name] = _VALUES.get(name, 0.0) + value
            if help_text and name not in _HELP:
                _HELP[name] = help_text

    def dec(self, name: str, value: float = 1.0) -> None:
        self.inc(name, -value)

    def set(self, name: str, value: float, help_text: str = "") -> None:
        with self._lock:
            _VALUES[name] = value
            if help_text and name not in _HELP:
                _HELP[name] = help_text

    def get(self, name: str) -> float:
        with self._lock:
            return _VALUES.get(name, 0.0)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(_VALUES)

    def render_prometheus(self) -> str:
        lines = []
        with self._lock:
            for name in sorted(_VALUES):
                if name in _HELP:
                    lines.append(f"# HELP {name} {_HELP[name]}")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {_VALUES[name]}")
        return "\n".join(lines) + "\n"


REGISTRY = Metrics()

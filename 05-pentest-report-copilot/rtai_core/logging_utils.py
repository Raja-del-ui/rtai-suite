"""Opinionated structured logging: human console + optional JSON lines file."""

import json
import logging
import sys
from pathlib import Path

_RESERVED = frozenset(set(vars(logging.Formatter())) | {"message", "asctime"})


class JsonLinesFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        extra = {k: v for k, v in vars(record).items()
                 if k not in _RESERVED and not k.startswith("_")}
        if extra:
            payload["ctx"] = {k: str(v)[:200] for k, v in extra.items()}
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)[-1500:]
        return json.dumps(payload, default=str)


def setup_logging(verbose=False, json_path=None):
    root = logging.getLogger("rtai")
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-7s %(name)s :: %(message)s", "%H:%M:%S"))
    root.addHandler(console)

    if json_path:
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(json_path, encoding="utf-8")
        file_handler.setFormatter(JsonLinesFormatter())
        root.addHandler(file_handler)
    return root


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"rtai.{name}")

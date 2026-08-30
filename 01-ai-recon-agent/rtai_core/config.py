"""Layered configuration: defaults <- file <- environment <- CLI overrides.

Subclasses declare typed fields as annotated class attributes with defaults
(no decorator required). from_layers() merges layers, rejects unknown keys,
and runs per-field validators passed as VALIDATORS-style callables.
"""

import json
import os
from pathlib import Path
from typing import Callable, Dict, get_type_hints

from rtai_core.exceptions import ConfigError

_LOADERS: Dict[str, Callable[[str], dict]] = {".json": json.loads}


class BaseConfig:
    def __init__(self, **values):
        hints = self._hints()
        unknown = set(values) - set(hints)
        if unknown:
            raise ConfigError(f"unknown config keys: {sorted(unknown)}")
        for name in hints:
            setattr(self, name, values.get(name, getattr(type(self), name, None)))

    @classmethod
    def _hints(cls) -> Dict[str, type]:
        hints = {}
        for klass in reversed(cls.__mro__):
            hints.update(get_type_hints(klass))
        return hints

    @classmethod
    def field_names(cls):
        return list(cls._hints())

    @classmethod
    def from_layers(cls, file_path=None, env_prefix=None, overrides=None,
                    validators=None, env_cast=True):
        data = {}

        if file_path:
            path = Path(file_path)
            loader = _LOADERS.get(path.suffix.lower())
            if loader is None:
                raise ConfigError(f"unsupported config format: {path.suffix}")
            if not path.exists():
                raise ConfigError(f"config file not found: {path}")
            try:
                data.update(loader(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError as exc:
                raise ConfigError(f"invalid JSON in {path}: {exc}") from exc

        if env_prefix:
            hints = cls._hints()
            for name in cls.field_names():
                raw = os.environ.get(f"{env_prefix}{name.upper()}")
                if raw is None:
                    continue
                expected = hints.get(name, str)
                if expected is bool:
                    data[name] = raw.strip().lower() in ("1", "true", "yes")
                elif expected is int:
                    try:
                        data[name] = int(raw)
                    except ValueError:
                        raise ConfigError(f"env {env_prefix}{name.upper()} "
                                          f"must be an integer") from None
                elif expected is float:
                    try:
                        data[name] = float(raw)
                    except ValueError:
                        raise ConfigError(f"env {env_prefix}{name.upper()} "
                                          f"must be a number") from None
                else:
                    data[name] = raw

        if overrides:
            unknown = set(overrides) - set(cls.field_names())
            if unknown:
                raise ConfigError(f"unknown config keys: {sorted(unknown)}")
            data.update({k: v for k, v in overrides.items() if v is not None})

        instance = cls(**data)

        if validators:
            for name, check in validators.items():
                value = getattr(instance, name)
                try:
                    checked = check(value)
                except Exception as exc:
                    raise ConfigError(f"field '{name}' failed validation: {exc}") from exc
                if checked is False:
                    raise ConfigError(f"field '{name}' failed validation")
                if checked is not None and checked is not True:
                    setattr(instance, name, checked)
        return instance

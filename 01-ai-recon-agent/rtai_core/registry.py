"""Generic plugin registry: the extension point pattern used by every project."""

from typing import Callable, Dict, Generic, Iterable, TypeVar

T = TypeVar("T")


class RegistryError(Exception):
    pass


class Registry(Generic[T]):
    def __init__(self, name: str):
        self.name = name
        self._items: Dict[str, T] = {}
        self._meta: Dict[str, dict] = {}

    def register(self, key: str, item: T, replace: bool = False, **meta) -> T:
        key = key.lower()
        if key in self._items and not replace:
            raise RegistryError(f"{self.name}: duplicate registration '{key}'")
        self._items[key] = item
        self._meta[key] = meta
        return item

    def decorator(self, key: str, **meta) -> Callable[[T], T]:
        def wrapper(item: T) -> T:
            return self.register(key, item, **meta)
        return wrapper

    def get(self, key: str) -> T:
        try:
            return self._items[key.lower()]
        except KeyError:
            raise RegistryError(
                f"{self.name}: unknown '{key}' (have: {', '.join(sorted(self._items))})")

    def meta(self, key: str) -> dict:
        return dict(self._meta.get(key.lower(), {}))

    def keys(self) -> Iterable[str]:
        return sorted(self._items)

    def items(self):
        return sorted(self._items.items())

    def __contains__(self, key) -> bool:
        return str(key).lower() in self._items

    def __len__(self) -> int:
        return len(self._items)

"""rtai_core: shared industrial foundation for the AI red-team suite.

Every project imports this package instead of reimplementing cross-cutting
concerns. Design rules:

- Standard library only at runtime (portability, auditable supply chain).
- Typed public surface (dataclasses, enums, Protocols/ABCs).
- Deterministic behavior first; LLM reasoning sits above this core.
"""

from rtai_core.exceptions import (
    AuthError,
    ConfigError,
    ProviderError,
    RTAIError,
    StorageError,
    TargetError,
    ValidationError,
)
from rtai_core.version import __version__

__all__ = [
    "__version__",
    "RTAIError",
    "ConfigError",
    "ValidationError",
    "ProviderError",
    "TargetError",
    "StorageError",
    "AuthError",
]

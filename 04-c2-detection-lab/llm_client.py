"""Deprecated shim kept for backward compatibility with project-local imports.

New code should import from rtai_core.providers directly.
"""

from rtai_core.exceptions import ProviderError as LLMError
from rtai_core.providers import ChatClient, create_provider

__all__ = ["ChatClient", "LLMError", "create_provider"]

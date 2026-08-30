"""Provider package: protocols + factory."""

from rtai_core.providers.base import (
    ChatClient,
    ChatProvider,
    Completion,
    Message,
    parse_json_reply,
)
from rtai_core.providers.factory import create_provider
from rtai_core.providers.anthropic import AnthropicProvider
from rtai_core.providers.openai_compat import (
    OllamaProvider,
    OpenAICompatibleProvider,
)

__all__ = [
    "ChatClient", "ChatProvider", "Completion", "Message",
    "create_provider", "parse_json_reply",
    "AnthropicProvider", "OpenAICompatibleProvider", "OllamaProvider",
]

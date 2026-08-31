"""Anthropic Messages API wire protocol."""

import os
from typing import List

from rtai_core.providers.base import PROVIDER_DEFAULTS, ChatProvider, Message
from rtai_core.exceptions import ConfigError


class AnthropicProvider(ChatProvider):
    name = "anthropic"

    def __init__(self, model, api_key="", base_url="", timeout=120):
        super().__init__(model=model, api_key=api_key or
                         os.environ.get(PROVIDER_DEFAULTS[self.name]["key_env"], ""),
                         base_url=base_url, timeout=timeout)
        if not self.api_key:
            raise ConfigError("missing ANTHROPIC_API_KEY")

    def endpoint(self) -> str:
        return f"{self.base_url}/messages"

    def headers(self) -> dict:
        return {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}

    def payload(self, messages: List[Message], temperature: float,
                max_tokens: int) -> dict:
        system_chunks = [m.content for m in messages if m.role == "system"]
        user_turns = [{"role": m.role, "content": m.content}
                      for m in messages if m.role != "system"]
        payload = {"model": self.model, "max_tokens": max_tokens,
                   "temperature": temperature, "messages": user_turns}
        if system_chunks:
            payload["system"] = "\n\n".join(system_chunks)
        return payload

    def extract(self, response_json: dict) -> str:
        blocks = [block.get("text", "") for block in response_json["content"]
                  if block.get("type") == "text"]
        return "\n".join(blocks)


PROTOCOLS = {"anthropic": AnthropicProvider}

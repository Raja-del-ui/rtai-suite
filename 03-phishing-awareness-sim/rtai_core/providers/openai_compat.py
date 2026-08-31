"""OpenAI-compatible wire protocol (also serves Ollama, vLLM, LM Studio, etc.)."""

from typing import List

from rtai_core.providers.base import ChatProvider, Message


class OpenAICompatibleProvider(ChatProvider):
    name = "openai"

    def endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def headers(self) -> dict:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def payload(self, messages: List[Message], temperature: float,
                max_tokens: int) -> dict:
        wire = [{"role": m.role, "content": m.content} for m in messages]
        return {"model": self.model, "messages": wire,
                "temperature": temperature, "max_tokens": max_tokens}

    def extract(self, response_json: dict) -> str:
        choice = (response_json["choices"])[0]
        return (choice.get("message") or {}).get("content") or ""


class OllamaProvider(OpenAICompatibleProvider):
    name = "ollama"

class XAIProvider(OpenAICompatibleProvider):
    name = "xai"

class GrokProvider(OpenAICompatibleProvider):
    name = "grok"


PROTOCOLS = {
    "openai": OpenAICompatibleProvider,
    "ollama": OllamaProvider,
    "xai": XAIProvider,
    "grok": GrokProvider,
}

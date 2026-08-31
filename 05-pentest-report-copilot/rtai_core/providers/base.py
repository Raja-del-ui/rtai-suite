"""Provider abstraction: uniform chat over OpenAI-compatible and Anthropic APIs."""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from rtai_core.exceptions import ProviderError
from rtai_core.retry import RetryPolicy

RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})

PROVIDER_DEFAULTS = {
    "openai": {"model": "gpt-4o-mini", "key_env": "OPENAI_API_KEY",
               "base": "https://api.openai.com/v1"},
    "anthropic": {"model": "claude-sonnet-4-20250514", "key_env": "ANTHROPIC_API_KEY",
                  "base": "https://api.anthropic.com/v1"},
    "xai": {"model": "grok-4", "key_env": "XAI_API_KEY",
            "base": "https://api.x.ai/v1"},
    "grok": {"model": "grok-4", "key_env": "XAI_API_KEY",
             "base": "https://api.x.ai/v1"},
    "gemini": {"model": "gemini-3-flash-preview", "key_env": "GEMINI_API_KEY",
               "base": "https://generativelanguage.googleapis.com/v1beta"},
    "google": {"model": "gemini-3-flash-preview", "key_env": "GOOGLE_API_KEY",
               "base": "https://generativelanguage.googleapis.com/v1beta"},
    "ollama": {"model": "llama3.1", "key_env": "",
               "base": "http://127.0.0.1:11434/v1"},
}


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    provider: str
    prompt_chars: int
    completion_chars: int


class TransportError(ProviderError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class ChatProvider(ABC):
    """One class per wire protocol; selected by factory, wrapped by ChatClient."""

    name = "abstract"

    def __init__(self, model: str, api_key: str = "", base_url: str = "",
                 timeout: int = 120):
        self.model = model
        self.api_key = api_key
        self.base_url = (base_url or PROVIDER_DEFAULTS[self.name]["base"]).rstrip("/")
        self.timeout = timeout

    @abstractmethod
    def endpoint(self) -> str:
        ...

    @abstractmethod
    def headers(self) -> dict:
        ...

    @abstractmethod
    def payload(self, messages: List[Message], temperature: float,
                max_tokens: int) -> dict:
        ...

    @abstractmethod
    def extract(self, response_json: dict) -> str:
        ...

    def send(self, messages: List[Message], temperature: float,
             max_tokens: int) -> Completion:
        import urllib.error
        import urllib.request

        body = json.dumps(self.payload(messages, temperature, max_tokens)).encode()
        request = urllib.request.Request(self.endpoint(), data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        for key, value in self.headers().items():
            request.add_header(key, value)

        def once() -> dict:
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode(errors="replace"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode(errors="replace")[:300]
                raise TransportError(f"HTTP {exc.code} from {self.name}: {detail}",
                                     status=exc.code) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                raise TransportError(f"transport failure ({self.name}): {exc}") from exc

        policy = RetryPolicy(attempts=3, retry_on=(TransportError,))
        data = policy.run(once)
        try:
            text = self.extract(data)
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"malformed {self.name} response: {exc}") from exc
        return Completion(text=text, model=self.model, provider=self.name,
                          prompt_chars=sum(len(m.content) for m in messages),
                          completion_chars=len(text))


def parse_json_reply(text: str):
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    candidate = fenced.group(1).strip() if fenced else text.strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}|\[.*\]", candidate, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    raise ProviderError(f"could not parse JSON from model reply:\n{text[:400]}")


class ChatClient:
    """Facade used by every project. Stable API across provider swaps."""

    def __init__(self, provider=None, model=None, api_key=None, base_url=None,
                 temperature=0.4, max_tokens=2048, timeout=120):
        from rtai_core.providers.factory import create_provider

        self.temperature = temperature
        self.max_tokens = max_tokens
        self._provider: ChatProvider = create_provider(
            requested=provider, model=model, api_key=api_key,
            base_url=base_url, timeout=timeout)

    @property
    def provider(self) -> str:
        return self._provider.name

    @property
    def model(self) -> str:
        return self._provider.model

    def chat(self, user: str, system: Optional[str] = None) -> str:
        if not user:
            raise ProviderError("empty user message")
        messages = []
        if system:
            messages.append(Message("system", system))
        messages.append(Message("user", user))
        return self._provider.send(messages, self.temperature,
                                   self.max_tokens).text.strip()

    def ask_json(self, user: str, system: Optional[str] = None):
        return parse_json_reply(self.chat(user, system))

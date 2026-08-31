"""Google Gemini wire protocol — Generative Language API."""

import os
from typing import List

from rtai_core.exceptions import ConfigError
from rtai_core.providers.base import ChatProvider, Message, PROVIDER_DEFAULTS


class GeminiProvider(ChatProvider):
    name = "gemini"

    def __init__(self, model, api_key="", base_url="", timeout=120):
        # Gemini uses X-goog-api-key header, not Authorization
        super().__init__(model=model, api_key=api_key or os.environ.get(PROVIDER_DEFAULTS[self.name]["key_env"], "") or os.environ.get("GOOGLE_API_KEY",""), base_url=base_url, timeout=timeout)
        # Also accept GOOGLE_API_KEY alias
        if not self.api_key:
            self.api_key = os.environ.get("GOOGLE_API_KEY","") or os.environ.get("GEMINI_API_KEY","")
        if not self.api_key:
            raise ConfigError("missing GEMINI_API_KEY (or GOOGLE_API_KEY / XAI_API_KEY alias). Set GEMINI_API_KEY env")
        # Gemini models: gemini-flash-latest, gemini-2.0-flash, gemini-1.5-pro etc — keep as provided
        # base_url is https://generativelanguage.googleapis.com/v1beta
        if not self.base_url or "generativelanguage" not in self.base_url:
            # Use default if not overridden
            self.base_url = PROVIDER_DEFAULTS[self.name]["base"]

    def endpoint(self) -> str:
        # Gemini endpoint is /models/{model}:generateContent
        base = self.base_url.rstrip("/")
        # Avoid double /v1beta if base already has it
        if base.endswith("/v1beta"):
            return f"{base}/models/{self.model}:generateContent"
        if "generativelanguage" in base:
            return f"{base}/models/{self.model}:generateContent"
        return f"{base}/models/{self.model}:generateContent"

    def headers(self) -> dict:
        return {"Content-Type": "application/json", "X-goog-api-key": self.api_key}

    def payload(self, messages: List[Message], temperature: float, max_tokens: int) -> dict:
        # Gemini wants contents: [{parts: [{text: ...}]}] with role user/model
        # Map system -> user prefix, and chat history
        contents = []
        system_texts = [m.content for m in messages if m.role == "system"]
        system_prefix = "\n\n".join(system_texts) + "\n\n" if system_texts else ""
        for m in messages:
            if m.role == "system":
                continue
            # Gemini roles: user -> user, assistant -> model
            role = "user" if m.role == "user" else "model"
            text = m.content
            if system_prefix and role == "user" and not contents:
                text = system_prefix + text
            # Gemini parts must be list
            contents.append({"role": role, "parts": [{"text": text}]})
        # If only system was present (edge), add as user
        if not contents and system_prefix:
            contents.append({"role": "user", "parts": [{"text": system_prefix.strip()}]})
        return {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

    def extract(self, response_json: dict) -> str:
        # Gemini response: {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
        try:
            cands = response_json.get("candidates", [])
            if not cands:
                # Check for promptFeedback block
                if "promptFeedback" in response_json:
                    return f"[blocked: {response_json['promptFeedback']}]"
                return ""
            parts = cands[0].get("content", {}).get("parts", [])
            texts = [p.get("text","") for p in parts if isinstance(p, dict)]
            return "\n".join(texts).strip()
        except (KeyError, IndexError, TypeError) as e:
            raise ConfigError(f"malformed gemini response: {e}: {str(response_json)[:400]}")


class GoogleProvider(GeminiProvider):
    name = "google"


PROTOCOLS = {
    "gemini": GeminiProvider,
    "google": GoogleProvider,
}

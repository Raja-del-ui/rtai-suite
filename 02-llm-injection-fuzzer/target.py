"""Client for the application under test: any OpenAI-compatible chat endpoint."""

import json
import urllib.error
import urllib.request


class TargetError(RuntimeError):
    pass


class TargetClient:
    def __init__(self, base_url, model, api_key="", system_prompt="", temperature=0.7, timeout=60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.timeout = timeout

    def send(self, user_text):
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": user_text})
        payload = {"model": self.model, "messages": messages, "temperature": self.temperature}
        req = urllib.request.Request(f"{self.base_url}/chat/completions",
                                     data=json.dumps(payload).encode(), method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode(errors="replace"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            raise TargetError(f"target returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise TargetError(f"cannot reach target at {self.base_url}: {exc}") from exc
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise TargetError(f"unexpected response shape: {json.dumps(data)[:300]}") from exc

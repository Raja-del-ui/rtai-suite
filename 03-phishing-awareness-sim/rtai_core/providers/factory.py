"""Provider factory: explicit > env > autodetect (keys present, else local Ollama)."""

import os

from rtai_core.exceptions import ProviderError
from rtai_core.providers.anthropic import AnthropicProvider
from rtai_core.providers.base import PROVIDER_DEFAULTS
from rtai_core.providers.openai_compat import PROTOCOLS as OPENAI_LIKE

try:
    from rtai_core.providers.gemini import PROTOCOLS as GEMINI_LIKE
except ImportError:
    GEMINI_LIKE = {}


def create_provider(requested=None, model=None, api_key=None, base_url=None,
                    timeout=120):
    chosen = (requested or os.environ.get("LLM_PROVIDER") or "").lower() or None
    if chosen is None:
        if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
            chosen = "gemini"
        elif os.environ.get("OPENAI_API_KEY"):
            chosen = "openai"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            chosen = "anthropic"
        elif os.environ.get("XAI_API_KEY"):
            chosen = "xai"
        else:
            chosen = "ollama"
    if chosen not in PROVIDER_DEFAULTS:
        raise ProviderError(
            f"unknown provider '{chosen}' (expected openai|anthropic|xai|grok|gemini|google|ollama)")

    defaults = PROVIDER_DEFAULTS[chosen]
    resolved_model = model or os.environ.get("LLM_MODEL") or defaults["model"]
    resolved_base = base_url or os.environ.get("LLM_BASE_URL") or defaults["base"]
    env_key = os.environ.get(defaults["key_env"], "") if defaults["key_env"] else ""
    resolved_key = api_key or env_key

    if chosen in OPENAI_LIKE:
        provider_class = OPENAI_LIKE[chosen]
        if defaults["key_env"] and not resolved_key:
            raise ProviderError(f"missing API key: set {defaults['key_env']}")
        return provider_class(model=resolved_model, api_key=resolved_key,
                              base_url=resolved_base, timeout=timeout)
    if chosen in GEMINI_LIKE:
        provider_class = GEMINI_LIKE[chosen]
        if defaults["key_env"] and not resolved_key:
            # also check GOOGLE_API_KEY alias
            alt = os.environ.get("GOOGLE_API_KEY","") or os.environ.get("GEMINI_API_KEY","")
            if not alt and not resolved_key:
                raise ProviderError(f"missing API key: set {defaults['key_env']} (or GOOGLE_API_KEY)")
            resolved_key = resolved_key or alt
        return provider_class(model=resolved_model, api_key=resolved_key,
                              base_url=resolved_base, timeout=timeout)
    return AnthropicProvider(model=resolved_model, api_key=resolved_key,
                             base_url=resolved_base, timeout=timeout)

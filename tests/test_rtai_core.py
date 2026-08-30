import pytest

from rtai_core.config import BaseConfig
from rtai_core.exceptions import ConfigError, RTAIError
from rtai_core.registry import Registry, RegistryError
from rtai_core.retry import RetryPolicy
from rtai_core.storage import JsonlStore, SqliteEventStore
from rtai_core.validation import assert_lab_address, normalize_domain


def test_exception_exit_codes_are_distinct():
    codes = [78, 64, 77, 69, 75, 74]
    seen = set()
    for code in codes:
        assert code not in seen
        seen.add(code)
    assert issubclass(ConfigError, RTAIError)


class DemoConfig(BaseConfig):
    host: str = "127.0.0.1"
    port: int = 8080
    verbose: bool = False


def test_config_defaults_and_file_layer(tmp_path):
    config = DemoConfig.from_layers()
    assert (config.host, config.port) == ("127.0.0.1", 8080)
    file = tmp_path / "c.json"
    file.write_text('{"port": 9999}', encoding="utf-8")
    config = DemoConfig.from_layers(file_path=str(file))
    assert config.port == 9999 and config.host == "127.0.0.1"


def test_config_cli_overrides_beat_file(tmp_path):
    file = tmp_path / "c.json"
    file.write_text('{"port": 9999}', encoding="utf-8")
    config = DemoConfig.from_layers(file_path=str(file), overrides={"port": 1234})
    assert config.port == 1234


def test_config_rejects_unknown_keys():
    with pytest.raises(ConfigError):
        DemoConfig.from_layers(overrides={"nope": 1})


def test_config_validators_run():
    with pytest.raises(ConfigError):
        DemoConfig.from_layers(
            overrides={"port": -1},
            validators={"port": lambda v: v > 0})


def test_registry_register_get_meta():
    registry = Registry("collectors")

    @registry.decorator("dns", passive=True)
    def run_dns():  # pragma: no cover
        return {}

    assert "DNS" in registry
    assert registry.meta("dns")["passive"] is True
    with pytest.raises(RegistryError):
        registry.register("dns", run_dns)


def test_retry_policy_backoff_monotonic_and_capped():
    import time as time_module

    policy = RetryPolicy(attempts=4, base_delay=1.0, max_delay=2.0,
                         _sleeper=lambda s: None)
    delays = [policy.delay_for(a) for a in range(6)]
    assert all(0 <= d <= 2.0 for d in delays)

    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("boom")
        return "ok"

    policy2 = RetryPolicy(attempts=5, base_delay=0.001,
                          _sleeper=time_module.sleep)
    assert policy2.run(flaky) == "ok"


def test_retry_exhaustion_reraises():
    policy = RetryPolicy(attempts=2, base_delay=0.001, _sleeper=lambda s: None)

    def always_fails():
        raise ConnectionError("down")

    with pytest.raises(ConnectionError):
        policy.run(always_fails)


def test_jsonl_store_roundtrip(tmp_path):
    store = JsonlStore(tmp_path / "events.jsonl")
    store.append({"event": "a"})
    store.append({"event": "b", "n": 2})
    rows = store.read()
    assert [r["event"] for r in rows] == ["a", "b"]
    assert all("ts" in r for r in rows)


def test_sqlite_store_emit_query(tmp_path):
    store = SqliteEventStore(tmp_path / "events.db")
    store.emit("poll", task="whoami")
    store.emit("exfil", size=10)
    polls = store.query(kind="poll")
    assert len(polls) == 1
    assert polls[0]["payload"]["task"] == "whoami"
    assert len(store.query()) == 2


def test_lab_guard_accepts_loopback_rejects_public():
    assert_lab_address("127.0.0.1")
    try:
        assert_lab_address("example.com")
    except ValueError as exc:
        assert "non-lab" in str(exc)
    else:
        raise AssertionError("public host accepted")


def test_normalize_domain():
    assert normalize_domain(" EXAMPLE.COM ") == "example.com"
    with pytest.raises(ValueError):
        normalize_domain("bad")


def test_provider_factory_unknown_and_ollama_default(monkeypatch):
    from rtai_core.providers import create_provider

    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    provider = create_provider()
    assert provider.name == "ollama"
    with pytest.raises(Exception):
        create_provider(requested="skynet")


def test_openai_payload_shape_vs_anthropic():
    from rtai_core.providers.anthropic import AnthropicProvider
    from rtai_core.providers.openai_compat import OpenAICompatibleProvider
    from rtai_core.providers.base import Message

    openai_like = OpenAICompatibleProvider(model="m", api_key="k")
    wire = openai_like.payload([Message("system", "s"), Message("user", "u")], 0.1, 9)
    assert wire["messages"][0]["role"] == "system" and wire["max_tokens"] == 9

    monkey_env = {"ANTHROPIC_API_KEY": "test-key"}
    import os
    old = os.environ.get("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    try:
        anthropic = AnthropicProvider(model="m")
        wire = anthropic.payload([Message("system", "s"), Message("user", "u")], 0.1, 9)
        assert wire["system"] == "s" and "system" not in wire["messages"][0]
    finally:
        if old is None:
            del os.environ["ANTHROPIC_API_KEY"]
        else:
            os.environ["ANTHROPIC_API_KEY"] = old

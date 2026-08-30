import json
import threading
import urllib.request

import pytest

from rtai_core.cli_app import find_repo_root, main as cli_main
from rtai_core.metrics import REGISTRY
from rtai_core.version import __version__


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, json.loads(resp.read().decode())


@pytest.fixture(scope="module")
def api_base_url():
    from services.api.server import create_server

    server = create_server(host="127.0.0.1", port=0,
                           recon_runner=lambda target, http: {
                               "target": target, "stub": True})
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


def test_health_and_version(api_base_url):
    status, health = _get(f"{api_base_url}/health")
    assert (status, health["status"]) == (200, "ok")
    _, version = _get(f"{api_base_url}/version")
    assert version["version"] == __version__
    assert "recon" in version["tools"]


def test_metrics_endpoint_prometheus_format(api_base_url):
    import urllib.request
    with urllib.request.urlopen(f"{api_base_url}/metrics", timeout=5) as resp:
        body = resp.read().decode()
        assert resp.headers["Content-Type"].startswith("text/plain")
    assert "rtai_http_requests_total_code_" in body


def test_recon_stub_and_validation(api_base_url):
    request = urllib.request.Request(
        f"{api_base_url}/v1/recon",
        data=json.dumps({"target": "lab.local"}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    assert data == {"target": "lab.local", "stub": True}

    bad = urllib.request.Request(
        f"{api_base_url}/v1/recon", data=b"not json",
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(bad, timeout=5)
        raise AssertionError("malformed body should 400")
    except urllib.error.HTTPError as exc:
        assert exc.code == 400


def test_rate_limiter_window():
    from services.api.server import SlidingWindowLimiter

    limiter = SlidingWindowLimiter(limit_per_minute=3)
    assert [limiter.allow("ip") for _ in range(5)] == [True, True, True, False, False]
    assert limiter.allow("other-ip") is True


def test_metrics_registry_counts():
    before = REGISTRY.get("test_counter_x")
    REGISTRY.inc("test_counter_x", help_text="unit test counter")
    REGISTRY.inc("test_counter_x")
    assert REGISTRY.get("test_counter_x") == before + 2
    text = REGISTRY.render_prometheus()
    assert "# HELP test_counter_x unit test counter" in text


def test_cli_dispatcher_lists_tools(capsys):
    assert cli_main(["--list"]) == 0
    out = capsys.readouterr().out
    assert {"recon", "fuzz", "c2-listen", "report"} <= set(out.split())


def test_cli_dispatcher_rejects_unknown():
    assert cli_main(["nope"]) == 2


def test_cli_dispatcher_runs_real_tool_offline(capsys):
    code = cli_main(["fuzz", "--list-payloads"])
    assert code == 0
    assert "AO-01" in capsys.readouterr().out


def test_cli_error_funnel_maps_validation_exit_code():
    code = cli_main(["recon", "--target", "bad_domain"])
    assert code == 64


def test_cli_sysexit_string_becomes_internal_error():
    import sys

    from rtai_core import cli_app

    original = cli_app.runpy.run_path

    def fake_run(_path, run_name=None):
        raise SystemExit("some legacy failure message")

    cli_app.runpy.run_path = fake_run
    try:
        code = cli_app.dispatch("report", [])
    finally:
        cli_app.runpy.run_path = original
        _ = sys  # keep reference for clarity
    assert code == 70


def test_cli_help_of_real_tool_exits_cleanly():
    code = cli_main(["c2-beacon", "--help"])
    assert code == 0


def test_find_repo_root_locates_checkout():
    root = find_repo_root(__import__("pathlib").Path(__file__).resolve())
    assert (root / "rtai_core").is_dir()

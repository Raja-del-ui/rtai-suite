import json
import threading
import time
import urllib.request

import pytest

from services.api.server import JobManager, create_server


@pytest.fixture(scope="module")
def api():
    server = create_server(host="127.0.0.1", port=0,
                           recon_runner=lambda target, http: {
                               "target": target, "stub": True})
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


def _request(url, method="GET", body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read()


def test_security_headers_on_every_response(api):
    status, headers, _ = _request(f"{api}/health")
    assert status == 200
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Cache-Control"] == "no-store"


def test_openapi_contract_served(api):
    status, _, body = _request(f"{api}/openapi.json")
    spec = json.loads(body)
    assert status == 200 and spec["openapi"].startswith("3.")
    assert "/v1/jobs/{id}" in spec["paths"]
    assert "/v1/recon/async" in spec["paths"]


def test_async_job_lifecycle(api):
    status, _, body = _request(f"{api}/v1/recon/async", method="POST",
                               body={"target": "jobbed.local"})
    assert status == 202
    job_id = json.loads(body)["job_id"]

    deadline = time.time() + 10
    while time.time() < deadline:
        _, _, raw = _request(f"{api}/v1/jobs/{job_id}")
        view = json.loads(raw)
        if view["status"] in ("done", "error"):
            break
        time.sleep(0.05)
    assert view["status"] == "done"
    assert view["result"] == {"target": "jobbed.local", "stub": True}

    _, _, listing = _request(f"{api}/v1/jobs")
    ids = [j["id"] for j in json.loads(listing)["jobs"]]
    assert job_id in ids


def test_unknown_job_404_and_auth_failures_audited(tmp_path, monkeypatch):
    import services.api.server as api_module

    captured = []
    monkeypatch.setattr(api_module, "audit_record",
                        lambda event, actor="", **kw: captured.append(
                            {"event": event, "actor": actor, **kw}))
    server = create_server(host="127.0.0.1", port=0, token="sekret")
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        status, _, _ = _request(f"http://127.0.0.1:{port}/v1/jobs/nope",
                                headers={"Authorization": "Bearer wrong"})
        assert status == 401
        assert any(entry["event"] == "auth_failure" for entry in captured)
        assert any(entry["actor"].startswith("127.0.0.1") for entry in captured)

        status, _, _ = _request(f"http://127.0.0.1:{port}/v1/jobs/nope",
                                headers={"Authorization": "Bearer sekret"})
        assert status == 404
    finally:
        server.shutdown()
        server.server_close()


def test_jobmanager_direct_states():
    manager = JobManager(workers=1)
    job_id = manager.submit("unit", lambda: 41 + 1)
    deadline = time.time() + 5
    while time.time() < deadline:
        job = manager.get(job_id)
        if job.status == "done":
            break
        time.sleep(0.02)
    view = JobManager.public_view(manager.get(job_id))
    assert view["result"] == 42

    failing = manager.submit("unit", lambda: 1 / 0)
    deadline = time.time() + 5
    while time.time() < deadline:
        job = manager.get(failing)
        if job.status == "error":
            break
        time.sleep(0.02)
    assert "division by zero" in JobManager.public_view(
        manager.get(failing))["error"]

import json

import pytest

from rtai_core.audit import AuditChain, GENESIS


def test_chain_records_and_verifies(tmp_path):
    chain = AuditChain(tmp_path / "audit.log")
    chain.record("authorization", actor="alice", tool="fuzzer", target="local")
    chain.record("authorization", actor="bob", tool="phish", target="lab")
    ok, broken = chain.verify()
    assert ok and broken is None


def test_tampering_is_detected_at_exact_line(tmp_path):
    path = tmp_path / "audit.log"
    chain = AuditChain(path)
    chain.record("e1")
    chain.record("e2")
    chain.record("e3")

    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[1]["actor"] = "mallory"                      # mutate middle record
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    ok, broken = AuditChain(path).verify()
    assert not ok
    assert broken == 2


def test_deletion_breaks_chain(tmp_path):
    path = tmp_path / "audit.log"
    chain = AuditChain(path)
    chain.record("a")
    chain.record("b")
    chain.record("c")
    rows = path.read_text().splitlines()
    del rows[0]
    path.write_text("\n".join(rows) + "\n")
    ok, broken = AuditChain(path).verify()
    assert not ok and broken == 1


def test_genesis_hash_shape():
    assert len(GENESIS) == 64


def test_default_chain_singleton():
    from rtai_core import audit as audit_module

    assert audit_module.default_chain() is audit_module.default_chain()


@pytest.mark.parametrize("event", ["auth_failure", "authorization", "job_submit"])
def test_event_payload_roundtrip(tmp_path, event):
    chain = AuditChain(tmp_path / "a.log")
    entry = chain.record(event, actor="t", target="x", extra={"k": 1})
    rows = chain.read()
    assert rows[-1]["event"] == event and entry["hash"]

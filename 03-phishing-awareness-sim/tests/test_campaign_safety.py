import pytest

import auth
from generator import campaign_manifest, links_csv, validate_draft
from templates import TEMPLATES


def _base_config():
    return {
        "company": "Acme",
        "attested_by": "Sec Lead",
        "sender_domain": "acme-secure.example",
        "recipients": ["alice@corp.example"],
    }


def test_valid_config_passes():
    assert auth.validate_campaign(_base_config())


def test_missing_attestation_rejected():
    config = _base_config()
    del config["attested_by"]
    with pytest.raises(ValueError):
        auth.validate_campaign(config)


def test_bad_recipient_email_rejected():
    config = _base_config()
    config["recipients"] = ["not-an-email"]
    with pytest.raises(ValueError):
        auth.validate_campaign(config)


def test_smtp_without_allow_send_rejected():
    config = _base_config()
    config["smtp"] = {"host": "smtp.local"}
    with pytest.raises(ValueError):
        auth.validate_campaign(config)


def test_recipient_cap_enforced():
    config = _base_config()
    config["recipients"] = [f"u{i}@corp.example" for i in range(60)]
    with pytest.raises(ValueError):
        auth.validate_campaign(config)


def test_draft_blocklist():
    with pytest.raises(ValueError):
        validate_draft({"subject": "hi", "body": "run <script>alert(1)</script>"})
    assert validate_draft({"subject": "Reset", "body": "Please click https://ok.example"})


def test_every_template_has_red_flags_and_link_label():
    for key, template in TEMPLATES.items():
        assert template["red_flags"], key
        assert template["link_label"], key


def test_csv_shapes():
    manifest = campaign_manifest([{"file": "a.eml", "recipient": "r@x",
                                   "template": "t", "subject": "s"}])
    links = links_csv([{"token": "tok", "recipient": "r@x", "template": "t",
                        "file": "a.eml"}])
    assert manifest.splitlines()[0] == "file,recipient,template,subject"
    assert links.splitlines()[0] == "token,recipient,template,file"

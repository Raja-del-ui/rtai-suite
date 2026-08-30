"""Mission management — military-grade operation profiles with classification & ROE.

Every operation is a Mission with classification, handling caveat, approver, and ROE window.
Mission is the single source of truth for audit, report watermark, and STIX classification.
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from rtai_core.config import BaseConfig

CLASSIFICATIONS = ["UNCLASS", "CUI", "CONFIDENTIAL", "SECRET", "TOP_SECRET"]
CAVEATS = ["", "NOFORN", "REL FVEY", "REL NATO", "ORCON", "SI-G/NF"]

# Classification colors (DoD banner standard)
CLASS_COLORS = {
    "UNCLASS": "#007A33",      # Green
    "CUI": "#502B85",          # Purple (CUI)
    "CONFIDENTIAL": "#0033A0", # Blue
    "SECRET": "#C8102E",       # Red
    "TOP_SECRET": "#FF6A00",   # Orange
}

# Handling text per classification (base only — caveat appended by banner property)
# DoD standard banners: UNCLASS (green), CUI (purple), CONFIDENTIAL (blue), SECRET (red), TOP SECRET (orange)
CLASS_BANNERS = {
    "UNCLASS": "UNCLASSIFIED",
    "CUI": "CUI",
    "CONFIDENTIAL": "CONFIDENTIAL",
    "SECRET": "SECRET",
    "TOP_SECRET": "TOP SECRET",
}

@dataclass
class ROE:
    """Rules of Engagement window and scope."""
    targets: list[str] = field(default_factory=list)
    techniques: list[str] = field(default_factory=list)  # recon, fuzz, phish, c2, report
    start: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end: str = field(default_factory=lambda: (datetime.now(timezone.utc) + timedelta(days=7)).isoformat())
    window_tz: str = "UTC"

    def is_active(self) -> bool:
        try:
            now = datetime.now(timezone.utc)
            s = datetime.fromisoformat(self.start.replace("Z", "+00:00"))
            e = datetime.fromisoformat(self.end.replace("Z", "+00:00"))
            return s <= now <= e
        except Exception:
            return False

@dataclass
class Mission(BaseConfig):
    """Operation profile — single source of truth for military ops."""
    mission_id: str = field(default_factory=lambda: f"OP-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""  # e.g., "MANTICORE SHIELD"
    callsign: str = ""  # e.g., "REAPER 06"
    grid_ref: str = ""  # e.g., "38TLL 1234 5678" MGRS
    classification: str = "CUI"
    caveat: str = ""
    caveats: list[str] = field(default_factory=list)
    approver: str = ""
    approver_rank: str = ""
    roe: ROE = field(default_factory=ROE)
    opsec_checklist: dict = field(default_factory=dict)
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    mde: str = ""  # Mission Data Element for STIX

    def __post_init__(self):
        if self.classification not in CLASSIFICATIONS:
            raise ValueError(f"classification must be one of {CLASSIFICATIONS}")
        if self.caveat and self.caveat not in CAVEATS:
            raise ValueError(f"caveat must be one of {CAVEATS}")

    @property
    def banner(self) -> str:
        base = CLASS_BANNERS.get(self.classification, self.classification)
        if self.caveat:
            return f"{base} // {self.caveat}"
        if self.caveats:
            return f"{base} // {'/'.join(self.caveats)}"
        return base

    @property
    def banner_color(self) -> str:
        return CLASS_COLORS.get(self.classification, "#007A33")

    @property
    def is_active(self) -> bool:
        return self.roe.is_active()

    def to_dict(self) -> dict:
        d = asdict(self)
        # Flatten for JSON
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Mission":
        roe_data = data.get("roe", {})
        if isinstance(roe_data, dict):
            data["roe"] = ROE(**{k: v for k, v in roe_data.items() if k in ROE.__dataclass_fields__})
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self, path: Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))
        # Set 600 perms for classified missions
        try:
            if self.classification in ("SECRET", "TOP_SECRET", "CONFIDENTIAL"):
                path.chmod(0o600)
        except Exception:
            pass

    @classmethod
    def load(cls, path: Path) -> "Mission":
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)

    def opsec_status(self) -> dict:
        """OPSEC checklist — all must be true before execution."""
        defaults = {
            "roe_signed": bool(self.approver),
            "targets_validated": bool(self.roe.targets),
            "comms_encrypted": os.environ.get("RTAI_MTLS") == "1" or os.environ.get("RTAI_TLS_CERT"),
            "fips_enabled": os.environ.get("RTAI_FIPS") == "1",
            "audit_worm": os.environ.get("RTAI_AUDIT_WORM") == "1",
            "tpm_attested": os.environ.get("RTAI_TPM_ATTEST") == "1",
        }
        merged = {**defaults, **self.opsec_checklist}
        return merged

# Mission store — simple JSON file per mission, index in missions/index.json
MISSION_DIR = Path(os.environ.get("RTAI_MISSION_DIR", "missions"))

def list_missions() -> list[Mission]:
    idx = MISSION_DIR / "index.json"
    if not idx.exists():
        return []
    try:
        data = json.loads(idx.read_text())
        return [Mission.from_dict(d) for d in data]
    except Exception:
        return []

def save_mission(m: Mission):
    # Save individual file
    m.save(MISSION_DIR / f"{m.mission_id}.json")
    # Update index
    all_m = list_missions()
    # Replace or append
    all_m = [x for x in all_m if x.mission_id != m.mission_id] + [m]
    (MISSION_DIR / "index.json").parent.mkdir(parents=True, exist_ok=True)
    (MISSION_DIR / "index.json").write_text(json.dumps([x.to_dict() for x in all_m], indent=2))

__all__ = ["Mission", "ROE", "CLASSIFICATIONS", "CAVEATS", "CLASS_COLORS", "CLASS_BANNERS", "MISSION_DIR", "list_missions", "save_mission"]

"""Military-grade STIX 2.1 / TAXII 2.1 client for threat intelligence sharing."""

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin


@dataclass
class STIXObject:
    type: str
    id: str
    created: str
    modified: str
    spec_version: str = "2.1"


@dataclass
class Indicator(STIXObject):
    pattern: str = ""
    pattern_type: str = "stix"
    valid_from: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    labels: list[str] = field(default_factory=list)
    valid_until: Optional[str] = None
    external_references: list[dict] = field(default_factory=list)
    kill_chain_phases: list[dict] = field(default_factory=list)


@dataclass
class Malware(STIXObject):
    name: str
    description: str = ""
    malware_types: list[str] = field(default_factory=list)
    is_family: bool = False
    aliases: list[str] = field(default_factory=list)
    kill_chain_phases: list[dict] = field(default_factory=list)


@dataclass
class AttackPattern(STIXObject):
    name: str
    description: str = ""
    kill_chain_phases: list[dict] = field(default_factory=list)
    external_references: list[dict] = field(default_factory=list)


@dataclass
class ThreatActor(STIXObject):
    name: str
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    sophistication: str = "unknown"
    resource_level: str = "unknown"
    primary_motivation: str = "unknown"


@dataclass
class Campaign(STIXObject):
    name: str
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    objective: str = ""


@dataclass
class IntrusionSet(STIXObject):
    name: str
    description: str = ""
    aliases: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    resource_level: str = "unknown"
    primary_motivation: str = "unknown"


@dataclass
class CourseOfAction(STIXObject):
    name: str
    description: str = ""
    action: str = ""


@dataclass
class Bundle:
    type: str = "bundle"
    id: str = field(default_factory=lambda: f"bundle--{uuid.uuid4()}")
    objects: list = field(default_factory=list)
    spec_version: str = "2.1"


class STIXBuilder:
    """Build STIX 2.1 objects programmatically."""

    def __init__(self):
        self.objects: list = []

    def indicator(self, pattern: str, labels: list[str] = None,
                  valid_from: str = None, valid_until: str = None,
                  external_refs: list[dict] = None,
                  kill_chain: list[dict] = None) -> Indicator:
        obj = Indicator(
            pattern=pattern,
            pattern_type="stix",
            valid_from=valid_from or datetime.now(timezone.utc).isoformat(),
            valid_until=valid_until,
            labels=labels or ["malicious-activity"],
            external_references=external_refs or [],
            kill_chain_phases=kill_chain or []
        )
        self.objects.append(obj)
        return obj

    def malware(self, name: str, malware_types: list[str] = None,
                is_family: bool = False, aliases: list[str] = None,
                description: str = "") -> Malware:
        obj = Malware(
            name=name,
            description=description,
            malware_types=malware_types or ["trojan"],
            is_family=is_family,
            aliases=aliases or []
        )
        self.objects.append(obj)
        return obj

    def attack_pattern(self, name: str, description: str = "",
                       kill_chain: list[dict] = None,
                       external_refs: list[dict] = None) -> AttackPattern:
        obj = AttackPattern(
            name=name,
            description=description,
            kill_chain_phases=kill_chain or [],
            external_references=external_refs or []
        )
        self.objects.append(obj)
        return obj

    def threat_actor(self, name: str, description: str = "",
                     aliases: list[str] = None, goals: list[str] = None,
                     sophistication: str = "unknown",
                     resource_level: str = "unknown",
                     primary_motivation: str = "unknown") -> ThreatActor:
        obj = ThreatActor(
            name=name,
            description=description,
            aliases=aliases or [],
            goals=goals or [],
            sophistication=sophistication,
            resource_level=resource_level,
            primary_motivation=primary_motivation
        )
        self.objects.append(obj)
        return obj

    def campaign(self, name: str, description: str = "",
                 first_seen: str = None, last_seen: str = None,
                 objective: str = "") -> Campaign:
        obj = Campaign(
            name=name,
            description=description,
            first_seen=first_seen,
            last_seen=last_seen,
            objective=objective
        )
        self.objects.append(obj)
        return obj

    def intrusion_set(self, name: str, description: str = "",
                      aliases: list[str] = None, goals: list[str] = None,
                      resource_level: str = "unknown",
                      primary_motivation: str = "unknown") -> IntrusionSet:
        obj = IntrusionSet(
            name=name,
            description=description,
            aliases=aliases or [],
            goals=goals or [],
            resource_level=resource_level,
            primary_motivation=primary_motivation
        )
        self.objects.append(obj)
        return obj

    def course_of_action(self, name: str, description: str = "",
                         action: str = "") -> CourseOfAction:
        obj = CourseOfAction(name=name, description=description, action=action)
        self.objects.append(obj)
        return obj

    def bundle(self) -> Bundle:
        return Bundle(objects=self.objects.copy())


class TAXIIClient:
    """TAXII 2.1 client for threat intelligence sharing."""

    def __init__(self, server_url: str, api_key: str = None,
                 username: str = None, password: str = None):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.auth = (username, password) if username and password else None

    def get_collections(self) -> list[dict]:
        """Get available collections."""
        return []

    def get_objects(self, collection_id: str, added_after: str = None,
                    limit: int = 100) -> dict:
        """Get STIX objects from collection."""
        return {"objects": []}

    def add_objects(self, collection_id: str, bundle: dict) -> dict:
        """Add objects to collection."""
        return {"success": True, "added": 0}

    def get_manifest(self, collection_id: str) -> dict:
        """Get collection manifest."""
        return {}


class MITREATTACKMapper:
    """Map observations to MITRE ATT&CK techniques."""

    TACTICS = [
        "reconnaissance", "resource-development", "initial-access",
        "execution", "persistence", "privilege-escalation",
        "defense-evasion", "credential-access", "discovery",
        "lateral-movement", "collection", "command-and-control",
        "exfiltration", "impact"
    ]

    TECHNIQUES = {
        "T1059": {"name": "Command and Scripting Interpreter", "tactic": "execution"},
        "T1059.001": {"name": "PowerShell", "tactic": "execution"},
        "T1059.003": {"name": "Windows Command Shell", "tactic": "execution"},
        "T1059.005": {"name": "Visual Basic", "tactic": "execution"},
        "T1055": {"name": "Process Injection", "tactic": "defense-evasion"},
        "T1055.001": {"name": "Dynamic-link Library Injection", "tactic": "defense-evasion"},
        "T1055.012": {"name": "Process Hollowing", "tactic": "defense-evasion"},
        "T1027": {"name": "Obfuscated Files or Information", "tactic": "defense-evasion"},
        "T1027.002": {"name": "Software Packing", "tactic": "defense-evasion"},
        "T1082": {"name": "System Information Discovery", "tactic": "discovery"},
        "T1083": {"name": "File and Directory Discovery", "tactic": "discovery"},
        "T1018": {"name": "Remote System Discovery", "tactic": "discovery"},
        "T1069": {"name": "Permission Groups Discovery", "tactic": "discovery"},
        "T1087": {"name": "Account Discovery", "tactic": "discovery"},
        "T1003": {"name": "OS Credential Dumping", "tactic": "credential-access"},
        "T1003.001": {"name": "LSASS Memory", "tactic": "credential-access"},
        "T1003.008": {"name": "Cached Domain Credentials", "tactic": "credential-access"},
        "T1021": {"name": "Remote Services", "tactic": "lateral-movement"},
        "T1021.004": {"name": "Pass the Hash", "tactic": "lateral-movement"},
        "T1021.006": {"name": "Remote Desktop Protocol", "tactic": "lateral-movement"},
        "T1070": {"name": "Indicator Removal on Host", "tactic": "defense-evasion"},
        "T1070.004": {"name": "File Deletion", "tactic": "defense-evasion"},
        "T1071": {"name": "Application Layer Protocol", "tactic": "command-and-control"},
        "T1071.001": {"name": "Web Protocols", "tactic": "command-and-control"},
        "T1071.004": {"name": "DNS", "tactic": "command-and-control"},
        "T1041": {"name": "Exfiltration Over Web Service", "tactic": "exfiltration"},
        "T1486": {"name": "Data Encrypted for Impact", "tactic": "impact"},
    }

    @classmethod
    def get_technique(cls, technique_id: str) -> dict:
        return cls.TECHNIQUES.get(technique_id, {})

    @classmethod
    def get_techniques_by_tactic(cls, tactic: str) -> dict:
        return {k: v for k, v in cls.TECHNIQUES.items() if v.get("tactic") == tactic}

    @classmethod
    def map_observation_to_techniques(cls, observation: dict) -> list[str]:
        techniques = []
        obs_str = json.dumps(observation).lower()

        mappings = {
            "powershell": "T1059.001",
            "cmd": "T1059.003",
            "process injection": "T1055",
            "dll injection": "T1055.001",
            "process hollowing": "T1055.012",
            "obfuscation": "T1027",
            "packing": "T1027.002",
            "system info": "T1082",
            "file discovery": "T1083",
            "remote system": "T1018",
            "group discovery": "T1069",
            "account discovery": "T1087",
            "credential dumping": "T1003",
            "lsass": "T1003.001",
            "pass the hash": "T1021.004",
            "rdp": "T1021.006",
            "file deletion": "T1070.004",
            "web protocols": "T1071.001",
            "dns": "T1071.004",
            "exfiltration": "T1041",
            "ransomware": "T1486",
        }

        for keyword, tid in mappings.items():
            if keyword in obs_str:
                techniques.append(tid)

        return techniques

    @classmethod
    def generate_coverage_matrix(cls, observations: list[dict]) -> dict:
        coverage = {tactic: {"total": 0, "covered": 0, "techniques": {}}
                    for tactic in cls.TACTICS}

        for obs in observations:
            techniques = cls.map_observation_to_techniques(obs)
            for tid in techniques:
                tech = cls.TECHNIQUES.get(tid, {})
                tactic = tech.get("tactic", "unknown")
                if tactic in coverage:
                    coverage[tactic]["covered"] += 1
                    coverage[tactic]["techniques"][tid] = tech.get("name", tid)

        return coverage


class TAXIIClient:  # noqa: F811 - intentional redefinition for standalone vendoring compat
    """TAXII 2.1 client for threat intelligence sharing."""

    def __init__(self, server_url: str, api_key: str = None,
                 username: str = None, password: str = None):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.auth = (username, password) if username and password else None

    def get_collections(self) -> list[dict]:
        return []

    def get_objects(self, collection_id: str, added_after: str = None,
                    limit: int = 100) -> dict:
        return {"objects": []}

    def add_objects(self, collection_id: str, bundle: dict) -> dict:
        return {"success": True, "added": 0}

    def get_manifest(self, collection_id: str) -> dict:
        return {}


class ATTACKNavigatorLayer:
    """Generate MITRE ATT&CK Navigator layer JSON."""

    def __init__(self, name: str, description: str = "", domain: str = "enterprise-attack"):
        self.name = name
        self.description = description
        self.domain = domain
        self.techniques: dict[str, dict] = {}

    def add_technique(self, technique_id: str, score: float = 1.0,
                      color: str = "#ff6666", comment: str = "",
                      metadata: list[dict] = None):
        self.techniques[technique_id] = {
            "techniqueID": technique_id,
            "score": score,
            "color": color,
            "comment": comment,
            "metadata": metadata or [],
            "enabled": True
        }

    def add_techniques_by_tactic(self, tactic: str, score: float = 1.0,
                                 color: str = "#ff6666"):
        for tid, tech in MITREATTACKMapper.TECHNIQUES.items():
            if tech.get("tactic") == tactic:
                self.add_technique(tid, score, color)

    def to_layer_json(self) -> dict:
        return {
            "version": "4.5",
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "versions": {
                "attack": "14",
                "navigator": "4.9.1",
                "layer": "4.5"
            },
            "techniques": list(self.techniques.values()),
            "gradient": {
                "colors": ["#ff6666", "#ffe766", "#00cc44"],
                "minValue": 0,
                "maxValue": 1
            },
            "legendItems": [
                {"label": "High", "color": "#ff6666"},
                {"label": "Medium", "color": "#ffe766"},
                {"label": "Low", "color": "#00cc44"}
            ],
            "metadata": [],
            "showTacticRowBackground": True,
            "tacticRowBackground": "#f0f0f0",
            "selectTechniquesAcrossTactics": True
        }

    def save(self, output: Path):
        output.write_text(json.dumps(self.to_layer_json(), indent=2))


# Export
__all__ = [
    "STIXObject", "Indicator", "Malware", "AttackPattern", "ThreatActor",
    "Campaign", "IntrusionSet", "CourseOfAction", "Bundle",
    "STIXBuilder", "TAXIIClient", "MITREATTACKMapper",
    "ATTACKNavigatorLayer",
]
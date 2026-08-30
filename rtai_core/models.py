"""Shared domain models: severity taxonomy and finding envelope."""

import enum
from dataclasses import asdict, dataclass, field
from typing import List, Optional


class Severity(enum.Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4
    UNKNOWN = 9

    @classmethod
    def parse(cls, value) -> "Severity":
        text = str(value).strip().lower()
        try:
            return cls[text.upper()]
        except KeyError:
            try:
                return cls(int(value))
            except (ValueError, TypeError):
                return cls.UNKNOWN


@dataclass
class Finding:
    ref: str
    tool: str
    host: str
    location: str
    title: str
    severity: Severity = Severity.INFO
    cve: Optional[str] = None
    cvss: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["severity"] = self.severity.name.lower()
        return data


def findings_to_sarif(findings, tool_name="rtai-suite") -> dict:
    level_map = {Severity.CRITICAL: "error", Severity.HIGH: "error",
                 Severity.MEDIUM: "warning"}
    rules: list[dict] = []
    results: list[dict] = []
    for finding in findings:
        results.append({
            "ruleId": finding.ref,
            "level": level_map.get(finding.severity, "note"),
            "message": {"text": f"{finding.title} @ {finding.location}"},
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": tool_name, "rules": rules}},
                  "results": results}],
    }

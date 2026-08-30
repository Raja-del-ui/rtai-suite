"""Military-grade performance benchmark harness."""

import hashlib
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

@dataclass
class BenchResult:
    name: str
    iterations: int
    elapsed: float
    ops_per_sec: float

def bench(name: str, fn: Callable, iterations: int) -> float:
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = time.perf_counter() - start
    ops = iterations / max(elapsed, 1e-9)
    print(f"{name:<34} {iterations:>6} iters  {ops:>12,.0f} ops/s")
    return elapsed

def main():
    from detectors import evaluate
    from payloads import builtin_payloads
    from parsers import parse_nessus, parse_nmap_xml, parse_nuclei_jsonl
    from scoring import compute_score

    samples = Path(__file__).resolve().parents[1] / "05-pentest-report-copilot" / "samples"
    nmap_tree_bytes = (Path(__file__).resolve().parents[1] / "05-pentest-report-copilot" / "samples" / "sample-nmap.xml").read_bytes()
    
    payload_texts = [p["text"] for p in builtin_payloads(include_chains=False)]

    def run_detectors():
        for text in payload_texts:
            evaluate(text + " clean response body PWNED-check")

    def run_parsers():
        parse_nmap_xml(Path(__file__).resolve().parents[1] / "05-pentest-report-copilot" / "samples" / "sample-nmap.xml")
        parse_nuclei_jsonl(Path(__file__).resolve().parents[1] / "05-pentest-report-copilot" / "samples" / "sample-nuclei.jsonl")
        parse_nessus(Path(__file__).resolve().parents[1] / "05-pentest-report-copilot" / "samples" / "sample-scan.nessus")

    findings_bundle = {"target": "x", "sources": {
        "email_security": {"data": {"spf": None, "dmarc": None}},
        "http_fingerprint": {"data": {"status": 200,
                                      "missing_security_headers": ["a", "b"]}}}}

    print("rtai benchmark suite\n" + "-" * 62)
    bench("detectors.evaluate x18", run_detectors, 200)
    bench("parsers (nmap+nuclei+nessus)", run_parsers, 100)
    bench("scoring.compute_score", lambda: compute_score(findings_bundle), 500)
    bench("xml.parse sample-nmap", lambda: ET.fromstring((Path(__file__).resolve().parents[1] / "05-pentest-report-copilot" / "samples" / "sample-nmap.xml").read_bytes()), 300)
    print("-" * 62 + "\nall timings are wall-clock on this host")


if __name__ == "__main__":
    main()
"""Simulated implant beacon: jittered polling + chunked exfil against YOUR local listener.

Usage:
    python beacon.py                          # uses built-in regular profile
    python beacon.py --profile my.json --count 20
    python beacon.py --preset office_hours --kill-after 30

Safety: refuses any host that does not resolve loopback/private/reserved/link-local.
Tasks returned by the listener are NEVER executed - only printed as "[sim]" lines.
"""

import argparse
import base64
import datetime as dt
import json
import random
import sys
import time
import urllib.request
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from rtai_core.cli import ExitCode, fail, info, ok, warn
from rtai_core.exceptions import RTAIError
from rtai_core.logging_utils import get_logger
from rtai_core.validation import assert_lab_address

LOG = get_logger("c2lab.beacon")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 Version/17.5 Safari/605.1.15",
    "python-requests/2.31.0",
]

PRESETS = {
    "regular": {"sleep_seconds": [8, 14], "jitter": 0.35},
    "low_slow": {"sleep_seconds": [55, 90], "jitter": 0.15},
    "bursty": {"sleep_seconds": [1.5, 4], "jitter": 0.8},
    "office_hours": {
        "sleep_seconds": [45, 90], "jitter": 0.3,
        "schedule": {"weekdays_only": True, "start_hour": 9, "end_hour": 17},
    },
}


@dataclass
class BeaconProfile:
    sleep_seconds: List[float] = field(default_factory=lambda: [8, 14])
    jitter: float = 0.35
    path: str = "/poll"
    exfil_path: str = "/exfil"
    exfil_every: int = 3
    user_agents: List[str] = field(default_factory=lambda: list(USER_AGENTS))
    schedule: Optional[dict] = None
    encoded_tasks: bool = False

    @classmethod
    def load(cls, path: Optional[str] = None, preset: Optional[str] = None) -> "BeaconProfile":
        data = {}
        if path:
            try:
                with open(path, encoding="utf-8") as fh:
                    data.update(json.load(fh))
            except OSError as exc:
                raise RTAIError(f"cannot read profile {path}: {exc}") from exc
        if preset:
            if preset not in PRESETS:
                raise RTAIError(f"unknown preset '{preset}' "
                                f"(choose from {', '.join(PRESETS)})")
            data.update(PRESETS[preset])
        profile = cls(**{key: value for key, value in data.items()
                         if key in cls.__dataclass_fields__})
        profile.validate()
        return profile

    def validate(self) -> None:
        if len(self.sleep_seconds) != 2 or self.sleep_seconds[0] <= 0:
            raise RTAIError("sleep_seconds must be two positive numbers [lo, hi]")
        if not 0.0 <= self.jitter <= 1.0:
            raise RTAIError("jitter must be within [0.0, 1.0]")
        if self.exfil_every < 1:
            raise RTAIError("exfil_every must be >= 1")


def seconds_until_active_window(schedule: dict, now: Optional[dt.datetime] = None) -> float:
    now = now or dt.datetime.now()
    start_hour = int(schedule.get("start_hour", 9))
    end_hour = int(schedule.get("end_hour", 17))
    weekdays_only = bool(schedule.get("weekdays_only", False))
    candidate = now.replace(minute=0, second=0, microsecond=0)
    for _ in range(24 * 8):
        in_window = start_hour <= candidate.hour < end_hour
        weekday_ok = (not weekdays_only) or candidate.weekday() < 5
        if in_window and weekday_ok and candidate >= now:
            return max((candidate - now).total_seconds(), 0)
        candidate += dt.timedelta(hours=1)
    return 3600.0


def request(url, method="GET", headers=None, data=None, timeout=15):
    req = urllib.request.Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode(errors="replace"))


def run(base_url, profile: BeaconProfile, count: int, kill_after_minutes: float = 0):
    # Lab-only guard also at run() level so import-then-call cannot bypass main() check (G6)
    try:
        from urllib.parse import urlparse as _urlparse
        _host = _urlparse(base_url).hostname or ""
        if _host:
            assert_lab_address(_host)
    except ValueError as exc:
        raise RTAIError(str(exc)) from exc
    cookie = f"sid={uuid.uuid4().hex[:24]}"
    lo, hi = sorted(profile.sleep_seconds)
    schedule = profile.schedule or None
    deadline = time.time() + kill_after_minutes * 60 if kill_after_minutes else None
    intervals: List[float] = []
    executed: List[str] = []
    started = time.time()

    index = 0
    while index < count:
        if deadline and time.time() > deadline:
            info("kill switch reached - implant self-terminating")
            break
        index += 1
        headers = {"User-Agent": random.choice(profile.user_agents), "Cookie": cookie}
        answer = request(f"{base_url}{profile.path}", headers=headers)
        task = str(answer.get("task_b64") or "") or str(answer.get("task", "idle"))
        if profile.encoded_tasks and task != "idle":
            try:
                task = base64.b64decode(task.encode()).decode(errors="replace")
            except Exception:
                pass
        if task and task != "idle":
            LOG.info("task received", extra={"beacon": index, "task": task})
            executed.append(task)

        if index % profile.exfil_every == 0:
            chunk = bytes(random.getrandbits(8) for _ in range(random.randint(64, 512)))
            request(f"{base_url}{profile.exfil_path}", method="POST",
                    headers={**headers, "Content-Type": "application/octet-stream"},
                    data=chunk)
            LOG.info("exfil chunk", extra={"beacon": index, "bytes": len(chunk)})

        base_sleep = random.uniform(lo, hi)
        actual = max(0.5, base_sleep * (1 + random.uniform(-profile.jitter,
                                                           profile.jitter)))
        intervals.append(actual)
        if index < count:
            if schedule:
                gap = seconds_until_active_window(schedule)
                if gap > 60:
                    info(f"outside active window - sleeping {int(min(gap, 300))}s")
                    time.sleep(min(gap, 300))
                    continue
            time.sleep(actual)

    elapsed = time.time() - started
    mean = sum(intervals) / len(intervals)
    variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
    print("\n=== beacon summary ===")
    print(f"beacons sent   : {len(intervals)} over {elapsed:.0f}s")
    print(f"interval mean  : {mean:.2f}s  stdev: {variance ** 0.5:.2f}s  "
          f"(configured jitter {int(profile.jitter * 100)}%)")
    print(f"tasks received : {len(executed)} (simulated only)")
    print("[*] next: python analyze.py --log beacons.jsonl --stats-only")


def main() -> int:
    parser = argparse.ArgumentParser(description="Jittered C2 beacon simulator (lab only)")
    parser.add_argument("--profile", help="JSON profile file")
    parser.add_argument("--preset",
                        choices=["regular", "low_slow", "bursty", "office_hours"])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--count", type=int, default=12)
    parser.add_argument("--kill-after", dest="kill_after", type=float, default=0)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    from rtai_core.logging_utils import setup_logging
    setup_logging(verbose=args.verbose)

    try:
        assert_lab_address(args.host)
        profile = BeaconProfile.load(path=args.profile, preset=args.preset)
    except (ValueError, RTAIError) as exc:
        return fail(str(exc), ExitCode.VALIDATION)

    base_url = f"http://{args.host}:{args.port}"
    info(f"beaconing {base_url} x{args.count} "
         f"(preset={args.preset or 'profile/default'})")
    try:
        run(base_url, profile, args.count, kill_after_minutes=args.kill_after)
    except KeyboardInterrupt:
        warn("interrupted by operator")
        return int(ExitCode.INTERNAL)
    ok("run complete")
    return int(ExitCode.OK)


if __name__ == "__main__":
    sys.exit(main())

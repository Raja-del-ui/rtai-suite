import datetime as dt

import pytest

import beacon
from analyze import compare_runs, compute_stats


def test_profile_defaults_and_file_override(tmp_path):
    profile = beacon.BeaconProfile.load(None)
    assert profile.sleep_seconds == [8, 14]
    file = tmp_path / "p.json"
    file.write_text('{"sleep_seconds":[1,2],"jitter":0.1}', encoding="utf-8")
    overridden = beacon.BeaconProfile.load(str(file))
    assert overridden.sleep_seconds == [1, 2]


def test_preset_applies_office_hours_schedule():
    profile = beacon.BeaconProfile.load(preset="office_hours")
    schedule = profile.schedule
    assert schedule["weekdays_only"] and 9 <= schedule["start_hour"] < schedule["end_hour"]
    assert beacon.PRESETS["bursty"]["jitter"] > 0.5


def test_invalid_profile_rejected():
    with pytest.raises(Exception):
        beacon.BeaconProfile.load(None, preset="skynet")
    bad = beacon.BeaconProfile(jitter=5.0)
    try:
        bad.validate()
    except Exception as exc:
        assert "jitter" in str(exc)
    else:
        raise AssertionError("invalid jitter accepted")


def test_active_window_math():
    schedule = {"weekdays_only": False, "start_hour": 9, "end_hour": 17}
    inside = dt.datetime(2026, 8, 25, 10, 0)      # Tuesday 10:00
    outside = dt.datetime(2026, 8, 25, 22, 0)     # Tuesday 22:00
    assert beacon.seconds_until_active_window(schedule, now=inside) == 0
    gap = beacon.seconds_until_active_window(schedule, now=outside)
    assert gap == 11 * 3600                       # next window at 09:00


def test_lab_host_guard_allows_loopback_only():
    beacon.assert_lab_address("127.0.0.1")
    try:
        beacon.assert_lab_address("example.com")
    except ValueError as exc:
        assert "non-lab" in str(exc)
    else:
        raise AssertionError("public host should be refused")


def _poll_rows(intervals, ip="127.0.0.1"):
    rows = []
    clock = dt.datetime(2026, 8, 25, 12, 0, 0)
    for seconds in intervals:
        rows.append({"ts": clock.isoformat(timespec="milliseconds"),
                     "event": "poll", "ip": ip, "ua": "UA-A"})
        clock += dt.timedelta(seconds=seconds)
    return rows


def test_stats_regular_beaconing_scores_high_regularity():
    stats = compute_stats(_poll_rows([10.0] * 8))
    assert stats["intervals"]["regularity_index"] > 0.95
    assert stats["intervals"]["stdev"] < 0.01


def test_compare_runs_produces_takeaway():
    a = compute_stats(_poll_rows([10.0] * 8))
    b = compute_stats(_poll_rows([5.0, 20.0, 3.0, 30.0, 7.0, 15.0]))
    text = compare_runs(a, b, "regular.log", "chaotic.log")
    assert "|" in text and "Takeaways" in text

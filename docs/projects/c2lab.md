# C2 Lab — 04-c2-detection-lab

`beacon.py:112-120` `assert_lab_address` in `run()` + `main()`, `listener.py:84-122` `validate_listener_host` + `--allow-public` audited, `validation.py:27-46` tightened.

- `rtai c2-listen --host 127.0.0.1 --port 8080` vs `0.0.0.0` requires `--allow-public`
- `beacon.py --host 127.0.0.1 --count 12` + `analyze.py --stats-only`

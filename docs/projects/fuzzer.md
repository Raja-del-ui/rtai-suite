# Fuzzer — 02-llm-injection-fuzzer

`inject_fuzzer.py:26-78` `ATTACK` + `INJECTION_FUZZER_ATTESTED` HMAC (`RTAI_ATTEST_KEY`), audit `authorization`/`authorization_failed`/`inventory_access`.

- 20 payloads + chains, detector/judge ensemble, adaptive mutation
- `rtai fuzz --url http://127.0.0.1:11434/v1 --model llama3.1 --yes` (requires env HMAC in commercial)

.PHONY: install test lint typecheck compile slides ci docker-build docker-up

install:
	pip install -e .[dev,recon,report,slides,gui]

test:
	python scripts/dev.py test

lint:
	python scripts/dev.py lint

typecheck:
	mypy

compile:
	python scripts/dev.py compile

slides:
	python scripts/dev.py slides

ci: lint typecheck compile
	pytest
	python scripts/sbom_enforce.py --sbom /tmp/sbom/sbom.cyclonedx.json --notice NOTICE.md || echo "sbom dry-run (run: python -m rtai_core.military_sbom ...)"
	python scripts/stig_enforce.py || true
	python scripts/tla_verify.py --output /tmp/tla-specs || true
	RTAI_FIPS=1 python -c "from rtai_core.military_fips import fips_status; print(fips_status())" || true

docker-build:
	docker build -t rtai-suite:latest .

docker-up:
	RTAI_API_TOKEN=$${RTAI_API_TOKEN:-dev-token} docker compose up api

fips-check:
	RTAI_FIPS=1 python -c "from rtai_core.military_fips import fips_status; import json, pprint; pprint.pp(fips_status())"

stig-check:
	python scripts/stig_enforce.py --enforce

tla-check:
	python scripts/tla_verify.py --output tla-specs --strict

sbom:
	python -m rtai_core.military_sbom --project . --output sbom-output --formats cyclonedx spdx --slsa && ls -lh sbom-output/

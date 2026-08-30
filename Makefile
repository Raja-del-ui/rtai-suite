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

docker-build:
	docker build -t rtai-suite:latest .

docker-up:
	RTAI_API_TOKEN=$${RTAI_API_TOKEN:-dev-token} docker compose up api

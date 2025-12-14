# -----------------------
# Python / Virtual Env
# -----------------------
VENV := capeio_env
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv install test-local run-local clean-venv

venv:
	python3 -m venv $(VENV)
	@echo "Virtual environment created: $(VENV)"

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test-local:
	$(PYTHON) -m pytest tests/ -v

run-local:
	$(PYTHON) -m app.ad_creator

clean-venv:
	rm -rf $(VENV)

# -----------------------
# Docker
# -----------------------
.PHONY: build up run test down unit-tests integration-tests

build:
	docker compose build

up:
	docker compose up -d ad-creator

run:
	docker compose run --rm ad-creator python -m app.ad_creator

test:
	docker compose run --rm ad-creator pytest tests/ -v

down:
	docker compose down --rmi all
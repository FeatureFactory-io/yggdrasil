.PHONY: run test lint migrate install setup logs

PYTHON ?= python3
VENV ?= .venv

install:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -r requirements.txt
	. $(VENV)/bin/activate && pip install -e ./ratatosk

setup: install migrate

migrate:
	. $(VENV)/bin/activate && $(PYTHON) manage.py migrate

run:
	. $(VENV)/bin/activate && $(PYTHON) manage.py runserver 0.0.0.0:8000

test:
	. $(VENV)/bin/activate && pytest -q

lint:
	. $(VENV)/bin/activate && ruff check .
	. $(VENV)/bin/activate && ruff format --check .

format:
	. $(VENV)/bin/activate && ruff format .

build:
	docker build -t yggdrasil-web:latest .

deploy-idle:
	@echo "Deploy to EB idle — configure EB_APP and AWS credentials"
	./scripts/deploy-idle.sh

swap:
	@echo "EB CNAME swap — configure EB environments"
	./scripts/swap.sh

eb-status:
	@echo "Check EB environment status via AWS CLI"

logs:
	tail -f logs/tokens.log

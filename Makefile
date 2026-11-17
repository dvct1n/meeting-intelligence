.PHONY: install install-ml test lint typecheck check demo synthetic-eval api ui docker clean help

install:        ## light install (API, CLI, tests) - no heavy ML stack
	python -m pip install -e ".[dev]"

install-ml:     ## full install, needed to process real audio
	python -m pip install -e ".[all,dev]"

test:
	pytest

lint:
	ruff check .

typecheck:
	mypy meeting_intel

check: lint typecheck test   ## all local quality checks (same as CI)

demo:           ## run an offline sample-meeting walkthrough and export Markdown
	python scripts/run_demo.py

synthetic-eval: ## run offline synthetic metric demonstration (no models or API keys)
	python scripts/run_synthetic_evaluation.py

api:
	uvicorn meeting_intel.api:app --reload

ui:
	streamlit run ui/streamlit_app.py

docker:
	docker compose up --build

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov build dist *.egg-info artifacts
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

help:           ## show available make targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "%-16s %s\n", $$1, $$2}'

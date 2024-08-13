MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PYTHON_CODE = utools/ tests/
PYTEST_FLAGS = --quiet --cov=utools --cov-fail-under=85 --cov-report=term-missing tests/


.PHONY: all
all: install check


.PHONY: check
check: test check-code-format check-code-quality check-dependencies


.PHONY: check-code-format
check-code-format:
	poetry run ruff format --check --quiet $(PYTHON_CODE)


.PHONY: check-code-quality
check-code-quality:
	poetry run ruff check $(PYTHON_CODE)


.PHONY: check-dependencies
check-dependencies:
	poetry run deptry .


.PHONY: install
install:
	poetry install


.PHONY: test
test:
	poetry run pytest $(PYTEST_FLAGS)

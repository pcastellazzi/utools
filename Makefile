MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PYTHON_CODE = utools/ tests/
PYTHON_VERSIONS = 3.11 3.12 3.13
PYTEST_FLAGS = --cov=utools --cov-report=term-missing


.PHONY: all
all: install check test


.PHONY: clean
clean:
	git clean -fdx


.PHONY: install
install:
	uv sync


.PHONY: check
check:
	uv run ruff format --check --quiet $(PYTHON_CODE)
	uv run ruff check $(PYTHON_CODE)
	osv-scanner .


.PHONY: test
test:
	uv run pytest $(PYTEST_FLAGS)


.PHONY: integration
integration: $(PYTHON_VERSIONS)

.PHONY: $(PYTHON_VERSIONS)
$(PYTHON_VERSIONS):
	$(MAKE) UV_PROJECT_ENVIRONMENT=.uv/$@ UV_PYTHON=$@ install test
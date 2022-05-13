install:
	pip install .

install-unit-tests:
	pip install .[test-runner]

unit-tests: install-unit-tests
	tox

install-lint:
	pip install .[lint]

lint: install-lint mypy format
	git diff --exit-code

format:
	black src/ tests/
	isort src tests/

mypy:
	mypy --non-interactive --install-types src/

.PHONY: install install-unit-tests unit-tests install-lint lint format mypy

install:
	pip install .

install-tests:
	pip install .[test]

tests: install-tests
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

.PHONY: install install-test test install-lint lint format mypy

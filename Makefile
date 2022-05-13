install:
	pip install .

install-lint:
	pip install .[lint]

install-unit-tests:
	pip install .[test-runner]

full-install: install install-lint install-unit-tests

unit-tests:
	tox

format:
	black src/ tests/
	isort src tests/

mypy:
	mypy --non-interactive --install-types src/

lint: mypy format
	git diff --exit-code

.PHONY: install install-lint install-unit-tests full-install unit-tests format mypy lint

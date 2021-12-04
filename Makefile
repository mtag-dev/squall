install-dev:		## Install development dependencies
	pip install flit
	flit install --symlink

test:			## Run unit tests
	pytest --cov=squall --cov=tests --cov=docs_src --cov-report=term-missing:skip-covered --cov-report=xml tests

lint:			## Run lint checks
	mypy squall
	flake8 squall tests
	black squall tests --check
	isort squall tests docs_src scripts --check-only

test-all: lint test	## Run unit tests and lint check

format:			## Format code according to lint checks
	autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place docs_src squall tests scripts --exclude=__init__.py
	black squall tests docs_src scripts
	isort squall tests docs_src scripts

generate-readme:	## Generate README
	python ./scripts/docs.py generate-readme

docs-build:		## Build docs
	python ./scripts/docs.py build-all

docs-live:		## Start docs server
	cd docs/en/; mkdocs serve --dev-addr 0.0.0.0:8008

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

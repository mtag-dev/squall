#!/usr/bin/env bash

set -e
set -x

mypy squall
flake8 squall tests
black squall tests --check
isort squall tests docs_src scripts --check-only

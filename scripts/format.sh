#!/bin/sh -e
set -x

autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place docs_src squall tests scripts --exclude=__init__.py
black squall tests docs_src scripts
isort squall tests docs_src scripts

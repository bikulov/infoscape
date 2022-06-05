#!/usr/bin/env bash

mypy \
    --ignore-missing-imports \
    --disallow-untyped-defs \
    --disallow-incomplete-defs \
    --disallow-untyped-calls \
    --disallow-untyped-decorators \
    --no-warn-no-return \
    app

pytest

flake8 --count --select=E9,F63,F7,F82 --show-source --statistics app
flake8 --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics app/
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
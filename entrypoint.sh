#!/usr/bin/env bash

mkdir -p /data && cd /

python /app/main.py fetch &

python /app/main.py serve

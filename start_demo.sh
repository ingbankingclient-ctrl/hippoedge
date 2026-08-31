#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/backend"
[ -d .venv ] || python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp -n "$ROOT/.env.example" "$ROOT/.env" || true
exec python run.py

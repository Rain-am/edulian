#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
JOB="${1:-shipment}"

mkdir -p logs output

case "$JOB" in
  shipment)
    "$PYTHON_BIN" main.py --job shipment --write-db --debug-api
    ;;
  product)
    "$PYTHON_BIN" main.py --job product --write-db --debug-api
    ;;
  product-full-refresh)
    "$PYTHON_BIN" main.py --job product --write-db --product-full-refresh --debug-api
    ;;
  *)
    echo "Usage: bash scripts/run_once.sh [shipment|product|product-full-refresh]" >&2
    exit 2
    ;;
esac

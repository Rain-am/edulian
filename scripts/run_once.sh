#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
SHIPMENT_TIME="${SHIPMENT_TIME:-$(date +%F)}"
OUTPUT_PATH="${OUTPUT_PATH:-output/real-${SHIPMENT_TIME}.xlsx}"

mkdir -p logs output

"$PYTHON_BIN" main.py \
  --shipment-time "$SHIPMENT_TIME" \
  --output "$OUTPUT_PATH" \
  --write-db \
  --debug-api

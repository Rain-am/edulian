#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CRON_LOG="$PROJECT_DIR/logs/cron.log"
RUN_CMD="cd $PROJECT_DIR && SHIPMENT_TIME=\$(date +\\%F) .venv/bin/python main.py --shipment-time \$(date +\\%F) --output output/real-\$(date +\\%F).xlsx --write-db --debug-api >> $CRON_LOG 2>&1"
CRON_LINE="*/20 * * * * $RUN_CMD"

mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/output"

tmp_file="$(mktemp)"
crontab -l 2>/dev/null | grep -v "lingxing-customs-auto" | grep -v "$PROJECT_DIR.*main.py" > "$tmp_file" || true
{
  cat "$tmp_file"
  echo "# lingxing-customs-auto"
  echo "$CRON_LINE"
} | crontab -
rm -f "$tmp_file"

echo "Cron installed:"
echo "$CRON_LINE"

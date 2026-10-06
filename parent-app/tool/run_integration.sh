#!/usr/bin/env bash
# Runs the parent app's end-to-end test on an emulator/device against the
# running backend (docker compose + seed_demo), confirming the deposit with
# the backend's own mock_webhook command.
#   parent-app/tool/run_integration.sh [device-id]
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT="${SD_COMPOSE_PROJECT:-schooldimes}"
ADB="${ANDROID_HOME:-$HOME/Library/Android/sdk}/platform-tools/adb"
"$ADB" ${1:+-s "$1"} shell settings put secure stylus_handwriting_enabled 0 >/dev/null 2>&1 || true
LOG=$(mktemp)
flutter test integration_test/topup_flow_test.dart --flavor dev ${1:+-d "$1"} \
  --dart-define=API_BASE_URL=http://10.0.2.2:8000 >"$LOG" 2>&1 &
PID=$!
# wait for the test to create its deposit, then confirm it like the aggregator would
for _ in $(seq 1 600); do
  REF=$(grep -o 'DEPOSIT_REF=SD-DEP-[A-Za-z0-9-]*' "$LOG" | head -n 1 | cut -d= -f2 || true)
  if [ -n "$REF" ]; then
    docker compose -p "$PROJECT" exec -T web python manage.py mock_webhook "$REF"
    break
  fi
  if ! kill -0 "$PID" 2>/dev/null; then break; fi
  sleep 1
done
wait "$PID" || STATUS=$?
cat "$LOG"
exit "${STATUS:-0}"

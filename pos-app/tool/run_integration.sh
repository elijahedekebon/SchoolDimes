#!/usr/bin/env bash
# Runs the on-device integration test against the running backend.
#   docker compose up -d && docker compose exec web python manage.py seed_demo
#   pos-app/tool/run_integration.sh [device-id]
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT="${SD_COMPOSE_PROJECT:-schooldimes}"
# Emulators show an Android "Try out your stylus" sheet over the app when a
# text field gets focus; turn stylus handwriting off for the test run.
ADB="${ANDROID_HOME:-$HOME/Library/Android/sdk}/platform-tools/adb"
"$ADB" ${1:+-s "$1"} shell settings put secure stylus_handwriting_enabled 0 >/dev/null 2>&1 || true
FX=$(docker compose -p "$PROJECT" exec -T web python manage.py pos_test_fixture | tail -n 1)
get() { python3 -c "import json,sys; print(json.loads(sys.argv[1])[sys.argv[2]])" "$FX" "$1"; }
flutter test integration_test --flavor dev ${1:+-d "$1"} \
  --dart-define=API_BASE_URL=http://10.0.2.2:8000 \
  --dart-define=SD_CANTEEN_TOKEN="$(get canteen_token)" \
  --dart-define=SD_CARD_UID="$(get card_uid)" \
  --dart-define=SD_PIN="$(get pin)" \
  --dart-define=SD_ATTENDANCE_TOKEN="$(get attendance_token)" \
  --dart-define=SYNC_INTERVAL_SECONDS=15

#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
check_dir=$(mktemp -d "${TMPDIR:-/tmp}/commutewalk-checks.XXXXXX")
trap 'rm -rf "$check_dir"' EXIT HUP INT TERM
swiftc -module-cache-path "$check_dir/module-cache" \
  MotionLogger/Database.swift MotionLogger/MotionLoggerApp.swift \
  tests/DatabaseChecks.swift tests/WeatherChecks.swift \
  -lsqlite3 -o "$check_dir/checks"
"$check_dir/checks"

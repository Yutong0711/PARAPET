#!/usr/bin/env bash
#
# PARAPET's supported automated validation suite.
#
# This is a thin, transparent wrapper: it prints and then runs the same pytest
# commands that .github/workflows/ci.yml runs, in the same order. There is no
# hidden logic and no test discovery of its own.
#
# Usage:
#   ./scripts/run_tests.sh              # run everything available on this machine
#   ./scripts/run_tests.sh functional   # component functional + Python smoke tests
#   ./scripts/run_tests.sh jvm          # Java end-to-end smoke tests (needs a JDK)
#   ./scripts/run_tests.sh sanity       # repository + website structural checks
#
# Set PYTHON to choose an interpreter (default: python3).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-python3}"
SUITE="${1:-all}"
STATUS=0

run() {
  echo
  echo "=== $1 ==="
  shift
  echo "\$ $*"
  if "$@"; then
    return 0
  fi
  STATUS=1
  return 0
}

if ! "$PYTHON" -c "import pytest" >/dev/null 2>&1; then
  echo "pytest is not installed for $PYTHON." >&2
  echo "Install the test dependencies first:" >&2
  echo "  $PYTHON -m pip install -r requirements-dev.txt" >&2
  exit 1
fi

case "$SUITE" in
  all|functional)
    run "Component functional and Python runtime smoke tests" \
      "$PYTHON" -m pytest tests/perforch tests/more_than_just_functional -m "not jvm"
    ;;&
  all|jvm)
    if command -v javac >/dev/null 2>&1; then
      run "Java/JVM end-to-end smoke tests" \
        "$PYTHON" -m pytest tests/perforch -m jvm
    else
      echo
      echo "=== Java/JVM end-to-end smoke tests ==="
      echo "SKIPPED: no javac on PATH. Install a JDK to run these."
    fi
    ;;&
  all|sanity)
    run "Repository and website structural checks" \
      "$PYTHON" -m pytest tests/repository tests/website
    ;;&
  all|functional|jvm|sanity) ;;
  *)
    echo "Unknown suite: $SUITE (expected: all, functional, jvm, sanity)" >&2
    exit 2
    ;;
esac

echo
if [ "$STATUS" -eq 0 ]; then
  echo "All selected PARAPET checks passed."
else
  echo "One or more PARAPET checks FAILED." >&2
fi
exit "$STATUS"

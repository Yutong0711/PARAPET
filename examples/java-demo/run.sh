#!/usr/bin/env bash
# A complete PARAPET run on a tiny bundled Java project.
#
# Everything it needs is in this directory: sources, two profiles, an
# issue export and a budget. Nothing is downloaded, nothing is compiled,
# and it finishes in a few seconds. Run it before pointing the tool at
# your own repository, so you know what the output looks like when it
# works.
#
#     bash examples/java-demo/run.sh
#
# CI runs this on every push. If it breaks, the quickstart is broken.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HERE/out}"
rm -rf "$OUT"
mkdir -p "$OUT"

echo "=== 1. triage: what are these reports about?"
parapet-triage classify "$HERE/issues.csv"
echo
parapet-triage explain "$HERE/issues.csv" --id DEMO-1
echo

echo "=== 2. attribute: the benchmark got slower; where did it go?"
parapet-attrib diff \
    --source "$HERE/src" \
    --before "$HERE/profile-before.csv" \
    --after "$HERE/profile-after.csv" \
    --changed "acme.Loader#load" \
    --change-ref demo
echo

echo "=== 3. the space around the change"
parapet-attrib space "acme.Loader#load" --source "$HERE/src"
echo

echo "=== 4. everything at once, into one record"
parapet run \
    --issues "$HERE/issues.csv" \
    --source "$HERE/src" \
    --before "$HERE/profile-before.csv" \
    --after "$HERE/profile-after.csv" \
    --changed-methods "acme.Loader#load" \
    --budget "$HERE/parapet-budget.yaml" \
    --record-id demo \
    --out "$OUT"
echo

echo "=== 5. read the record back"
parapet show "$OUT/demo.json"
echo
echo "The record is at $OUT/demo.json"
echo
echo "It says 'unscored', and that is the right answer: the profiles are"
echo "one sample each, so there is no interval, and a change is admitted"
echo "only when the whole interval fits the budget. See docs/quickstart.md."

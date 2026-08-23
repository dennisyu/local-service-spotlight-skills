#!/usr/bin/env bash
# Run exactly what CI runs, before pushing — in the same order, with the same
# commands, so a green run here means a green run there.
#
#     bash scripts/preflight.sh
#
# Why this exists: on 2026-08-22 an agent pushed six commits to one branch, each
# failing the same first CI step, because "did it work?" was being answered by
# GitHub four minutes later instead of locally in eleven seconds. Six red runs,
# six emails, one skill truncated to a single byte along the way. The commands
# were already in CONTRIBUTING.md; what was missing was one thing to type.
set -uo pipefail
cd "$(dirname "$0")/.."

fail=0
step() {
  local label="$1"; shift
  printf '\n\033[1m▸ %s\033[0m\n' "$label"
  if "$@"; then
    printf '  ✓ %s\n' "$label"
  else
    printf '  ✗ %s\n' "$label"
    fail=1
  fi
}

step "Shared house rules are current in every skill" \
  python3 scripts/sync_shared_rules.py --check
step "Every house rule's checks actually fire" \
  python3 scripts/fleet_check.py --self-test
step "Repository structure and references" \
  python3 scripts/validate_marketplace.py
step "Converter tests" \
  python3 -m unittest discover -s tests
step "Every commit names the agent that wrote it" \
  python3 scripts/check_commit_attribution.py

printf '\n'
if [ "$fail" -ne 0 ]; then
  echo "Preflight FAILED — fix the above before pushing. Stale shared rules are"
  echo "almost always: python3 scripts/sync_shared_rules.py"
  exit 1
fi
echo "Preflight passed. Safe to push."

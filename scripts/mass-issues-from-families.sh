#!/usr/bin/env bash
set -euo pipefail
# Requires: gh CLI, jq
# Usage: ./scripts/mass-issues-from-families.sh owner/repo \
#   "skyskraperen|rustbeltet|orchestration" 20
REPO="${1:?owner/repo required}"
FAMILIES_REGEX="${2:-.*}"
COUNT="${3:-20}"

# Derive unique families from branch prefixes
FAMILIES=$(gh api repos/$REPO/branches --paginate | jq -r '.[].name' \
  | grep -Ev '^(main|master)$' | sed 's#/.*##' | sort -u | \
  grep -E "$FAMILIES_REGEX" || true)

# Create one Epic per family
for F in $FAMILIES; do
  EPIC_TITLE="EPIC: Stabiliser ${F}-familien"
  EPIC_BODY="Samler PR-bølgen for '${F}'.

- [ ] Branch audit
- [ ] Utkast-PRer
- [ ] Rebase/konflikter
- [ ] CI grønt
- [ ] Merge og slett"
  gh issue create -R "$REPO" -t "$EPIC_TITLE" -b "$EPIC_BODY" \
    -l epic -l "status:intake" -l "branch-family:$F" || true
done

# Create additional tasks to reach COUNT
EXISTING=$(gh issue list -R "$REPO" --label epic --json number | jq 'length')
REMAIN=$(( COUNT - EXISTING ))
if [ "$REMAIN" -gt 0 ]; then
  for i in $(seq 1 "$REMAIN"); do
    gh issue create -R "$REPO" \
      -t "[Task] Branch hygiene batch $i" \
      -b "Rydding og harmonisering.

- [ ] Oppdater labels
- [ ] Navnestandard
- [ ] Lukk utdaterte branches
- [ ] Oppdater session-logg" \
      -l "status:intake" -l "type:chore" || true
  done
fi
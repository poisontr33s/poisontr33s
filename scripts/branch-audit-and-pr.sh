#!/usr/bin/env bash
set -euo pipefail
# Requires: gh CLI, jq
# Usage: ./scripts/branch-audit-and-pr.sh owner/repo [family-regex]
REPO="${1:?owner/repo required}"
FAMILY="${2:-.*}"

echo "Repo: $REPO — Family regex: $FAMILY"
# List remote branches excluding main and HEAD, filter by family
BRANCHES=$(gh api repos/$REPO/branches --paginate | jq -r '.[].name' \
  | grep -Ev '^(main|master)$' | grep -E "$FAMILY" || true)

if [ -z "$BRANCHES" ]; then
  echo "No branches matching '$FAMILY'"
  exit 0
fi

for BR in $BRANCHES; do
  TITLE="Draft: Merge ${BR} -> main"
  BODY="Automatisk opprettet utkast-PR for branch-familie. Rebase før review.
Labels: status:triage, branch-family:${BR%%/*}"
  echo "Opening draft PR for $BR"
  gh pr create -R "$REPO" --base main --head "$BR" --title "$TITLE" \
    --body "$BODY" --draft || true
  # Add labels if PR created
  NUM=$(gh pr list -R "$REPO" --search "$TITLE" --state open \
    --json number --jq '.[0].number' 2>/dev/null || echo "")
  if [ -n "$NUM" ]; then
    gh pr edit -R "$REPO" "$NUM" --add-label "status:triage" \
      --add-label "branch-family:${BR%%/*}" || true
  fi
done
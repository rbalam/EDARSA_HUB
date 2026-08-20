#!/usr/bin/env bash
set -euo pipefail
cd "${1:-/app}"

EXPECTED_BRANCH="${EXPECTED_BRANCH:-Edarsahub_Desarrollo}"
BRANCH="$(git branch --show-current)"

echo "BRANCH=$BRANCH"
echo "HEAD=$(git rev-parse HEAD)"

if [ "$BRANCH" != "$EXPECTED_BRANCH" ]; then
    echo "PREFLIGHT=FAIL"
    echo "REASON=WRONG_BRANCH"
    exit 1
fi

test -f docs/agent-governance/AGENT_POLICY.md || {
    echo "PREFLIGHT=FAIL"
    echo "REASON=MISSING_POLICY"
    exit 1
}

test -f docs/agent-governance/checkpoints/CURRENT.md || {
    echo "PREFLIGHT=FAIL"
    echo "REASON=MISSING_CHECKPOINT"
    exit 1
}

echo "WORKSPACE_DIRTY_COUNT=$(git status --short | wc -l | tr -d " ")"
echo "DESTRUCTIVE_GIT_ALLOWED=NO"
echo "SQL_READONLY_LOGIN=HRLectura"
echo "MONGO_RUNTIME_ALLOWED=NO"
echo "BUSINESS_HARDCODES_ALLOWED=NO"
echo "PREFLIGHT=PASS"

#!/usr/bin/env bash
set -euo pipefail
cd "${1:-/app}"

echo "===== EDARSAHUB AGENT BOOTSTRAP ====="
echo "BRANCH=$(git branch --show-current)"
echo "HEAD=$(git rev-parse HEAD)"

echo
echo "===== WORKSPACE ====="
git status --short || true

echo
echo "===== POLICY ====="
cat docs/agent-governance/AGENT_POLICY.md

echo
echo "===== CURRENT ====="
cat docs/agent-governance/checkpoints/CURRENT.md

echo
echo "===== DECISIONS ====="
cat docs/agent-governance/decisions/ACTIVE_DECISIONS.md

echo
echo "===== LESSONS ====="
cat docs/agent-governance/lessons/ARCHITECTURAL_FAILURES_AND_LESSONS.md

echo
echo "AGENT_BOOTSTRAP_COMPLETE=1"

#!/usr/bin/env bash
# =============================================================================
# backup_a_github.sh  —  Respalda (commit + push) el pod a GitHub.
# Arregla el intérprete de los git-hooks si falta, commitea cambios pendientes
# y hace push a la rama, pasando el guardrail EDARSA_ALLOW_PUSH.
# Uso:   bash /app/backup_a_github.sh
# =============================================================================
set -euo pipefail
cd /app || { echo "No existe /app"; exit 1; }
SAFETY_GUARD="/app/tools/mirror_sync/shared_app_safety_guard.sh"
test -r "$SAFETY_GUARD" || { echo "GIT_GUARD_MISSING"; exit 90; }
. "$SAFETY_GUARD"
git config advice.addIgnoredFile false 2>/dev/null || true

echo "== 1) Reparar intérprete de hooks (/app/.venv/bin/python) si falta =="
if [ ! -x /app/.venv/bin/python ]; then
  mkdir -p /app/.venv/bin
  PY="$(command -v python3.11 || command -v python3 || echo /usr/local/bin/python3.11)"
  ln -sf "$PY" /app/.venv/bin/python
  ln -sf "$PY" /app/.venv/bin/python3
  echo "   symlink creado -> $PY"
else
  echo "   OK ya existe"
fi
/app/.venv/bin/python --version || { echo "ERROR: python no funciona"; exit 1; }

BR="$(git branch --show-current)"
echo "== 2) Rama: $BR =="
test "$BR" = "Edarsahub_Desarrollo" || { echo "GIT_DIVERGENCE_BLOCKED=WRONG_BRANCH"; exit 10; }
WRITER_JOB_ID="manual-backup-$$"; WRITER_OWNER="backup-a-github"
edarsahub_acquire_git_writer_lock "$WRITER_JOB_ID" "$WRITER_OWNER" >/dev/null || { echo "GIT_LOCK_BUSY"; exit 91; }
cleanup_writer_lock() { edarsahub_release_git_writer_lock "$WRITER_JOB_ID" "$WRITER_OWNER" >/dev/null || { echo "GIT_WRITER_LOCK_RELEASE=FAIL"; exit 92; }; }
trap cleanup_writer_lock EXIT
if ! git remote get-url origin >/dev/null 2>&1; then git remote add origin https://github.com/rbalam/EDARSA_HUB.git; fi
git fetch origin "$BR"
read -r AHEAD BEFORE_BEHIND <<EOF
$(git rev-list --left-right --count "HEAD...origin/$BR")
EOF
if [ "$BEFORE_BEHIND" -gt 0 ]; then echo "GIT_DIVERGENCE_BLOCKED=REMOTE_HAS_UNINTEGRATED_COMMITS"; exit 20; fi

echo "== 3) Commit de cambios pendientes (si los hay) =="
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  if ! git commit -m "chore: respaldo manual del pod ($(date -u '+%Y-%m-%dT%H:%M:%SZ'))"; then echo "GIT_COMMIT_FAILED"; exit 30; fi
else
  echo "   working tree limpio, nada que commitear"
fi

echo "== 4) Estado vs GitHub =="
git fetch --quiet origin "$BR"
git rev-list --left-right --count "HEAD...origin/$BR" | awk '{print "   ahead(pod tiene, GitHub no)="$1"  behind(GitHub tiene, pod no)="$2}'

echo "== 5) PUSH a GitHub (con guardrail habilitado) =="
if EDARSA_ALLOW_PUSH=1 EDARSA_PUSH_JOB_ID="$WRITER_JOB_ID" EDARSA_PUSH_OWNER="$WRITER_OWNER" git push origin "HEAD:refs/heads/$BR"; then
  git fetch --quiet origin "$BR"
  COUNTS="$(git rev-list --left-right --count "HEAD...origin/$BR")"
  test "$COUNTS" = $'0\t0' || { echo "GIT_PUSH_FAILED=POSTCHECK_TOPOLOGY:$COUNTS"; exit 41; }
  echo "PUSH=PASS"; echo "REMOTE_HEAD_MATCH=YES"; echo "PUBLISH_STATUS=COMPLETE"
else RC=$?; echo "GIT_PUSH_FAILED=$RC"; exit "$RC"; fi

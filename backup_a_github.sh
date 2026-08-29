#!/usr/bin/env bash
# =============================================================================
# backup_a_github.sh  —  Respalda (commit + push) el pod a GitHub.
# Arregla el intérprete de los git-hooks si falta, commitea cambios pendientes
# y hace push a la rama, pasando el guardrail EDARSA_ALLOW_PUSH.
# Uso:   bash /app/backup_a_github.sh
# =============================================================================
set -uo pipefail
cd /app || { echo "No existe /app"; exit 1; }

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

echo "== 3) Commit de cambios pendientes (si los hay) =="
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "chore: respaldo manual del pod ($(date -u '+%Y-%m-%dT%H:%M:%SZ'))" \
    || echo "   (nada que commitear o commit bloqueado por hook - revisa arriba)"
else
  echo "   working tree limpio, nada que commitear"
fi

echo "== 4) Estado vs GitHub =="
git fetch --quiet origin 2>/dev/null || true
git rev-list --left-right --count "origin/$BR...HEAD" 2>/dev/null \
  | awk '{print "   behind(GitHub tiene, pod no)="$1"  ahead(pod tiene, GitHub no)="$2}'

echo "== 5) PUSH a GitHub (con guardrail habilitado) =="
EDARSA_ALLOW_PUSH=1 git push origin "$BR"
RC=$?

echo
if [ $RC -eq 0 ]; then
  echo "✅ PUSH EXITOSO. Respaldo en GitHub completado."
  git rev-list --left-right --count "origin/$BR...HEAD" 2>/dev/null \
    | awk '{print "   ahead ahora = "$2" (debe ser 0)"}'
else
  echo "❌ PUSH FALLÓ (código $RC). Copia el mensaje de arriba y pégalo en el chat."
fi

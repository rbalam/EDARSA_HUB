#!/usr/bin/env bash
set -e

cd /app

echo "===== RAMA ====="
BRANCH="$(git branch --show-current)"
echo "$BRANCH"
test "$BRANCH" = "Edarsahub_Desarrollo"

echo
echo "===== STATUS ====="
git status --short

echo
echo "===== ARCHIVOS AGENTES ====="
find .github/agents .github/instructions .agents/rules .agents/skills scripts/agent_guardrails -maxdepth 4 -type f | sort

echo
echo "===== CLAUDE MINIMIZADO ====="
if [ -d ".claude/agents" ]; then
  BAD_CLAUDE_FILES="$(find .claude/agents -type f ! -path ".claude/agents/edarsa-claude-haiku-auditor.md" | sort | head -50)"
  if [ -n "$BAD_CLAUDE_FILES" ]; then
    echo "ERROR: .claude/agents solo permite .claude/agents/edarsa-claude-haiku-auditor.md"
    echo "$BAD_CLAUDE_FILES"
    exit 1
  fi
fi
echo "OK: .claude/agents limitado a auditor Claude Haiku controlado"

echo
echo "===== BLOQUEOS DE REGLAS OBSOLETAS ====="
if grep -RIn "Sales KPI = \`ventas_sin_propina\`" .github/agents .agents AGENTS.md .github/instructions 2>/dev/null; then
  echo "BLOQUEADO: regla obsoleta detectada: Sales KPI = ventas_sin_propina"
  exit 1
fi

if grep -RInE "tools:.*edit.*auditor|tools:.*todo.*auditor" .github/agents 2>/dev/null; then
  echo "BLOQUEADO: auditor con tools edit/todo"
  exit 1
fi

echo "OK: no se detectaron reglas obsoletas criticas"

echo
echo "===== GREP REGLAS CLAVE ====="
grep -RInE "ventas_total|unidad_negocio_pk|Unidades_Negocio|MongoDB|RBAC|Edarsahub_Desarrollo|Copilot Supervisor" \
  AGENTS.md .github .agents scripts/agent_guardrails | head -240

echo
echo "===== DIFF CHECK ====="
git diff --check

echo
echo "OK: agent setup validado"

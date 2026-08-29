#!/usr/bin/env bash
# =============================================================================
# reporte_git_vs_github.sh
# Muestra TODO lo que GitHub NO puede ver del pod: cambios sin commitear,
# archivos sin trackear, archivos ignorados (.gitignore), divergencia con el
# remoto y stashes. Pega la salida completa en el chat.
# Uso:  bash /app/reporte_git_vs_github.sh
# =============================================================================
set -uo pipefail
cd /app 2>/dev/null || { echo "No existe /app"; exit 1; }

line(){ printf '\n\033[1m===== %s =====\033[0m\n' "$*"; }

line "0. CONTEXTO"
echo "Fecha:        $(date -u '+%Y-%m-%d %H:%M:%SZ')"
echo "Remoto:       $(git remote get-url origin 2>/dev/null || echo '(sin remoto)')"
echo "Rama local:   $(git branch --show-current 2>/dev/null)"
echo "HEAD local:   $(git rev-parse --short HEAD 2>/dev/null)"

line "1. DIVERGENCIA CON GITHUB (fetch)"
git fetch --quiet origin 2>/dev/null && echo "(fetch OK)" || echo "(fetch FALLÓ - revisa credenciales/red)"
BR="$(git branch --show-current 2>/dev/null)"
if git rev-parse --verify -q "origin/$BR" >/dev/null 2>&1; then
  read -r behind ahead < <(git rev-list --left-right --count "origin/$BR...HEAD" 2>/dev/null | awk '{print $1" "$2}')
  echo "Commits que GitHub tiene y el pod NO (behind): ${behind:-?}"
  echo "Commits que el pod tiene y GitHub NO  (ahead):  ${ahead:-?}"
  if [ "${ahead:-0}" -gt 0 ] 2>/dev/null; then
    echo "--- Commits locales NO subidos a GitHub: ---"
    git log --oneline "origin/$BR..HEAD" 2>/dev/null | head -50
  fi
else
  echo "No existe origin/$BR (rama no publicada en GitHub)."
fi

line "2. CAMBIOS SIN COMMITEAR (working tree sucio)"
echo "Staged (listos para commit):"
git diff --cached --name-status 2>/dev/null | head -200
echo "--- Modificados NO staged: ---"
git diff --name-status 2>/dev/null | head -200
echo "(resumen)"; git diff --shortstat 2>/dev/null; git diff --cached --shortstat 2>/dev/null

line "3. ARCHIVOS SIN TRACKEAR (existen en el pod, NO en git)"
git ls-files --others --exclude-standard 2>/dev/null | head -300
echo "Total sin trackear: $(git ls-files --others --exclude-standard 2>/dev/null | wc -l)"

line "4. ARCHIVOS IGNORADOS POR .gitignore (nunca llegan a GitHub)"
git ls-files --others --ignored --exclude-standard 2>/dev/null | sed 's|/[^/]*$||' | sort | uniq -c | sort -rh | head -40
echo "Total ignorados: $(git ls-files --others --ignored --exclude-standard 2>/dev/null | wc -l)"

line "5. STASHES (trabajo guardado fuera de commits)"
git stash list 2>/dev/null | head -30
echo "Total stashes: $(git stash list 2>/dev/null | wc -l)"

line "6. WORKTREES ADICIONALES"
git worktree list 2>/dev/null

line "7. TOP 15 ARCHIVOS SIN TRACKEAR MÁS GRANDES"
git ls-files --others --exclude-standard 2>/dev/null | xargs -r du -h 2>/dev/null | sort -rh | head -15

line "FIN DEL REPORTE"
echo "Copia TODO lo anterior y pégalo en el chat."

# EDARSAHUB V1.0 — instrucciones globales para GitHub Copilot / VS Code

Usar `AGENTS.md` como contrato principal del repositorio.

Prioridad operativa:
1. Antigravity
2. Codex
3. GitHub Copilot / VS Code
4. Claude minimizado

Agentes Copilot disponibles:
- EDARSA Copilot Supervisor: coordina, no edita.
- EDARSA Auditor: audita, no edita.
- EDARSA Coder: implementa cambios minimos.
- EDARSA Validator: valida y bloquea.

No crear `.claude/agents` excepto `.claude/agents/edarsa-claude-haiku-auditor.md`, permitido solo como auditor Claude Haiku de solo lectura, uso excepcional y bajo autorización explícita.

Reglas críticas:
- Rama obligatoria: `Edarsahub_Desarrollo`.
- No tocar producción.
- No push/deploy sin autorización explícita.
- No MongoDB en módulos críticos.
- No conexiones live para endpoints/tableros/reportes.
- No mocks.
- No hardcodes.
- No fuentes paralelas.
- No tocar RBAC ni debilitarlo.
- No patch sin evidencia exacta.
- DB solo `SELECT` para auditorías.
- KPI Ventas = `ventas_total` con IVA.
- Unidad de negocio: fuente `dbo.Unidades_Negocio`, llave `unidad_negocio_pk`.

## EDARSA Committer

- EDARSA Committer: crea commits locales solo despues de Validator APROBADO.
- No hace push.
- No deploy.
- No Produccion.
- No reset.
- No checkout destructivo.

## Flujo autonomo

Usar cadena:

`Supervisor -> Auditor -> Coder -> Validator -> Committer -> Supervisor`

Cada agente debe terminar con bloque `HANDOFF`.

<!-- EDARSAHUB_ATOMIC_WORKFLOW_START -->

## MÁXIMA DE ORO — CAMBIOS ATÓMICOS Y BASE ESTABLE

1. Trabajar sobre una rama, HEAD y workspace verificados.
2. Un bloque de trabajo corresponde a un solo objetivo funcional.
3. No mezclar dominios ni restaurar masivamente stashes, recoveries o worktrees.
4. Si existía una versión funcional, recuperarla y comparar antes de crear lógica nueva.
5. No parchar sin evidencia exacta de la causa.
6. Modificar únicamente los archivos declarados en el alcance.
7. Validar el dominio antes de ampliar el trabajo.
8. No incorporar respaldos, dumps, archivos temporales ni salidas de herramientas.
9. Commit, push, deploy y SQL requieren autorización expresa.
10. Ante una condición inesperada, detenerse y reportar; no improvisar.

Documento normativo:
`docs/operacion/MODO_TRABAJO_CAMBIOS_ATOMICOS.md`

<!-- EDARSAHUB_ATOMIC_WORKFLOW_END -->

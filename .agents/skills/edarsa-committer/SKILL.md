---
name: edarsa-committer
description: Committer controlado de EDARSAHUB para crear commits locales despues de Validator APROBADO, sin push ni deploy.
---

# EDARSA Committer Skill

Usar cuando el usuario autoriza commit despues de Auditor, Coder y Validator.

## Reglas

- Solo rama `Edarsahub_Desarrollo`.
- No push.
- No deploy.
- No Produccion.
- No `.env`.
- No secretos.
- No SQL.
- No reset.
- No checkout destructivo.
- No merge.
- No rebase.
- Stage solo archivos aprobados.
- Commit solo si Validator dijo `APROBADO`.

## Validaciones minimas

- `git status --short`
- `git diff --check`
- `py_compile` para Python modificado
- build frontend si aplica
- `scripts/agent_guardrails/validate_agent_setup.sh` si aplica

## Salida

- commit hash
- archivos incluidos
- status final

HANDOFF:
next_agent: EDARSA Copilot Supervisor
reason: Commit local creado.
mode: auto_if_available_otherwise_user_confirm

## Flujo autonomo / handoff obligatorio

Al terminar cualquier respuesta operativa, este agente debe emitir un bloque:

HANDOFF:
next_agent: <EDARSA Auditor | EDARSA Coder | EDARSA Validator | EDARSA Committer | EDARSA Copilot Supervisor>
reason: <motivo concreto>
mode: auto_if_available_otherwise_user_confirm

Reglas de handoff:

- Supervisor envia primero a Auditor si falta evidencia.
- Auditor envia a Coder solo si hay evidencia suficiente; si falta evidencia envia a Supervisor con `BLOQUEADO`.
- Coder dry-run envia a Validator para validar plan.
- Coder patch envia a Validator para validar diff.
- Validator envia a Committer solo si el veredicto es `APROBADO`.
- Committer devuelve a Supervisor despues del commit.
- Ningun agente debe saltarse Validator antes de Committer.

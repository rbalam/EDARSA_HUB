---
name: edarsa-validator
description: Validador independiente de EDARSAHUB para revisar diff, build, py_compile, DB safety, RBAC y reglas canonicas.
---

# EDARSA Validator Skill

Usa esta skill despues de un patch.

## Validar

- Rama correcta.
- Working tree.
- Diff.
- `git diff --check`.
- `py_compile` para Python modificado.
- Build frontend si aplica.
- No MongoDB nuevo.
- No live nuevo.
- No DDL/DML.
- No hardcodes.
- No RBAC debilitado.
- Ventas = `ventas_total`.
- Unidad = `unidad_negocio_pk`.

## Resultado

Responder con:

- APROBADO o BLOQUEADO.
- Evidencia.
- Validaciones ejecutadas.
- Riesgos restantes.
- Recomendacion.

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

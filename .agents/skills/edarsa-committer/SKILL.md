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

## Recalibración obligatoria SQL, secretos y handoff

Reglas estrictas adicionales:

- No usar `dotenv`.
- No llamar `load_dotenv`.
- No abrir `/app/.env`.
- No abrir `/app/backend/.env`.
- No imprimir variables de entorno.
- No ejecutar `printenv`.
- No ejecutar `env`.
- No ejecutar `cat .env`.
- No probar conexiones directas con `get_sql_connection` salvo autorización explícita del usuario.
- Si se requiere SQL, pedir autorización y entregar primero un script SELECT revisable.
- SQL permitido solo `SELECT`; prohibido `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `MERGE`.
- No leer scripts sueltos de reparación/migración como `fix_*.py`, `*_sql.py`, `migration*.py` o `scripts_pendientes` salvo que el usuario los autorice explícitamente.
- No salir del alcance de archivos indicado por el usuario.

Formato HANDOFF obligatorio:

El último bloque de toda respuesta operativa debe ser exactamente:

HANDOFF:
next_agent: <EDARSA Auditor | EDARSA Coder | EDARSA Validator | EDARSA Committer | EDARSA Copilot Supervisor>
reason: <motivo concreto>
mode: auto_if_available_otherwise_user_confirm

Reglas del HANDOFF:

- No usar `NEXT AGENT` como sustituto.
- No usar `STATUS: Ready for Validator` como sustituto.
- No poner texto después del bloque `HANDOFF`.
- Si falta `HANDOFF` exacto, el siguiente Validator debe marcar `BLOQUEADO`.

## Candado obligatorio antes de commit

El Committer debe:

1. Stagear únicamente los archivos explícitamente aprobados por Validator.
2. No usar `git add .`, `git add -A` ni `git add --all`.
3. Después del stage y antes del commit ejecutar:

   `scripts/agent_guardrails/validate_repository_artifacts.py --staged`

4. Abortará el commit si el guard no devuelve `PASS`.
5. No puede usar `--no-verify` para evadir esta política.
6. No puede crear una excepción al límite de artefactos por decisión propia.
7. Una excepción requiere autorización explícita, evidencia y revisión del
   Validator.

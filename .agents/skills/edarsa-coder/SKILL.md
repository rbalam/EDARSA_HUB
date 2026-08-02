---
name: edarsa-coder
description: Implementador controlado de EDARSAHUB para aplicar patches minimos despues de evidencia del auditor.
---

# EDARSA Coder Skill

Usa esta skill solo cuando el usuario autorice implementar.

## Reglas

- Cambios minimos.
- No tocar produccion.
- No push/deploy.
- No crear tablas/columnas/migraciones sin autorizacion.
- No mocks.
- No hardcodes.
- No MongoDB.
- No live para endpoints/tableros/reportes.
- No debilitar RBAC.

## Comercial

- Ventas = `ventas_total` con IVA.
- Unidad = `unidad_negocio_pk`.
- Fuente = `dbo.Unidades_Negocio`.
- Backend calcula KPIs.

## Despues del patch

- Mostrar diff.
- Ejecutar validaciones.
- Reportar riesgos.

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

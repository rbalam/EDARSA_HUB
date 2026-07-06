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

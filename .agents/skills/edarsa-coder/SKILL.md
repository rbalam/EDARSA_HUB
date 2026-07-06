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

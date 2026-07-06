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

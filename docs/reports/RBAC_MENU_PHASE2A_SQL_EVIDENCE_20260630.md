# Fase 2A - Evidencia SQL recibida

## Fuente

Reporte pegado desde el entorno Emergent/VSCode:

```text
docs/reports/sql_runner_logs/20260630_073332_validate_phase2_rbac_empty_roles_impact_audit.md
```

El archivo original no estaba versionado en este workspace local de Codex. Esta nota captura solo el resumen operativo necesario, sin copiar usuarios, correos ni nombres personales.

## Resultado

- Fecha de ejecucion: 2026-06-30 07:33:32.
- Modo: `validate`.
- Base de datos: `EDARSAHUB`.
- Script: `backend/database/validation/phase2_rbac_empty_roles_impact_audit.sql`.
- Resultado: OK.
- Batches ejecutados: 6.

## Hallazgos

- Roles activos sin permisos permitidos: 8.
- Roles vacios detectados: `COMPRAS`, `CRM_ADMIN`, `CRM_AUDIT`, `CRM_EJEC`, `GERENTE`, `TESORERIA`, `USUARIO`, `VENTAS`.
- Usuarios activos asignados a esos roles: 0.
- Usuarios activos que dependan solo de roles vacios: 0.
- Mapeos legacy: todos `OK`.
- Recomendacion para los 8 roles: `BAJO_SIN_USUARIOS_ACTIVOS`.

## Decision derivada

La correccion `USUARIO -> OPERADOR` dejo a `OPERADOR` con 3 usuarios activos y 28 permisos permitidos, y a `USUARIO` sin usuarios activos asignados. Con Fase 2A confirmada, se puede desactivar de forma controlada el conjunto de roles vacios sin usuarios activos.

Ejecutar:

```bash
export EDARSAHUB_ALLOW_MIGRATIONS=true
python backend/tools/edarsahub_sql_runner.py \
  --mode migrate \
  --script backend/database/migrations/20260630_011_desactivar_roles_vacios_sin_usuarios_rbac.sql
```

Validar:

```bash
python backend/tools/edarsahub_sql_runner.py \
  --mode validate \
  --script backend/database/validation/phase2d_rbac_empty_roles_inactive_post_validation.sql
```

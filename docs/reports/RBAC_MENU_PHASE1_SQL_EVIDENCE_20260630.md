# Fase 1 - Evidencia SQL recibida

## Fuente

Reporte pegado desde el entorno Emergent/VSCode:

```text
docs/reports/sql_runner_logs/20260630_065814_validate_phase1_rbac_menu_seed_audit.md
```

El archivo original no estaba versionado en este workspace local de Codex. Esta nota captura solo el resumen operativo necesario, sin copiar usuarios, correos ni nombres personales.

## Resultado

- Fecha de ejecucion: 2026-06-30 06:58:14.
- Modo: `validate`.
- Base de datos: `EDARSAHUB`.
- Script: `backend/database/validation/phase1_rbac_menu_seed_audit.sql`.
- Resultado: OK.
- Batches ejecutados: 12.

## Conteos principales

- `Usuario_Catalogo`: 22 registros, 12 activos.
- `Usuario_Roles`: 23 registros, 23 activos.
- `Usuario_Modulos`: 61 registros, 61 activos, 56 visibles en menu.
- `Usuario_Acciones`: 20 registros, 20 activos.
- `Usuario_RolesAsignacion`: 37 registros, 22 activos.
- `Usuario_PermisosRolModulo`: 608 registros, 445 activos y permitidos.

## Hallazgos

- Usuarios activos sin rol activo: 0.
- Roles activos sin permisos permitidos: 8.
- Roles vacios detectados: `COMPRAS`, `CRM_ADMIN`, `CRM_AUDIT`, `CRM_EJEC`, `GERENTE`, `TESORERIA`, `USUARIO`, `VENTAS`.
- El preview del reporte muestra usuarios activos asignados al rol `USUARIO`, que esta entre los roles vacios.

## Decision derivada

La Fase 2A debe ejecutarse antes de la validacion API 2B. La razon es que la API puede reflejar correctamente permisos vacios si los usuarios activos dependen solo de roles vacios. Primero se debe clasificar el impacto con:

```bash
python backend/tools/edarsahub_sql_runner.py \
  --mode validate \
  --script backend/database/validation/phase2_rbac_empty_roles_impact_audit.sql
```

Solo despues de confirmar cero casos `CRITICO_SOLO_ROLES_VACIOS` conviene ejecutar `backend/tools/validate_rbac_menu_phase1.py --strict` contra usuarios reales.

# Fase 2 - API real y roles vacios

## Objetivo

Cerrar la validacion operativa despues de la Fase 1 SQL:

- Ejecutar `validate_rbac_menu_phase1.py` contra usuarios reales.
- Revisar si los 8 roles activos sin permisos afectan usuarios reales.
- Bloquear el paso a produccion si existe algun usuario activo cuyo acceso depende solo de roles vacios.
- Preparar la decision posterior sobre el fallback visual por rol legacy en `frontend/src/pages/Layout.js`.

## Entrada desde Fase 1

La validacion SQL reportada en Emergent/VSCode paso correctamente y dejo un hallazgo:

- 23 roles activos con conteo de permisos.
- 12 usuarios activos con roles asignados.
- 0 usuarios activos sin rol activo.
- 8 roles activos sin permisos permitidos: `COMPRAS`, `CRM_ADMIN`, `CRM_AUDIT`, `CRM_EJEC`, `GERENTE`, `TESORERIA`, `USUARIO`, `VENTAS`.
- El preview del reporte muestra usuarios activos asignados al rol `USUARIO`.

Esto cambia la prioridad: antes de validar API por usuarios reales, confirmar si esos usuarios tienen solo `USUARIO` o si tambien tienen otro rol con permisos. Si tienen solo `USUARIO`, el hallazgo es critico para produccion porque el endpoint de permisos efectivos puede quedar vacio correctamente, reflejando una semilla RBAC incompleta.

Nota tecnica: el mapeo legacy del backend no usa `USUARIO` como destino para el rol legacy `Usuario`; usa `OPERADOR`. Por eso el rol `USUARIO` vacio afecta sobre todo a usuarios con asignacion SQL directa a `USUARIO`, no al fallback legacy `Usuario -> OPERADOR`.

## Validacion 2A - Impacto de roles vacios

Ejecutar:

```bash
python backend/tools/edarsahub_sql_runner.py \
  --mode validate \
  --script backend/database/validation/phase2_rbac_empty_roles_impact_audit.sql
```

Interpretacion:

- `CRITICO_SOLO_ROLES_VACIOS`: usuario activo quedaria sin permisos efectivos por RBAC SQL.
- `REVISAR_ROL_VACIO_SECUNDARIO`: usuario tiene al menos un rol vacio, pero tambien tiene rol con permisos.
- `BAJO_SIN_USUARIOS_ACTIVOS`: rol vacio no esta asignado a usuarios activos.
- `CRITICO_ROL_DESTINO_SIN_PERMISOS`: un rol usado por mapeo legacy no tiene permisos y puede romper fallback legacy-to-SQL.

Criterio para avanzar:

- Cero usuarios con `CRITICO_SOLO_ROLES_VACIOS`.
- Cero mapeos legacy con `CRITICO_ROL_DESTINO_NO_EXISTE`.
- Cero mapeos legacy con `CRITICO_ROL_DESTINO_SIN_PERMISOS`.

Si aparece `CRITICO_SOLO_ROLES_VACIOS`, resolver datos RBAC antes de ejecutar 2B: poblar permisos del rol, reasignar el usuario a un rol con permisos, o desactivar el rol vacio si es obsoleto y no debe usarse.

## Correccion aprobada - USUARIO a OPERADOR

Decision tomada: los usuarios activos asignados al rol vacio `USUARIO` deben pasar a `OPERADOR`.

Ejecutar en modo migracion:

```bash
export EDARSAHUB_ALLOW_MIGRATIONS=true
python backend/tools/edarsahub_sql_runner.py \
  --mode migrate \
  --script backend/database/migrations/20260630_010_reasignar_usuario_a_operador_rbac.sql
```

Despues validar:

```bash
python backend/tools/edarsahub_sql_runner.py \
  --mode validate \
  --script backend/database/validation/phase2c_rbac_usuario_operador_post_validation.sql
```

Resultado esperado:

- `USUARIO` sin asignaciones activas de usuarios activos.
- `OPERADOR` con permisos permitidos activos.
- Cero filas en `USUARIO_ACTIVO_CON_ROL_USUARIO_ACTIVO`.
- Cero filas en `USUARIO_ACTIVO_SIN_OPERADOR_TRAS_MIGRACION`.

## Validacion 2B - API con usuarios reales

Preparar usuarios reales o QA por perfil. No guardar passwords en el repo.

```bash
export EDARSAHUB_API_URL="http://localhost:8001"
export RBAC_PHASE1_USERS_JSON='[
  {
    "label": "SuperAdministrador",
    "email": "qa.superadmin@edarsa.com",
    "password": "CAMBIAR",
    "expect_global_access": true,
    "expected_min_permissions": 1
  },
  {
    "label": "Administrador",
    "email": "qa.admin@edarsa.com",
    "password": "CAMBIAR",
    "expect_global_access": true,
    "expected_min_permissions": 1
  },
  {
    "label": "Supervisor",
    "email": "qa.supervisor@edarsa.com",
    "password": "CAMBIAR",
    "expected_min_permissions": 1
  },
  {
    "label": "UsuarioLimitado",
    "email": "qa.limitado@edarsa.com",
    "password": "CAMBIAR",
    "expected_enabled_menus": ["mis_tareas"],
    "expected_disabled_menus": ["usuarios", "servidores", "catalogo_sql"]
  },
  {
    "label": "UsuarioSinPermiso",
    "email": "qa.sinpermiso@edarsa.com",
    "password": "CAMBIAR",
    "expected_enabled_menus": ["mis_tareas"],
    "expected_disabled_menus": ["usuarios", "servidores", "catalogo_sql", "explorador_bd"]
  }
]'

python3 backend/tools/validate_rbac_menu_phase1.py --strict
```

El reporte se genera en:

```text
docs/reports/rbac_phase1/
```

## Gate para produccion

No promover a `Edarsahub_Produccion` hasta tener:

- Reporte SQL Fase 1 OK.
- Reporte SQL Fase 2A sin criticos.
- Migracion `USUARIO -> OPERADOR` aplicada si 2A confirma usuarios activos sobre `USUARIO`.
- Validacion 2C sin hallazgos.
- Migracion de desactivacion de roles vacios sin usuarios activos aplicada.
- Validacion 2D sin roles objetivo activos y sin asignaciones activas sobre esos roles.
- Reporte API Fase 2B sin FAIL/WARN en modo `--strict`.
- Decision tomada sobre roles vacios: poblar permisos, reasignar usuarios, o mantenerlos vacios solo si no afectan usuarios.
- Decision tomada sobre el fallback legacy del menu frontend.

## Nota sobre fallback frontend

`frontend/src/pages/Layout.js` conserva un fallback visual por `user.role` si falla `/auth/me/menu-permissions`. Para produccion, la decision recomendada es endurecerlo: si el endpoint RBAC falla, el menu no debe conceder visibilidad amplia por rol legacy sin evidencia de permisos efectivos.

# Fase 1 - Validacion RBAC/Menu

## Objetivo

Validar que el menu operativo de EDARSAHUB 1.0 se derive de permisos RBAC SQL efectivos y no de permisos visuales inventados en frontend.

La Fase 1 no cambia permisos productivos. Deja una prueba repetible para confirmar:

- `/api/auth/me/effective-permissions` responde desde RBAC SQL canonico.
- `/api/auth/me/menu-permissions` deriva `permisos_modulos` de esos permisos efectivos.
- Los roles reales tienen asignaciones, modulos, acciones y permisos permitidos en SQL.
- El comportamiento esperado se puede validar por perfil: SuperAdministrador, Administrador, Supervisor, Usuario limitado y Usuario sin permiso.

## Scripts agregados

- `backend/tools/validate_rbac_menu_phase1.py`
- `backend/database/validation/phase1_rbac_menu_seed_audit.sql`

## Validacion API

Definir usuarios de prueba con permisos reales. El script no imprime passwords ni tokens.

```bash
export EDARSAHUB_API_URL="http://localhost:8001"
export RBAC_PHASE1_USERS_JSON='[
  {
    "label": "SuperAdministrador",
    "email": "superadmin@empresa.com",
    "password": "CAMBIAR",
    "expect_global_access": true,
    "expected_min_permissions": 1
  },
  {
    "label": "Administrador",
    "email": "admin@empresa.com",
    "password": "CAMBIAR",
    "expected_min_permissions": 1
  },
  {
    "label": "Supervisor",
    "email": "supervisor@empresa.com",
    "password": "CAMBIAR",
    "expected_min_permissions": 1
  },
  {
    "label": "UsuarioLimitado",
    "email": "limitado@empresa.com",
    "password": "CAMBIAR",
    "expected_enabled_menus": ["mis_tareas"],
    "expected_disabled_menus": ["usuarios"]
  },
  {
    "label": "UsuarioSinPermiso",
    "email": "sinpermiso@empresa.com",
    "password": "CAMBIAR",
    "expected_enabled_menus": ["mis_tareas"],
    "expected_disabled_menus": ["usuarios", "servidores", "catalogo_sql"]
  }
]'

python3 backend/tools/validate_rbac_menu_phase1.py --strict
```

El reporte se genera en:

```text
docs/reports/rbac_phase1/
```

Si solo se quiere una prueba local rapida con el admin historico, usar explicitamente:

```bash
export EDARSAHUB_DEFAULT_ADMIN_EMAIL="admin@edarsa.com"
export EDARSAHUB_DEFAULT_ADMIN_PASSWORD="CAMBIAR"
python3 backend/tools/validate_rbac_menu_phase1.py --use-default-admin
```

## Validacion SQL

Ejecutar en modo `validate`, que bloquea cambios de datos y hace rollback al finalizar.

```bash
python3 backend/tools/edarsahub_sql_runner.py \
  --mode validate \
  --script backend/database/validation/phase1_rbac_menu_seed_audit.sql
```

Variables requeridas por el runner:

```bash
export EDARSAHUB_SQL_SERVER="..."
export EDARSAHUB_SQL_DATABASE="..."
export EDARSAHUB_SQL_USER="..."
export EDARSAHUB_SQL_PASSWORD="..."
```

## Criterios de aceptacion

- Login exitoso para los usuarios de prueba.
- `effective-permissions` y `menu-permissions` responden HTTP 200.
- `source` es `RBAC_SQL_CANONICAL_WITH_LEGACY_COMPAT`.
- `permissions_flat` es lista y contiene permisos para roles que no sean "sin permiso".
- `permisos_modulos` es objeto y contiene las llaves del menu operativo.
- `mis_tareas` queda habilitado para todo usuario autenticado.
- Un usuario sin permiso no habilita menus sensibles como `usuarios`, `servidores`, `catalogo_sql` o `explorador_bd`.
- SQL muestra datos activos en `Usuario_Roles`, `Usuario_Modulos`, `Usuario_Acciones`, `Usuario_RolesAsignacion` y `Usuario_PermisosRolModulo`.
- No hay usuarios activos sin rol activo, salvo usuarios deliberadamente creados para el caso "sin permiso".
- No hay roles activos sin permisos permitidos, salvo roles deliberadamente vacios para pruebas controladas.

## Riesgo observado

`frontend/src/pages/Layout.js` todavia contiene un fallback visual por `user.role` cuando falla `/auth/me/menu-permissions`. Ese fallback puede ocultar errores reales del backend durante pruebas manuales.

Decision recomendada despues de ejecutar esta Fase 1: eliminar o endurecer ese fallback para que el menu no conceda visibilidad por rol legacy cuando el endpoint RBAC falle.

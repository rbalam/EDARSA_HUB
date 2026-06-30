# Fase 2C - RBAC/Menu multiusuario

## Estado

- Fecha: 2026-06-30
- Rama: `Edarsahub_Desarrollo`
- Modo SQL usado: `validate`
- Escrituras SQL productivas: ninguna
- Passwords/tokens impresos: ninguno

## Evidencia SQL read-only

Reporte generado:

```text
docs/reports/sql_runner_logs/20260630_101032_validate_phase2c_rbac_menu_multiuser_candidates.md
```

Resumen:

- Roles revisados: 23
- Usuarios activos: 12
- Usuarios activos con hash de login: 11
- Usuarios activos sin rol activo: 0
- Usuarios activos no globales sin permisos efectivos: 0

Roles con usuarios activos y permisos:

- `SUPERADMIN`: 4 usuarios activos, 61 permisos
- `ADMIN`: 3 usuarios activos, 61 permisos
- `SUPERVISOR`: 1 usuario activo, 45 permisos
- `OPERADOR`: usuarios activos detectados, 28 permisos

## Candidatos API sugeridos

Usar usuarios con hash y roles activos:

- `qa.superadmin@edarsa.com` - `SUPERADMIN`
- `carlosruz@edarsa.com.mx` - `ADMIN`
- `noxte@alpyc.com` - `SUPERVISOR`
- `almacen@cienfuegos.mx` - `OPERADOR`

No usar `ewsbaquedano@gmail.com` para API hasta configurar hash de login.

## Runner interactivo

Se agrego:

```text
backend/tools/validate_rbac_menu_phase2c_interactive.py
```

Uso recomendado:

```bash
/app/.venv/bin/python backend/tools/validate_rbac_menu_phase2c_interactive.py --strict
```

El runner:

- Pide passwords por terminal con `getpass`.
- Permite omitir un usuario con Enter.
- No imprime ni guarda passwords.
- Reusa `backend/tools/validate_rbac_menu_phase1.py`.
- Genera reporte redacted en `docs/reports/rbac_phase1/`.

Uso con lista explicita:

```bash
/app/.venv/bin/python backend/tools/validate_rbac_menu_phase2c_interactive.py \
  --strict \
  --user SuperAdministrador:qa.superadmin@edarsa.com:1 \
  --user Administrador:carlosruz@edarsa.com.mx:1 \
  --user Supervisor:noxte@alpyc.com:1 \
  --user Operador:almacen@cienfuegos.mx:1
```

## Bloqueo restante

Para cerrar Fase 2C API real falta capturar passwords de aplicacion por perfil
en una terminal segura. No se deben pegar passwords en reportes, commits ni chat.

## Criterio de cierre

Fase 2C queda cerrada cuando exista un reporte API multiusuario con:

- `login` HTTP 200 para cada perfil validado.
- `/auth/me/effective-permissions` HTTP 200.
- `/auth/me/menu-permissions` HTTP 200.
- `source = RBAC_SQL_CANONICAL_WITH_LEGACY_COMPAT`.
- `OK/WARN/FAIL = N/0/0` bajo `--strict`.

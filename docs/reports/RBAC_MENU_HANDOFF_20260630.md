# RBAC/Menu handoff - 2026-06-30

## Estado

- Rama de trabajo: `Edarsahub_Desarrollo`
- Produccion: no tocada
- Commit publicado en Desarrollo:
  - `0430d0d3 test(rbac): validate admin menu permissions from canonical SQL`
- Push realizado:
  - `origin/Edarsahub_Desarrollo`

## Cambios incluidos

- `frontend/src/components/navigation/EnterpriseSidebarMenu.jsx`
  - El menu Enterprise ya no usa cache local ni fallback visual por rol.
  - Si no llega menu SQL autorizado, no renderiza menu inventado.
- `backend/database/validation/phase2c_rbac_menu_multiuser_candidates.sql`
  - Validacion read-only para roles, usuarios activos, permisos efectivos y candidatos API.
- `backend/tools/reset_admin_password_phase2b.py`
  - Reset controlado de password admin, sin imprimir ni guardar password plano/hash.
- `backend/tools/validate_rbac_menu_phase2c_interactive.py`
  - Validador interactivo multiusuario con `getpass`, sin imprimir ni guardar passwords.
- Evidencia guardada:
  - `docs/reports/rbac_phase1/20260630_100300_rbac_menu_phase1.md`
  - `docs/reports/rbac_phase1/20260630_100300_rbac_menu_phase1.json`
  - `docs/reports/sql_runner_logs/20260630_101032_validate_phase2c_rbac_menu_multiuser_candidates.md`
  - `docs/reports/RBAC_MENU_PHASE2C_MULTIUSER_API.md`

## Validaciones realizadas

- Python compile: OK
  - `backend/server.py`
  - `backend/tools/validate_rbac_menu_phase1.py`
  - `backend/tools/validate_rbac_menu_phase2c_interactive.py`
  - `backend/tools/reset_admin_password_phase2b.py`
- Frontend build: OK
  - `yarn build`
  - Resultado con warnings ESLint preexistentes de hooks.
- API admin validada con `admin@edarsa.com`:
  - login: `200`
  - `/auth/me/effective-permissions`: `200`
  - `/auth/me/menu-permissions`: `200`
  - source: `RBAC_SQL_CANONICAL_WITH_LEGACY_COMPAT`
  - role legacy: `SuperAdministrador`
  - permisos efectivos API: `261`
  - acceso global: `true`

## Usuarios, roles y permisos

Evidencia SQL read-only:

- Roles revisados: `23`
- Usuarios activos: `12`
- Usuarios activos con hash de login: `11`
- Usuarios activos sin rol activo: `0`
- Usuarios activos no globales sin permisos efectivos: `0`

Roles con usuarios activos:

- `SUPERADMIN`: 4 usuarios activos, 61 permisos, OK
- `ADMIN`: 3 usuarios activos, 61 permisos, OK
- `SUPERVISOR`: 1 usuario activo, 45 permisos, OK
- `OPERADOR`: usuarios activos detectados, 28 permisos, OK

Nota:

- `ewsbaquedano@gmail.com` aparece activo con rol `SUPERADMIN`, pero sin hash de login; no usar para validacion API hasta configurar hash.

## Reportes excluidos del commit

- Falsos negativos / intentos con password incorrecto o usuario SQL:
  - `docs/reports/rbac_phase1/20260630_104032_rbac_menu_phase1.*`
  - `docs/reports/rbac_phase1/20260630_103505_rbac_menu_phase1.*`
- Diagnosticos intermedios de fase 2B y logs historicos no necesarios para el commit limpio.
- `Open` esta vacio y debe ignorarse o eliminarse si se limpia el workspace.

## Pendiente al retomar

1. Decidir si se limpian o se conservan los reportes/diagnosticos no trackeados.
2. Si se requiere cierre multiusuario real, ejecutar:

```bash
/app/.venv/bin/python backend/tools/validate_rbac_menu_phase2c_interactive.py --strict
```

3. No pedir passwords por chat; el runner los captura por terminal.
4. No tocar `Edarsahub_Produccion` hasta validar y autorizar promocion desde Desarrollo.
5. Si se quiere promover, revisar primero:

```bash
git status --short --branch
git log --oneline --decorate -5
```

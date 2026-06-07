# Auditoría RBAC Hardcodes — Resumen ejecutivo (código vivo)

Fuente CSV: `docs/reports/AUDITORIA_RBAC_HARDCODES_REPO_20260607_213039.csv`

- TOTAL hits: 399  ·  ALTO: 50  ·  MEDIO: 74  ·  BAJO: 275
- ALTO en runtime real (gates a migrar): **44** en **14** archivos
- ALTO en tooling (migrations/scripts, NO runtime): 6 (ignorar)

## ALTO runtime por archivo (prioridad de migración)

| Archivo | Gates ALTO |
|---|---:|
| `backend/server.py` | 15 |
| `backend/core/security.py` | 5 |
| `backend/core/rbac/middleware.py` | 3 |
| `backend/core/server_registry.py` | 3 |
| `backend/modules/costos_margenes/routes.py` | 3 |
| `backend/modules/costos_margenes/routes_precios.py` | 3 |
| `backend/modules/auth/service.py` | 2 |
| `backend/modules/catalogos/routes.py` | 2 |
| `backend/modules/fase2_operativo/routes/automatizacion_compras_routes.py` | 2 |
| `backend/modules/finanzas/propinas_tpv/routes_sql.py` | 2 |
| `backend/modules/admin_sql/routes.py` | 1 |
| `backend/modules/auth/routes.py` | 1 |
| `backend/modules/comercial/inteligencia_comercial_routes.py` | 1 |
| `backend/modules/rh/service.py` | 1 |

## Criterio

- ALTO = gate de acceso backend por nombre legacy o clave `.get('rol')`.
- Migrar a helper canónico (`es_admin`/`es_supervisor_o_superior`/`get_role_code`) preservando alcance exacto, archivo por archivo + prueba funcional.
- NO tocar copias de backup/auditoría (ya excluidas).
# Sincronizacion Historica de Tablas - Reporte de implementacion

Fecha: 2026-10-09  
Rama: `Edarsahub_Desarrollo`  
Fuente funcional: Prompt Maestro de Implementacion - Sincronizacion Historica de Tablas.

## Estado de certificacion

**CERTIFIED_CODE / NOT_CERTIFIED_OPERATIONAL**

La implementacion de codigo, contratos y build queda certificada en la rama de
Desarrollo. La certificacion operacional queda pendiente exclusivamente de
aplicar y validar las migraciones SQL en EDARSAHUB Desarrollo mediante el canal
canonico `SQL_MIGRATION_DEVELOPMENT`, seguido de canario runtime.

No se declara DONE operacional hasta completar esa evidencia.

## Implementado

- Registry historico metadata-driven sobre `Sistema_Sync_Catalogo`.
- Compatibilidad explicita por `Sistema_Sync_Capacidades`.
- Planner atomico: sistema + unidad/sucursal + conexion + capability + bloque temporal.
- Ledger padre/hijos sobre `Sync_Control_Ejecuciones`.
- Idempotencia, dependencia, orden, retry/backoff, checkpoint, pause, resume y cancel seguro.
- Ejecucion cerrada por WORKER UNIVERSAL V1.2.
- API nativa:
  - `GET /api/sync-historical/catalog`
  - `POST /api/sync-historical/preflight`
  - `POST /api/sync-historical/jobs`
  - `GET /api/sync-historical/jobs`
  - `GET /api/sync-historical/jobs/{parent_id}`
  - `POST /api/sync-historical/jobs/{parent_id}/pause`
  - `POST /api/sync-historical/jobs/{parent_id}/resume`
  - `POST /api/sync-historical/jobs/{parent_id}/cancel`
- UI dedicada `/sync-historical`, sin listas fijas de sistemas, unidades o capabilities.
- Boton de acceso desde Monitor de Sincronizacion.
- Eliminado exclusivamente el bloque embebido
  `Re-sincronizacion Comercial por rango` del Scheduler.
- Conservada la seccion `Re-sincronizacion Manual`.
- Historial persistente, progreso, unidades atomicas y bitacora.
- Registro Enterprise de la nueva ruta.
- Primera capability certificada: `comercial_ventas_cerradas`.
- Rollbacks conservadores y validaciones para las migraciones.

## Protecciones verificadas

- No se modifica `sync_comercial_abiertas_v2`.
- No se crea segundo Worker.
- No se crea catalogo paralelo de sistemas/unidades.
- No se ejecuta SQL desde navegador.
- La API HTTP no ejecuta sincronizacion: persiste y encola.
- Las compatibilidades faltantes fallan cerrado.
- Las sucursales ambiguas o no mapeadas no se seleccionan por inferencia.
- Produccion no fue modificada.

## Quality gates

Ultimo gate determinista sobre SHA
`333bf052cca1b670ab7fc602a9fc3b7ed4204d36`:

- Backend deterministic gate: **PASS**
- Frontend build: **PASS**
- Repository Artifact Guard: **PASS**
- 49 contratos backend del gate historico/legacy: **PASS**
- Navegacion Enterprise: **PASS** dentro del build

El workflow legacy
`centro-control-sync-monitor-p5-runtime-e2e.yml` continua fallando sin jobs
materializados; el patron de fallo existe en multiples commits consecutivos y no
forma parte del gate determinista del nuevo modulo. Debe diagnosticarse por
separado antes de usarlo como evidencia runtime.

## Migraciones pendientes de ejecucion en Desarrollo

Orden obligatorio:

1. `20261009_001_sync_historical_capability_registry.sql`
2. `20261009_002_sync_historical_planner.sql`
3. `20261009_003_sync_historical_first_certified_capability.sql`
4. `20261009_004_sync_logs_canonical_execution_context.sql`

Cada una tiene validacion y rollback versionados.

## Criterio para CERTIFIED_OPERATIONAL

Despues de aplicar migraciones en Desarrollo:

1. Ejecutar todas las validaciones SQL.
2. Confirmar catalogo dinamico no vacio para capabilities certificadas.
3. Confirmar unidades/sucursales resueltas sin ambiguedad.
4. Ejecutar preflight de un rango de un dia en DRY RUN.
5. Crear un job padre de prueba.
6. Confirmar reclamacion por WORKER UNIVERSAL V1.2.
7. Verificar un hijo atomico completo y checkpoint.
8. Probar pause/resume.
9. Probar cancel seguro en limite atomico.
10. Probar reintento solo de fallidos.
11. Verificar bitacora e historial tras F5/reconexion.
12. Confirmar que `sync_comercial_abiertas_v2` permanece intacto.

Solo despues de esos pasos el estado puede cambiar a
**CERTIFIED_OPERATIONAL / DONE**.

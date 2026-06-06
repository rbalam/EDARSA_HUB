# VALIDACIÓN PORTAL INTELIGENCIA COMERCIAL FASE 1

Generado: 2026-06-02T20:07:06+00:00

## Objetivo

Validar que Inteligencia Comercial Fase 1 opera con EDARSAHUB SQL y sin conexión live en dashboard.

## Archivos backend detectados

```text
/app/backend/core/scheduler/jobs/__pycache__/inteligencia_comercial_status_job.cpython-311.pyc
/app/backend/core/scheduler/jobs/__pycache__/inteligencia_comercial_sync_job.cpython-311.pyc
/app/backend/core/scheduler/jobs/inteligencia_comercial_status_job.py
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py
/app/backend/database/diagnostics/002_diagnostico_inteligencia.sql
/app/backend/database/diagnostics/018_validacion_rbac_inteligencia_comercial.sql
/app/backend/database/migrations/009_crear_inteligencia_comercial_vistas_tablas.sql
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql
/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql
/app/backend/database/migrations/021_permisos_inteligencia_comercial.sql
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql
/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql
/app/backend/database/migrations/032_validacion_inteligencia_comercial_fase1.sql
/app/backend/modules/comercial/__pycache__/inteligencia_comercial_routes.cpython-311.pyc
/app/backend/modules/comercial/__pycache__/inteligencia_repository.cpython-311.pyc
/app/backend/modules/comercial/inteligencia_comercial_routes.py
/app/backend/modules/comercial/inteligencia_repository.py
/app/backend/modules/edge/auditoria_inteligencia_operativa.py
/app/backend/modules/inteligencia_comercial
/app/backend/scripts/seed_inteligencia_demo.py
/app/backend/sql/inteligencia_comercial_validacion_fuentes.sql
/app/backend/sql/inteligencia_comercial_validacion_status_sp.sql
```

## Endpoints registrados

```text
/app/backend/modules/comercial/inteligencia_comercial_routes.py:9:- Usa SP canónico: Sp_Validar_Inteligencia_Comercial_Status
/app/backend/modules/comercial/inteligencia_comercial_routes.py:104:def _require_permission(current_user: Dict[str, Any], permission: str = "INTELIGENCIA_COMERCIAL_VER") -> None:
/app/backend/modules/comercial/inteligencia_comercial_routes.py:121:    if permissions and permission.upper() not in permissions and "INTELIGENCIA_COMERCIAL_ADMIN" not in permissions:
/app/backend/modules/comercial/inteligencia_comercial_routes.py:333:    Fuente: dbo.Sp_Validar_Inteligencia_Comercial_Status (SP canónico)
/app/backend/modules/comercial/inteligencia_comercial_routes.py:338:    rows = _exec_sp("Sp_Validar_Inteligencia_Comercial_Status")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:341:        "source": "Sp_Validar_Inteligencia_Comercial_Status",
/app/backend/modules/comercial/inteligencia_repository.py:20:    - Sp_Validar_Inteligencia_Comercial_Status
/app/backend/modules/comercial/inteligencia_repository.py:165:            EXEC dbo.Sp_Validar_Inteligencia_Comercial_Status
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:19:- `/api/comercial/inteligencia/*`
/app/backend/modules/inteligencia_comercial/routes.py:10:- Vista consolidada: View_Inteligencia_Comercial
/app/backend/modules/inteligencia_comercial/routes.py:563:# Fuente: View_Inteligencia_Comercial (Sync_Sales + Products)
/app/backend/modules/inteligencia_comercial/routes.py:574:    Fuente: View_Inteligencia_Comercial (JOIN Sync_Sales + Products)
/app/backend/modules/inteligencia_comercial/routes.py:597:            FROM View_Inteligencia_Comercial
/app/backend/modules/inteligencia_comercial/routes.py:607:            "_source": "SQL_VIEW_INTELIGENCIA_COMERCIAL",
/app/backend/modules/inteligencia_comercial/routes.py:639:    Si View_Inteligencia_Comercial está vacía, usa catálogo + proporción.
/app/backend/scripts/seed_inteligencia_demo.py:97:    cursor.execute("SELECT COUNT(*) as total FROM View_Inteligencia_Comercial")
/app/backend/scripts/seed_inteligencia_demo.py:99:    print(f"✅ View_Inteligencia_Comercial ahora tiene {total_vista} registros")
/app/backend/scripts/seed_ventas_consolidadas.py:93:        cursor.execute("SELECT TOP 5 * FROM View_Inteligencia_Comercial")
/app/backend/scripts/seed_ventas_consolidadas.py:95:        print(f"\n=== View_Inteligencia_Comercial ({len(rows)} filas de muestra) ===")
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:9646:-- VISTA: [dbo].[View_Inteligencia_Comercial]
/app/backend/static/EDARSAHUB_SCHEMA_COMPLETO.sql:9648:CREATE   VIEW View_Inteligencia_Comercial
/app/backend/server.py:514:# Fuente: EDARSAHUB (View_Inteligencia_Comercial, Fact_Ventas_Consolidadas)
/app/backend/server.py:517:from modules.inteligencia_comercial.routes import router as inteligencia_router
/app/backend/server.py:523:# Endpoints: /api/comercial/inteligencia/*
/app/backend/server.py:526:from modules.comercial.inteligencia_comercial_routes import router as inteligencia_comercial_fase1_router
/app/backend/server.py:527:api_router.include_router(inteligencia_comercial_fase1_router)
/app/backend/sql/inteligencia_comercial_validacion_status_sp.sql:5:CREATE OR ALTER PROCEDURE dbo.Sp_Validar_Inteligencia_Comercial_Status
/app/backend/database/diagnostics/018_validacion_rbac_inteligencia_comercial.sql:2:   VALIDACIÓN FINAL RBAC INTELIGENCIA_COMERCIAL
/app/backend/database/diagnostics/018_validacion_rbac_inteligencia_comercial.sql:9:WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql:2:   ROLLBACK: Eliminar permisos CRM de INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql:12:DECLARE @ModuloID INT = 59; -- INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql:14:-- Eliminar permisos de CRM_ADMIN para INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql:18:PRINT 'Eliminados permisos de CRM_ADMIN para INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql:20:-- Eliminar permisos de CRM_EJEC para INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql:24:PRINT 'Eliminados permisos de CRM_EJEC para INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql:26:-- Eliminar permisos de CRM_AUDIT para INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql:30:PRINT 'Eliminados permisos de CRM_AUDIT para INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/022_rollback_permisos_crm_inteligencia.sql:44:PRINT 'Rollback completado. Permisos CRM eliminados de INTELIGENCIA_COMERCIAL.';
/app/backend/database/migrations/021_permisos_inteligencia_comercial.sql:2:   ASIGNAR PERMISOS INTELIGENCIA_COMERCIAL EN Usuario_PermisosRolModulo
/app/backend/database/migrations/021_permisos_inteligencia_comercial.sql:16:WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/021_permisos_inteligencia_comercial.sql:20:    PRINT 'ERROR: Módulo INTELIGENCIA_COMERCIAL no existe.';
/app/backend/database/migrations/021_permisos_inteligencia_comercial.sql:110:    'PERMISOS_INTELIGENCIA_COMERCIAL' AS resultado,
/app/backend/database/migrations/021_permisos_inteligencia_comercial.sql:119:WHERE m.CodigoModulo = 'INTELIGENCIA_COMERCIAL'
/app/backend/database/migrations/021_permisos_inteligencia_comercial.sql:122:PRINT 'Permisos de INTELIGENCIA_COMERCIAL asignados correctamente.';
/app/backend/database/migrations/032_validacion_inteligencia_comercial_fase1.sql:3:   Archivo: 032_validacion_inteligencia_comercial_fase1.sql
/app/backend/database/migrations/032_validacion_inteligencia_comercial_fase1.sql:37:    'Sp_Validar_Inteligencia_Comercial_Status',
/app/backend/database/migrations/032_validacion_inteligencia_comercial_fase1.sql:127:EXEC dbo.Sp_Validar_Inteligencia_Comercial_Status;
/app/backend/database/migrations/032_validacion_inteligencia_comercial_fase1.sql:138:WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/032_validacion_inteligencia_comercial_fase1.sql:147:WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/032_validacion_inteligencia_comercial_fase1.sql:167:    'INTELIGENCIA_COMERCIAL_FASE1_OPERATIVA' AS resultado,
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:3:   Script: 010_crear_rbac_roles_inteligencia_comercial.sql
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:107:        'INTELIGENCIA_COMERCIAL_VER',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:108:        'INTELIGENCIA_COMERCIAL_EXPORTAR',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:109:        'INTELIGENCIA_COMERCIAL_CONFIGURAR',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:110:        'INTELIGENCIA_COMERCIAL_SYNC',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:111:        'INTELIGENCIA_COMERCIAL_ADMIN'
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:142:        'INTELIGENCIA_COMERCIAL_VER',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:143:        'INTELIGENCIA_COMERCIAL_EXPORTAR',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:144:        'INTELIGENCIA_COMERCIAL_CONFIGURAR',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:145:        'INTELIGENCIA_COMERCIAL_SYNC',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:146:        'INTELIGENCIA_COMERCIAL_ADMIN'
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:177:        'INTELIGENCIA_COMERCIAL_VER',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:178:        'INTELIGENCIA_COMERCIAL_EXPORTAR'
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:209:        'INTELIGENCIA_COMERCIAL_VER',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:210:        'INTELIGENCIA_COMERCIAL_EXPORTAR'
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:241:        'INTELIGENCIA_COMERCIAL_VER'
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:272:        'INTELIGENCIA_COMERCIAL_VER',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:273:        'INTELIGENCIA_COMERCIAL_CONFIGURAR',
/app/backend/database/migrations/010_crear_rbac_roles_inteligencia_comercial.sql:274:        'INTELIGENCIA_COMERCIAL_SYNC'
/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql:2:   MIGRACIÓN: Registrar Módulo INTELIGENCIA_COMERCIAL y
/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql:9:-- BLOQUE 1: Registrar módulo INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql:14:    WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL'
/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql:32:        'INTELIGENCIA_COMERCIAL',
/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql:45:    PRINT 'Módulo INTELIGENCIA_COMERCIAL registrado correctamente.';
/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql:49:    PRINT 'Módulo INTELIGENCIA_COMERCIAL ya existe - sin cambios.';
/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql:277:    'MODULO_INTELIGENCIA_COMERCIAL' AS verificacion,
/app/backend/database/migrations/017_registrar_inteligencia_comercial_y_transicionales.sql:280:WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/023a_crear_roles_comerciales.sql:2:   EDARSAHUB - Crear Roles Comerciales para INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql:7:   1. Validar módulo INTELIGENCIA_COMERCIAL.
/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql:85:       1. Obtener módulo INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql:92:    WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql:95:        THROW 51000, 'No existe el módulo INTELIGENCIA_COMERCIAL en Usuario_Modulos.', 1;
/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql:204:       5. Desactivar permisos actuales de INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql:312:                'RBAC INTELIGENCIA_COMERCIAL: matriz canónica aplicada. Roles CRM excluidos. Fecha: ',
/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql:327:    PRINT 'RBAC INTELIGENCIA_COMERCIAL aplicado correctamente.';
/app/backend/database/migrations/023_rbac_inteligencia_comercial_matriz_ideal.sql:337:    PRINT 'ERROR aplicando RBAC INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/008_crear_sistema_rbac_tablas.sql:73:    SELECT 'INTELIGENCIA_COMERCIAL_VER' AS codigo, 'Ver Inteligencia Comercial' AS nombre, 'Comercial' AS modulo
/app/backend/database/migrations/008_crear_sistema_rbac_tablas.sql:74:    UNION ALL SELECT 'INTELIGENCIA_COMERCIAL_EXPORTAR', 'Exportar Inteligencia Comercial', 'Comercial'
/app/backend/database/migrations/008_crear_sistema_rbac_tablas.sql:75:    UNION ALL SELECT 'INTELIGENCIA_COMERCIAL_CONFIGURAR', 'Configurar Inteligencia Comercial', 'Comercial'
/app/backend/database/migrations/008_crear_sistema_rbac_tablas.sql:76:    UNION ALL SELECT 'INTELIGENCIA_COMERCIAL_SYNC', 'Ejecutar Sincronización Inteligencia Comercial', 'Comercial'
/app/backend/database/migrations/008_crear_sistema_rbac_tablas.sql:77:    UNION ALL SELECT 'INTELIGENCIA_COMERCIAL_ADMIN', 'Administrar Inteligencia Comercial', 'Comercial'
/app/backend/database/migrations/009_crear_inteligencia_comercial_vistas_tablas.sql:3:   Script: 009_crear_inteligencia_comercial_vistas_tablas.sql
/app/backend/database/migrations/009_crear_inteligencia_comercial_vistas_tablas.sql:9:   - SP Sp_Validar_Inteligencia_Comercial_Status
/app/backend/database/migrations/009_crear_inteligencia_comercial_vistas_tablas.sql:87:CREATE OR ALTER PROCEDURE dbo.Sp_Validar_Inteligencia_Comercial_Status
/app/backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql:113:   4. Validar módulo INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql:119:WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';
/app/backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql:123:   5. Validar permisos activos de INTELIGENCIA_COMERCIAL
/app/backend/database/migrations/030_diagnostico_mapeo_rbac_mongo_a_sql.sql:130:WHERE CodigoModulo = 'INTELIGENCIA_COMERCIAL';
/app/backend/core/scheduler/scheduler_manager.py:47:from .jobs.inteligencia_comercial_sync_job import job_inteligencia_comercial_sync
/app/backend/core/scheduler/scheduler_manager.py:774:    async def _run_inteligencia_comercial_sync_job(self):
/app/backend/core/scheduler/scheduler_manager.py:780:        job_config = self.config.jobs.get("inteligencia_comercial_sync")
/app/backend/core/scheduler/scheduler_manager.py:786:        lock = lock_manager.get_lock("inteligencia_comercial_sync")
/app/backend/core/scheduler/scheduler_manager.py:794:        log_entry = await job_logger.start_execution("inteligencia_comercial_sync")
/app/backend/core/scheduler/scheduler_manager.py:800:            result = job_inteligencia_comercial_sync(dias_atras=1)
/app/backend/core/scheduler/scheduler_manager.py:1173:        inteligencia_sync_config = self.config.jobs.get("inteligencia_comercial_sync")
/app/backend/core/scheduler/scheduler_manager.py:1182:                self._run_inteligencia_comercial_sync_job,
/app/backend/core/scheduler/scheduler_manager.py:1184:                id="inteligencia_comercial_sync",
/app/backend/core/scheduler/scheduler_manager.py:1190:            self._jobs["inteligencia_comercial_sync"] = inteligencia_sync_config
/app/backend/core/scheduler/scheduler_manager.py:1191:            logger.info(f"Job INTELIGENCIA_COMERCIAL_SYNC registrado: cron={inteligencia_sync_config.cron_expression or 'interval'}")
/app/backend/core/scheduler/config.py:273:            "inteligencia_comercial_sync": JobConfig(
/app/backend/core/scheduler/config.py:274:                job_id="inteligencia_comercial_sync",
/app/backend/core/scheduler/jobs/inteligencia_comercial_status_job.py:125:def create_inteligencia_comercial_status_job(db, config):
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py:368:        WHERE JobName = 'inteligencia_comercial_sync'
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py:377:def job_inteligencia_comercial_sync(
/app/backend/core/scheduler/jobs/inteligencia_comercial_sync_job.py:478:    result = job_inteligencia_comercial_sync(dias_atras=1)
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:77:<a href="#VIEW_INTELIGENCIA_COMERCIAL">VIEW_INTELIGENCIA_COMERCIAL.sql</a>
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3684:<h2 id="VIEW_INTELIGENCIA_COMERCIAL">📄 VIEW_INTELIGENCIA_COMERCIAL.sql</h2>
/app/frontend/public/SCRIPTS_SQL_CONSOLIDADO_EDARSAHUB.html:3691:CREATE VIEW [dbo].[View_Inteligencia_Comercial] AS
```

## Fuentes SQL canónicas usadas

```text
/app/backend/modules/comercial/service.py:76:# Tablero Ejecutivo lee exclusivamente de Comercial_KPIs_Diarios_v2.
/app/backend/modules/comercial/service.py:91:# FUENTE MAESTRA: Unidades_Negocio.codigo
/app/backend/modules/comercial/service.py:95:_CACHE_UNIDADES_NEGOCIO = None
/app/backend/modules/comercial/service.py:97:def _cargar_catalogo_unidades_negocio() -> Dict:
/app/backend/modules/comercial/service.py:101:    FUENTE MAESTRA: Unidades_Negocio
/app/backend/modules/comercial/service.py:108:    global _CACHE_UNIDADES_NEGOCIO
/app/backend/modules/comercial/service.py:110:    if _CACHE_UNIDADES_NEGOCIO is not None:
/app/backend/modules/comercial/service.py:111:        return _CACHE_UNIDADES_NEGOCIO
/app/backend/modules/comercial/service.py:122:    FROM Unidades_Negocio
/app/backend/modules/comercial/service.py:161:        _CACHE_UNIDADES_NEGOCIO = {
/app/backend/modules/comercial/service.py:167:        logging.info(f"[UNIDADES_NEGOCIO] Catálogo cargado desde EDARSAHUB: {len(result or [])} unidades activas")
/app/backend/modules/comercial/service.py:168:        return _CACHE_UNIDADES_NEGOCIO
/app/backend/modules/comercial/service.py:171:        logging.error(f"[UNIDADES_NEGOCIO] Error cargando catálogo desde EDARSAHUB: {e}")
/app/backend/modules/comercial/service.py:179:    FUENTE MAESTRA: Unidades_Negocio (EDARSAHUB SQL Server)
/app/backend/modules/comercial/service.py:189:    catalogo = _cargar_catalogo_unidades_negocio()
/app/backend/modules/comercial/service.py:202:    logging.warning(f"[UNIDADES_NEGOCIO] No se encontró unidad para server_id={server_id}, sucursal={sucursal}")
/app/backend/modules/comercial/service.py:217:    - Fallback a Unidades_Negocio (EDARSAHUB) si EmpresaResolver no resuelve
/app/backend/modules/comercial/service.py:263:    # Fallback: Buscar en Unidades_Negocio (EDARSAHUB)
/app/backend/modules/comercial/service.py:302:    - Los datos en Comercial_KPIs_Diarios_v2 deben usar códigos canónicos
/app/backend/modules/comercial/service.py:304:    CÓDIGOS CANÓNICOS OFICIALES (según Unidades_Negocio en EDARSAHUB):
/app/backend/modules/comercial/service.py:476:    Fuente: Comercial_KPIs_Diarios_v2 y Comercial_Ventas_Dia_Abiertas_v2.
/app/backend/modules/comercial/service.py:496:    Obtiene el último día con ventas registradas en Comercial_KPIs_Diarios_v2.
/app/backend/modules/comercial/service.py:501:    FROM Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:521:    Obtiene KPIs agregados de Comercial_KPIs_Diarios_v2 para un período.
/app/backend/modules/comercial/service.py:527:    RAZÓN: Para MPRO, los datos en Comercial_KPIs_Diarios_v2 tienen un server_id
/app/backend/modules/comercial/service.py:556:    FROM Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:591:    Obtiene ventas abiertas del día desde Comercial_Ventas_Dia_Abiertas_v2.
/app/backend/modules/comercial/service.py:668:        FROM Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:688:        FROM Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:715:        FROM Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:805:    - Lee de Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:841:    FROM Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:1018:            "tabla": "Comercial_KPIs_Diarios_v2",
/app/backend/modules/comercial/service.py:1035:# - Usar SIEMPRE códigos CANÓNICOS según tabla Unidades_Negocio en EDARSAHUB
/app/backend/modules/comercial/service.py:1184:    - FUENTE MAESTRA: Unidades_Negocio (EDARSAHUB)
/app/backend/modules/comercial/service.py:1196:    # FUENTE MAESTRA: Unidades_Negocio.codigo y Unidades_Negocio.nombre
/app/backend/modules/comercial/service.py:1364:# - Fuente: Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:1375:    - Lee EXCLUSIVAMENTE de EDARSAHUB (Comercial_KPIs_Diarios_v2)
/app/backend/modules/comercial/service.py:1380:    - Obtiene nombre y código canónico desde Unidades_Negocio (EDARSAHUB)
/app/backend/modules/comercial/service.py:1385:    - Lee de Comercial_Ventas_Dia_Abiertas_v2 en EDARSAHUB
/app/backend/modules/comercial/service.py:1392:    # CAMBIO A: Obtener datos canónicos desde Unidades_Negocio (EDARSAHUB)
/app/backend/modules/comercial/service.py:1393:    # FUENTE MAESTRA: Unidades_Negocio.codigo y Unidades_Negocio.nombre
/app/backend/modules/comercial/service.py:1405:        logging.warning(f"[TABLERO-EDARSAHUB] server_id {server_id} no encontrado en Unidades_Negocio EDARSAHUB")
/app/backend/modules/comercial/service.py:1411:    # usados en Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:1418:    # MODO VENTAS DEL DÍA: Leer de Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:1459:                # CAMBIO A: Campos canónicos desde Unidades_Negocio EDARSAHUB
/app/backend/modules/comercial/service.py:1468:    # MODO KPIs HISTÓRICOS/ACUMULADOS: Leer de Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:1492:    # CAMBIO A: Agregar campos canónicos desde Unidades_Negocio EDARSAHUB
/app/backend/modules/comercial/service.py:1505:    - Lee EXCLUSIVAMENTE de EDARSAHUB (Comercial_KPIs_Diarios_v2)
/app/backend/modules/comercial/service.py:1683:    - Ventas del día debe leerse desde Comercial_Ventas_Dia_Abiertas_v2 (EDARSAHUB SQL)
/app/backend/modules/comercial/service.py:1687:    - solo_ventas_dia=True → Lee de EDARSAHUB SQL (Comercial_Ventas_Dia_Abiertas_v2)
/app/backend/modules/comercial/service.py:1697:    # OBLIGATORIO: Leer desde Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/service.py:1817:    # - Usar la misma fuente que SoftRestaurant: Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:1840:        # Mapear código a unidad_negocio_id usado en Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:2033:        # FIX P0 (Dic 2025): Filtrar por Unidades_Negocio activas en EDARSAHUB
/app/backend/modules/comercial/service.py:2035:        # Si no existe en EDARSAHUB.Unidades_Negocio → OMITIR (no mostrar como "Unidad Desconocida")
/app/backend/modules/comercial/service.py:2040:            continue  # Omitir sucursal no registrada en Unidades_Negocio
/app/backend/modules/comercial/service.py:2247:            # FIX P0: Campos canónicos desde Unidades_Negocio EDARSAHUB
/app/backend/modules/comercial/service.py:2349:# EDARSAHUB SÍ tiene datos en Comercial_KPIs_Diarios_v2.
/app/backend/modules/comercial/service.py:2355:# SOLUCIÓN: Usar la MISMA fuente que Tablero Ejecutivo (Comercial_KPIs_Diarios_v2)
/app/backend/modules/comercial/service.py:2372:    DASHBOARD COMERCIAL - KPIs desde EDARSAHUB (Comercial_KPIs_Diarios_v2)
/app/backend/modules/comercial/service.py:2377:    FUENTE: Comercial_KPIs_Diarios_v2 en EDARSAHUB
/app/backend/modules/comercial/service.py:2472:        'source_table': 'Comercial_KPIs_Diarios_v2',
/app/backend/modules/comercial/service.py:2507:        FROM Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:2538:    # Este fallback maneja el caso donde los datos MPRO en Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:2557:        FROM Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:2622:    Busca en Comercial_KPIs_Diarios_v2 el registro más reciente para el servidor,
/app/backend/modules/comercial/service.py:2655:            FROM Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/inteligencia_comercial_routes.py:8:- Usa vistas canónicas: Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_comercial_routes.py:9:- Usa SP canónico: Sp_Validar_Inteligencia_Comercial_Status
/app/backend/modules/comercial/inteligencia_comercial_routes.py:174:    Fuente: dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_comercial_routes.py:199:    FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_comercial_routes.py:203:    return {"source": "Comercial_Inteligencia_VW_KPIsEjecutivos", "data": rows[0] if rows else {}}
/app/backend/modules/comercial/inteligencia_comercial_routes.py:216:    Fuente: dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_comercial_routes.py:251:    FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_comercial_routes.py:256:    return {"source": "Comercial_Inteligencia_VW_KPIsEjecutivos", "nivel": nivel, "data": _query(sql, params)}
/app/backend/modules/comercial/inteligencia_comercial_routes.py:269:    Fuente: dbo.Sync_PAX_Detalle (tabla sincronizada)
/app/backend/modules/comercial/inteligencia_comercial_routes.py:299:    FROM dbo.Sync_PAX_Detalle
/app/backend/modules/comercial/inteligencia_comercial_routes.py:304:    return {"source": "Sync_PAX_Detalle", "data": _query(sql, params)}
/app/backend/modules/comercial/inteligencia_comercial_routes.py:311:    Fuente: dbo.Unidades_Negocio
/app/backend/modules/comercial/inteligencia_comercial_routes.py:322:    FROM dbo.Unidades_Negocio
/app/backend/modules/comercial/inteligencia_comercial_routes.py:326:    return {"source": "Unidades_Negocio", "data": _query(sql)}
/app/backend/modules/comercial/inteligencia_comercial_routes.py:333:    Fuente: dbo.Sp_Validar_Inteligencia_Comercial_Status (SP canónico)
/app/backend/modules/comercial/inteligencia_comercial_routes.py:338:    rows = _exec_sp("Sp_Validar_Inteligencia_Comercial_Status")
/app/backend/modules/comercial/inteligencia_comercial_routes.py:341:        "source": "Sp_Validar_Inteligencia_Comercial_Status",
/app/backend/modules/comercial/inteligencia_comercial_routes.py:354:    Fuente: dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_comercial_routes.py:373:    FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_comercial_routes.py:378:    return {"source": "Comercial_Inteligencia_VW_KPIsEjecutivos", "data": _query(sql, params)}
/app/backend/modules/comercial/inteligencia_comercial_routes.py:389:    Fuente: dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_comercial_routes.py:411:    FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_comercial_routes.py:416:    return {"source": "Comercial_Inteligencia_VW_KPIsEjecutivos", "data": _query(sql, params)}
/app/backend/modules/comercial/inteligencia_repository.py:18:    - Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_repository.py:20:    - Sp_Validar_Inteligencia_Comercial_Status
/app/backend/modules/comercial/inteligencia_repository.py:79:            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_repository.py:121:            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_repository.py:152:            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_repository.py:165:            EXEC dbo.Sp_Validar_Inteligencia_Comercial_Status
/app/backend/modules/comercial/inteligencia_repository.py:180:            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_repository.py:215:            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/inteligencia_repository.py:226:            FROM dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:20:- `dbo.Comercial_Inteligencia_VW_KPIsEjecutivos`
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:21:- `dbo.Comercial_Ventas_Dia_Abiertas_v2`
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:22:- `dbo.Sync_PAX_Detalle`
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:23:- `dbo.Sync_Sales`
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:24:- `dbo.Unidades_Negocio`
/app/backend/modules/comercial/routes.py.bak:156:from core.server_registry import list_unidades_negocio
/app/backend/modules/comercial/routes.py.bak:194:# - /comercial/tablero-ejecutivo - Usa Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/routes.py.bak:360:# de Comercial_Ventas_Dia_Abiertas_v2 en EDARSAHUB como fallback.
/app/backend/modules/comercial/routes.py.bak:371:    Tabla: Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/routes.py.bak:450:    FROM Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/routes.py.bak:864:            # - solo_ventas_dia=True: Leer de Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/routes.py.bak:918:                            # Leer de Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/routes.py.bak:968:                                    '_source': 'Comercial_Ventas_Dia_Abiertas_v2',
/app/backend/modules/comercial/routes.py.bak:973:                                logging.warning(f"[P0.5-EDARSAHUB] {server['name']}: Sin datos en Comercial_Ventas_Dia_Abiertas_v2")
/app/backend/modules/comercial/routes.py.bak:1678:    # FUENTE: EDARSAHUB.Unidades_Negocio (NO MongoDB)
/app/backend/modules/comercial/routes.py.bak:1680:        unidades_edarsahub = list_unidades_negocio(active_only=True)
/app/backend/modules/comercial/routes.py.bak:1762:    # pero sus datos SÍ existen en Comercial_Ventas_Dia_Abiertas_v2.
/app/backend/modules/comercial/routes.py.bak:4109:    Consulta tabla Sync_PAX_Detalle en EDARSAHUB.
/app/backend/modules/comercial/routes.py.bak:4149:                SELECT * FROM Sync_PAX_Detalle
/app/backend/modules/comercial/routes.py.bak:4156:                SELECT * FROM Sync_PAX_Detalle
/app/backend/modules/comercial/routes.py.bak:4200:            source_message=f"SQL-First: {len(pax_detalle)} registros desde Sync_PAX_Detalle",
/app/backend/modules/comercial/routes.py.bak:4855:            # PERO EDARSAHUB sí tiene datos en Comercial_KPIs_Diarios_v2.
/app/backend/modules/comercial/repository.py:286:    Busca en la tabla Unidades_Negocio que mapea servidor + código origen -> nombre.
/app/backend/modules/comercial/repository.py:301:        FROM Unidades_Negocio
/app/backend/modules/comercial/routes.py:156:from core.server_registry import list_unidades_negocio
/app/backend/modules/comercial/routes.py:194:# - /comercial/tablero-ejecutivo - Usa Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/routes.py:360:# de Comercial_Ventas_Dia_Abiertas_v2 en EDARSAHUB como fallback.
/app/backend/modules/comercial/routes.py:371:    Tabla: Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/routes.py:450:    FROM Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/routes.py:864:            # - solo_ventas_dia=True: Leer de Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/routes.py:918:                            # Leer de Comercial_Ventas_Dia_Abiertas_v2
/app/backend/modules/comercial/routes.py:968:                                    '_source': 'Comercial_Ventas_Dia_Abiertas_v2',
/app/backend/modules/comercial/routes.py:973:                                logging.warning(f"[P0.5-EDARSAHUB] {server['name']}: Sin datos en Comercial_Ventas_Dia_Abiertas_v2")
/app/backend/modules/comercial/routes.py:1678:    # FUENTE: EDARSAHUB.Unidades_Negocio (NO MongoDB)
/app/backend/modules/comercial/routes.py:1680:        unidades_edarsahub = list_unidades_negocio(active_only=True)
/app/backend/modules/comercial/routes.py:1762:    # pero sus datos SÍ existen en Comercial_Ventas_Dia_Abiertas_v2.
/app/backend/modules/comercial/routes.py:4109:    Consulta tabla Sync_PAX_Detalle en EDARSAHUB.
/app/backend/modules/comercial/routes.py:4149:                SELECT * FROM Sync_PAX_Detalle
/app/backend/modules/comercial/routes.py:4156:                SELECT * FROM Sync_PAX_Detalle
/app/backend/modules/comercial/routes.py:4200:            source_message=f"SQL-First: {len(pax_detalle)} registros desde Sync_PAX_Detalle",
/app/backend/modules/comercial/routes.py:4466:            # PERO EDARSAHUB sí tiene datos en Comercial_KPIs_Diarios_v2.
```

## Búsqueda de patrones prohibidos en endpoints IC

```text
/app/backend/modules/comercial/service.py:11:- Migrado: get_kpis_softrestaurant() desde server.py
/app/backend/modules/comercial/service.py:12:- Migrado: get_kpis_mpro() desde server.py  
/app/backend/modules/comercial/service.py:13:- Migrado: get_kpis_mpro_por_sucursal() desde server.py
/app/backend/modules/comercial/service.py:17:- query_api_mpro_local() -> modules/comercial/adapters.py
/app/backend/modules/comercial/service.py:48:from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
/app/backend/modules/comercial/service.py:49:from modules.comercial.queries.mpro import query_ventas_periodo_mpro, query_ventas_por_sucursal_mpro
/app/backend/modules/comercial/service.py:77:# NO consulta servidores locales ni MongoDB para KPIs.
/app/backend/modules/comercial/service.py:93:# NO usar MongoDB como fuente funcional para unidades.
/app/backend/modules/comercial/service.py:102:    NO usa MongoDB.
/app/backend/modules/comercial/service.py:153:            # Mapeo por server_id (para SoftRestaurant sin sucursal)
/app/backend/modules/comercial/service.py:157:            # Mapeo por server_id:sucursal (para MPRO con sucursal)
/app/backend/modules/comercial/service.py:180:    NO usa MongoDB.
/app/backend/modules/comercial/service.py:184:        sucursal: ID de sucursal (para MPRO)
/app/backend/modules/comercial/service.py:201:    # Si no se encuentra, retornar estructura vacía (no usar MongoDB)
/app/backend/modules/comercial/service.py:211:def _obtener_codigo_canonico_mpro(server_id: str, sucursal_id: str, sucursal_nombre: str) -> tuple:
/app/backend/modules/comercial/service.py:213:    CAMBIO B HELPER: Obtiene código y nombre canónico para una sucursal MPRO.
/app/backend/modules/comercial/service.py:221:        server_id: ID del servidor MPRO
/app/backend/modules/comercial/service.py:235:            logging.debug(f"[SERVICE] _obtener_codigo_canonico_mpro: EmpresaResolver resolvió '{sucursal_nombre}' -> {empresa.codigo_empresa}")
/app/backend/modules/comercial/service.py:239:        # Los códigos MPRO deben estar en Sistema_EmpresasServidores
/app/backend/modules/comercial/service.py:257:                    logging.debug(f"[SERVICE] _obtener_codigo_canonico_mpro: Resuelto por CodigoSucursalSistema '{sucursal_id}' -> {codigo}")
/app/backend/modules/comercial/service.py:370:def _obtener_sucursales_mpro_desde_resolver() -> List[Dict[str, Any]]:
/app/backend/modules/comercial/service.py:372:    FASE 5B HELPER: Obtiene la lista de sucursales MPRO desde EmpresaResolver.
/app/backend/modules/comercial/service.py:374:    Lee de Sistema_EmpresasServidores las empresas que tienen conexión MPRO
/app/backend/modules/comercial/service.py:389:            # Buscar empresas con conexiones MPRO (tienen NumeroSucursalSistema)
/app/backend/modules/comercial/service.py:444:                logging.info(f"[SERVICE] _obtener_sucursales_mpro_desde_resolver: {len(sucursales)} sucursales obtenidas via EmpresaResolver")
/app/backend/modules/comercial/service.py:448:            logging.warning(f"[SERVICE] Error obteniendo sucursales MPRO desde EmpresaResolver: {e}")
/app/backend/modules/comercial/service.py:453:    logging.warning("[SERVICE] _obtener_sucursales_mpro_desde_resolver: Usando fallback hardcodeado")
/app/backend/modules/comercial/service.py:477:    NO usa MongoDB. NO usa servidores locales.
/app/backend/modules/comercial/service.py:527:    RAZÓN: Para MPRO, los datos en Comercial_KPIs_Diarios_v2 tienen un server_id
/app/backend/modules/comercial/service.py:542:        # FIX: Usar unidad_negocio_id para MPRO
/app/backend/modules/comercial/service.py:804:    - NO consulta MongoDB
/app/backend/modules/comercial/service.py:912:    # FIX: Pasar unidad_negocio_id para filtro más confiable (especialmente para MPRO)
/app/backend/modules/comercial/service.py:1040:    # SoftRestaurant
/app/backend/modules/comercial/service.py:1041:    "a5547321-1139-4d2b-9d53-182ca737b6b6": {"unidad_negocio_id": "130MID", "nombre": "130° MÉRIDA", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
/app/backend/modules/comercial/service.py:1042:    "6d053c22-523e-48c0-b72b-96081e2d781b": {"unidad_negocio_id": "CIENFUEGOS", "nombre": "CIENFUEGOS", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
/app/backend/modules/comercial/service.py:1043:    "a5ff0e25-f029-43db-b634-d4ac814c904f": {"unidad_negocio_id": "ESTELAR", "nombre": "LA ESTELAR", "sucursal_id": "DEFAULT", "sistema": "SoftRestaurant"},
/app/backend/modules/comercial/service.py:1044:    # MPRO (necesitan sucursal específica)
/app/backend/modules/comercial/service.py:1050:        "sistema": "MPRO"
/app/backend/modules/comercial/service.py:1185:    - NO usa MongoDB servers.name como nombre oficial
/app/backend/modules/comercial/service.py:1197:    # NO usar MongoDB servers.name como nombre funcional/oficial
/app/backend/modules/comercial/service.py:1210:    if system_type.upper() in ['MPRO', 'MANAGEMENTPRO']:
/app/backend/modules/comercial/service.py:1212:    elif system_type.upper() in ['SOFTRESTAURANT', 'SR']:
/app/backend/modules/comercial/service.py:1366:# - NO consultan MongoDB como fuente de datos
/app/backend/modules/comercial/service.py:1369:def get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
/app/backend/modules/comercial/service.py:1371:    TABLERO EJECUTIVO - KPIs SoftRestaurant desde EDARSAHUB
/app/backend/modules/comercial/service.py:1377:    - NO consulta MongoDB
/app/backend/modules/comercial/service.py:1381:    - NO usa MongoDB servers.name como nombre oficial
/app/backend/modules/comercial/service.py:1394:    # NO usar MongoDB servers.name como nombre oficial
/app/backend/modules/comercial/service.py:1402:    nombre = unidad_negocio_nombre or server.get('name', 'SoftRestaurant')
/app/backend/modules/comercial/service.py:1499:def get_kpis_mpro(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes):
/app/backend/modules/comercial/service.py:1501:    TABLERO EJECUTIVO - KPIs MPRO desde EDARSAHUB
/app/backend/modules/comercial/service.py:1507:    - NO consulta MongoDB
/app/backend/modules/comercial/service.py:1509:    NOTA: MPRO tiene múltiples sucursales (0021 = 130° QUERETARO, 0023 = ORIGEN).
/app/backend/modules/comercial/service.py:1511:    Para KPIs por sucursal individual, usar get_kpis_mpro_por_sucursal.
/app/backend/modules/comercial/service.py:1516:    nombre = server.get('name', 'MPRO')
/app/backend/modules/comercial/service.py:1518:    # Obtener configuración de unidades MPRO
/app/backend/modules/comercial/service.py:1519:    mpro_config = UNIDADES_EDARSAHUB_MAP.get(server_id, {})
/app/backend/modules/comercial/service.py:1521:    if not mpro_config or 'sucursales' not in mpro_config:
/app/backend/modules/comercial/service.py:1522:        logging.warning(f"[TABLERO-EDARSAHUB] {nombre}: server_id {server_id} no tiene mapeo de unidad MPRO")
/app/backend/modules/comercial/service.py:1525:    sucursales = mpro_config.get('sucursales', {})
/app/backend/modules/comercial/service.py:1534:    # Agregar KPIs de todas las sucursales MPRO
/app/backend/modules/comercial/service.py:1592:    # FIX PROYECCIÓN MENSUAL MPRO: Usar días transcurridos OPERATIVOS
/app/backend/modules/comercial/service.py:1594:    # REGLA CANÓNICA: Misma que SoftRestaurant
/app/backend/modules/comercial/service.py:1627:        logging.info(f"[PROYECCION-FIX-MPRO] {nombre}: Mes cerrado, días={dias_transcurridos_calc}")
/app/backend/modules/comercial/service.py:1630:        logging.info(f"[PROYECCION-FIX-MPRO] {nombre}: Mes actual, FechaOp={fecha_operacion_actual}, días={dias_transcurridos_calc}")
/app/backend/modules/comercial/service.py:1674:def get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant, fecha_ini_año_ant, fecha_fin_año_ant, dias_transcurridos, dias_mes, solo_ventas_dia=False):
/app/backend/modules/comercial/service.py:1676:    Query para MPRO que devuelve KPIs DIVIDIDOS POR SUCURSAL (como en Inventarios).
/app/backend/modules/comercial/service.py:1691:    logging.debug(f"MPRO {server['name']}: solo_ventas_dia={solo_ventas_dia}, fecha_ini={fecha_ini}, fecha_fin={fecha_fin}")
/app/backend/modules/comercial/service.py:1700:        logging.info(f"[FIX-P0] MPRO {server['name']}: Modo Ventas del Día - LEYENDO DE EDARSAHUB SQL (NO API local)")
/app/backend/modules/comercial/service.py:1703:        # FASE 5B: Obtener sucursales MPRO desde EmpresaResolver
/app/backend/modules/comercial/service.py:1704:        # Reemplaza el hardcoding de sucursales_mpro
/app/backend/modules/comercial/service.py:1706:        sucursales_mpro = _obtener_sucursales_mpro_desde_resolver()
/app/backend/modules/comercial/service.py:1710:        for suc in sucursales_mpro:
/app/backend/modules/comercial/service.py:1737:                    "system_type": "MPRO",
/app/backend/modules/comercial/service.py:1767:                    f"[FIX-P0] MPRO {nombre_canonico}: EDARSAHUB SQL OK - "
/app/backend/modules/comercial/service.py:1775:                    "system_type": "MPRO",
/app/backend/modules/comercial/service.py:1804:                    f"[FIX-P0] MPRO {nombre_canonico}: Sin datos en EDARSAHUB SQL - "
/app/backend/modules/comercial/service.py:1815:    # - Para modo HUB (Tablero Ejecutivo), MPRO debe leer de EDARSAHUB SQL
/app/backend/modules/comercial/service.py:1816:    # - NO consultar servidores MPRO directamente (bases QUERETARO, ORIGEN)
/app/backend/modules/comercial/service.py:1817:    # - Usar la misma fuente que SoftRestaurant: Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:1820:    # Las bases MPRO (QUERETARO, ORIGEN) son fuentes de extracción, no de lectura.
/app/backend/modules/comercial/service.py:1823:    logging.info(f"[FIX-HUB] MPRO {server['name']}: Modo Histórico/Acumulado - LEYENDO DE EDARSAHUB SQL (NO bases MPRO)")
/app/backend/modules/comercial/service.py:1825:    # Obtener sucursales MPRO desde EmpresaResolver
/app/backend/modules/comercial/service.py:1826:    sucursales_mpro = _obtener_sucursales_mpro_desde_resolver()
/app/backend/modules/comercial/service.py:1830:    for suc in sucursales_mpro:
/app/backend/modules/comercial/service.py:1843:        # Usar la misma función que SoftRestaurant para leer de EDARSAHUB
/app/backend/modules/comercial/service.py:1861:            kpis['system_type'] = "MPRO"
/app/backend/modules/comercial/service.py:1869:                f"[FIX-HUB] MPRO {nombre_canonico}: EDARSAHUB SQL OK - "
/app/backend/modules/comercial/service.py:1879:                "system_type": "MPRO",
/app/backend/modules/comercial/service.py:1905:                f"[FIX-HUB] MPRO {nombre_canonico}: Sin datos en EDARSAHUB SQL para período {fecha_ini} a {fecha_fin}"
/app/backend/modules/comercial/service.py:1913:        logging.error(f"MPRO {server['name']}: Rango de fechas inválido ({fecha_ini} > {fecha_fin})")
/app/backend/modules/comercial/service.py:1916:    # Formato YYYYMMDD para MPRO (SQL Server con configuración regional español)
/app/backend/modules/comercial/service.py:1920:        logging.error(f"MPRO {server['name']}: Error convirtiendo fechas: {e}")
/app/backend/modules/comercial/service.py:1923:    logging.info(f"[TABLERO] MPRO {server['name']}: Conexión OK - Fechas: {fecha_ini} a {fecha_fin}")
/app/backend/modules/comercial/service.py:1957:            logging.debug(f"MPRO por sucursal {server['name']} - Ultimo dia con ventas: {anio_ultimo}-{mes_ultimo:02d}-{dia_con_datos:02d}")
/app/backend/modules/comercial/service.py:1967:            logging.debug(f"MPRO por sucursal {server['name']} - Período ajustado: {fi} a {ff}, días: {dias_transcurridos}")
/app/backend/modules/comercial/service.py:1996:            logging.info(f"MPRO por sucursal Períodos ajustados - Mes ant: {fecha_ini_ant} a {fecha_fin_ant}, Año ant: {fecha_ini_año_ant} a {fecha_fin_año_ant}")
/app/backend/modules/comercial/service.py:1998:        logging.warning(f"MPRO por sucursal Error detectando último día: {e}")
/app/backend/modules/comercial/service.py:2005:    logging.info(f"MPRO {server['name']}: Consultando ventas del {fi} al {ff}")
/app/backend/modules/comercial/service.py:2007:    # BLOQUE 4: Migrado a query centralizada query_ventas_por_sucursal_mpro()
/app/backend/modules/comercial/service.py:2008:    # ORIGEN ANTERIOR: SQL directo líneas 862-875 (ahora en queries/mpro.py)
/app/backend/modules/comercial/service.py:2009:    result_principal = query_ventas_por_sucursal_mpro(server, fecha_ini, fecha_fin)
/app/backend/modules/comercial/service.py:2015:            f"Error consultando MPRO por sucursal {server['name']}: {result_principal.error} "
/app/backend/modules/comercial/service.py:2021:        logging.warning(f"MPRO {server['name']}: No se encontraron sucursales con ventas")
/app/backend/modules/comercial/service.py:2024:    logging.info(f"MPRO {server['name']}: Query retornó {len(result_principal.sucursales)} sucursales")
/app/backend/modules/comercial/service.py:2039:            logging.info(f"[MPRO] Sucursal no visible omitida: sucursal_origen_id={sucursal_id}, nombre={sucursal_nombre}")
/app/backend/modules/comercial/service.py:2072:                logging.debug(f"MPRO {sucursal_nombre} - Ultimo dia con ventas: dia {dia_suc}")
/app/backend/modules/comercial/service.py:2212:        logging.debug(f"MPRO {sucursal_nombre}: Dia={dia_suc}, Actual={ventas:.2f}, MesAnt({fia_suc}-{ffa_suc})={ventas_ant:.2f} -> {var_vs_mes_ant}%, AnoAnt({fiaa_suc}-{ffaa_suc})={ventas_año:.2f} -> {var_vs_año_ant}%")
/app/backend/modules/comercial/service.py:2219:        # via resolve_unidad_by_server_sucursal() - NO usar _obtener_codigo_canonico_mpro()
/app/backend/modules/comercial/service.py:2227:            "system_type": "MPRO",
/app/backend/modules/comercial/service.py:2252:        logging.info(f"MPRO {server['name']} - Sucursal '{nombre_canonico}' (origen_id={sucursal_id}): Ventas={ventas}, Cheques={cheques}")
/app/backend/modules/comercial/service.py:2261:def get_kpis_mpro_con_estado(
/app/backend/modules/comercial/service.py:2268:    FASE 4.4: Obtiene KPIs de MPRO con envelope de estado.
/app/backend/modules/comercial/service.py:2287:        unidades = get_kpis_mpro_por_sucursal(server, fecha_ini, fecha_fin, solo_ventas_dia)
/app/backend/modules/comercial/service.py:2335:    'get_kpis_softrestaurant',
/app/backend/modules/comercial/service.py:2336:    'get_kpis_mpro',
/app/backend/modules/comercial/service.py:2337:    'get_kpis_mpro_por_sucursal',
/app/backend/modules/comercial/service.py:2339:    'get_kpis_mpro_con_estado',
/app/backend/modules/comercial/service.py:2352:# SoftRestaurant. Si la conexión fallaba, mostraba "Sin Datos" aunque EDARSAHUB
/app/backend/modules/comercial/service.py:2378:    NO consulta: Servidores remotos SoftRestaurant
/app/backend/modules/comercial/service.py:2379:    NO consulta: MongoDB
/app/backend/modules/comercial/service.py:2489:    FIX MPRO: Si no encuentra por server_id, intenta buscar por unidad_negocio_id
/app/backend/modules/comercial/service.py:2490:    derivado del nombre del servidor. Esto maneja casos donde los datos MPRO
/app/backend/modules/comercial/service.py:2536:    # FIX MPRO: Buscar por unidad_negocio_id si no encontramos por server_id
/app/backend/modules/comercial/service.py:2538:    # Este fallback maneja el caso donde los datos MPRO en Comercial_KPIs_Diarios_v2
/app/backend/modules/comercial/service.py:2546:        logging.info(f"[DASHBOARD-EDARSAHUB-MPRO-FIX] Intentando búsqueda por unidad_negocio_id: {unidad_ids}")
/app/backend/modules/comercial/service.py:2551:        query_mpro = f"""
/app/backend/modules/comercial/service.py:2564:        result_mpro = _query_edarsahub_tablero(query_mpro)
/app/backend/modules/comercial/service.py:2566:        if result_mpro and len(result_mpro) > 0:
/app/backend/modules/comercial/service.py:2567:            row = result_mpro[0]
/app/backend/modules/comercial/service.py:2575:                    f"[DASHBOARD-EDARSAHUB-MPRO-FIX] Datos MPRO encontrados por unidad_negocio_id: "
/app/backend/modules/comercial/service.py:2610:        # ManagmentPro (servidor MPRO principal) - no necesita fallback
/app/backend/modules/comercial/service.py:2632:        conn = pymssql.connect(
/app/backend/modules/comercial/routes_pricing_ai.py:16:- NO usar MongoDB
/app/backend/modules/comercial/routes_pricing_ai.py:396:            "mongodb": False,
/app/backend/modules/comercial/routes_pricing_ai.py:432:    - NO usa MongoDB
/app/backend/modules/comercial/cache_service.py:14:entre SoftRestaurant y MPRO.
/app/backend/modules/comercial/cache_service.py:33:# Referencia global a MongoDB (evita circular import con server.py)
/app/backend/modules/comercial/cache_service.py:38:    DEPRECADO: MongoDB ya no se usa.
/app/backend/modules/comercial/cache_service.py:44:    logging.warning("[COMERCIAL] Cache service - MongoDB deprecado, funcionalidad limitada")
/app/backend/modules/comercial/cache_service.py:48:    DEPRECADO: MongoDB ya no se usa.
/app/backend/modules/comercial/cache_service.py:54:        logging.debug("[COMERCIAL] get_db() - MongoDB deprecado")
/app/backend/modules/comercial/cache_service.py:89:    SoftRestaurant y MPRO. Esto garantiza que:
/app/backend/modules/comercial/cache_service.py:90:    - SoftRestaurant NO comparta caché con MPRO
/app/backend/modules/comercial/cache_service.py:91:    - MPRO NO comparta caché con SoftRestaurant
/app/backend/modules/comercial/cache_service.py:92:    - Variantes de system_type (MPRO, ManagmentPro, etc.) se normalicen
/app/backend/modules/comercial/__init__.py:12:- repository.py: Queries SQL y acceso a MongoDB
/app/backend/modules/comercial/__init__.py:13:- adapters.py: Integración con APIs locales MPRO
/app/backend/modules/comercial/__init__.py:18:- APIS_MPRO_LOCALES (configuración)
/app/backend/modules/comercial/__init__.py:19:- query_api_mpro_local()
/app/backend/modules/comercial/__init__.py:38:    APIS_MPRO_LOCALES,
/app/backend/modules/comercial/__init__.py:39:    query_api_mpro_local,
/app/backend/modules/comercial/__init__.py:53:    Inicializa el módulo comercial con la conexión a MongoDB.
/app/backend/modules/comercial/__init__.py:56:        database: Instancia de AsyncIOMotorDatabase
/app/backend/modules/comercial/__init__.py:71:    # Adapters (APIs locales MPRO)
/app/backend/modules/comercial/__init__.py:72:    'APIS_MPRO_LOCALES',
/app/backend/modules/comercial/__init__.py:73:    'query_api_mpro_local',
/app/backend/modules/comercial/queries/__init__.py:17:- softrestaurant.py: Queries base para servidores SoftRestaurant
/app/backend/modules/comercial/queries/__init__.py:18:- mpro.py: Queries base para servidores MPRO
/app/backend/modules/comercial/queries/__init__.py:22:- VENTAS_TOTAL: query_ventas_periodo_sr/mpro
/app/backend/modules/comercial/queries/__init__.py:25:- CORTES_TURNOS: query_ventas_sin_corte_sr/mpro
/app/backend/modules/comercial/queries/__init__.py:44:# Bloque 2: Query base de ventas SoftRestaurant
/app/backend/modules/comercial/queries/__init__.py:45:from .softrestaurant import (
/app/backend/modules/comercial/queries/__init__.py:50:# Bloque 3: Query base de ventas MPRO
/app/backend/modules/comercial/queries/__init__.py:51:from .mpro import (
/app/backend/modules/comercial/queries/__init__.py:52:    query_ventas_periodo_mpro,
/app/backend/modules/comercial/queries/__init__.py:53:    VentasPeriodoResult as VentasPeriodoResultMPRO,
/app/backend/modules/comercial/queries/__init__.py:69:__phase__ = "BLOQUE_3_VENTAS_MPRO"
/app/backend/modules/comercial/queries/hub.py:2:EDARSA HUB - Lecturas desde EDARSA HUB (MongoDB)
/app/backend/modules/comercial/queries/hub.py:9:COLECCIONES MONGODB:
/app/backend/modules/comercial/queries/hub.py:59:# Los imports de MongoDB se agregarán cuando se implemente
/app/backend/modules/comercial/queries/hub.py:168:    Construye filtro MongoDB para consultas de KPIs.
/app/backend/modules/comercial/queries/hub.py:178:        Dict filtro para MongoDB find()
/app/backend/modules/comercial/queries/mpro.py:2:EDARSA HUB - Queries Base para MPRO (ManagementPro)
/app/backend/modules/comercial/queries/mpro.py:6:Centralizar las queries SQL homologadas para servidores MPRO.
/app/backend/modules/comercial/queries/mpro.py:9:TABLAS PRINCIPALES MPRO:
/app/backend/modules/comercial/queries/mpro.py:18:- query_ventas_periodo_mpro: Ventas totales, PAX, cheques para un período
/app/backend/modules/comercial/queries/mpro.py:19:- query_ventas_sin_corte_mpro: Ventas del día sin cierre
/app/backend/modules/comercial/queries/mpro.py:20:- query_ventas_por_sucursal_mpro: Ventas desglosadas por sucursal
/app/backend/modules/comercial/queries/mpro.py:30:DIFERENCIAS CON SOFTRESTAURANT:
/app/backend/modules/comercial/queries/mpro.py:37:- get_kpis_mpro() en service.py
/app/backend/modules/comercial/queries/mpro.py:56:from core.system_type_utils import is_mpro_system
/app/backend/modules/comercial/queries/mpro.py:61:# Importar EmpresaResolver para resolución canónica de sucursales MPRO
/app/backend/modules/comercial/queries/mpro.py:71:    logging.warning(f"[MPRO] EmpresaResolver no disponible: {e}. Usando fallback.")
/app/backend/modules/comercial/queries/mpro.py:79:# Tablas conocidas de MPRO para validación
/app/backend/modules/comercial/queries/mpro.py:80:MPRO_KNOWN_TABLES = [
/app/backend/modules/comercial/queries/mpro.py:92:MODULE_NAME = "COMERCIAL_QUERIES_MPRO"
/app/backend/modules/comercial/queries/mpro.py:96:# RESULTADO HOMOLOGADO (igual que SoftRestaurant para consistencia)
/app/backend/modules/comercial/queries/mpro.py:103:    Estructura idéntica a softrestaurant.py para consistencia.
/app/backend/modules/comercial/queries/mpro.py:117:def query_ventas_periodo_mpro(
/app/backend/modules/comercial/queries/mpro.py:124:    Query base ÚNICA de ventas para MPRO.
/app/backend/modules/comercial/queries/mpro.py:126:    ORIGEN: Extraída de service.py líneas 871-884 (get_kpis_mpro_por_sucursal)
/app/backend/modules/comercial/queries/mpro.py:134:    DIFERENCIAS VS SOFTRESTAURANT:
/app/backend/modules/comercial/queries/mpro.py:145:    - get_kpis_mpro_por_sucursal() en service.py (migración Bloque 4)
/app/backend/modules/comercial/queries/mpro.py:146:    - /comercial/tablero-ejecutivo para servidores MPRO
/app/backend/modules/comercial/queries/mpro.py:160:    if not is_mpro_system(system_type):
/app/backend/modules/comercial/queries/mpro.py:163:            error=f"Server {server.get('name')} no es MPRO (es {system_type})"
/app/backend/modules/comercial/queries/mpro.py:176:    fi = _format_fecha_mpro(fecha_ini, es_fin=False)
/app/backend/modules/comercial/queries/mpro.py:177:    ff = _format_fecha_mpro(fecha_fin, es_fin=True)
/app/backend/modules/comercial/queries/mpro.py:180:    filtro_suc = _build_sucursal_filter_mpro(sucursal_id, alias="VE")
/app/backend/modules/comercial/queries/mpro.py:237:        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_periodo_mpro para {server.get('name')}: {e}")
/app/backend/modules/comercial/queries/mpro.py:245:# FUNCIÓN PARA DASHBOARD MPRO CON FILTRO FLEXIBLE
/app/backend/modules/comercial/queries/mpro.py:248:def query_ventas_periodo_mpro_con_filtro_flexible(
/app/backend/modules/comercial/queries/mpro.py:256:    Query de ventas MPRO con filtro flexible de sucursal.
/app/backend/modules/comercial/queries/mpro.py:261:    A diferencia de query_ventas_periodo_mpro():
/app/backend/modules/comercial/queries/mpro.py:265:    - Usa la misma lógica que el endpoint dashboard MPRO
/app/backend/modules/comercial/queries/mpro.py:278:    - /comercial/dashboard/{server_id} (sección MPRO)
/app/backend/modules/comercial/queries/mpro.py:293:    if not is_mpro_system(system_type):
/app/backend/modules/comercial/queries/mpro.py:296:            error=f"Server {server.get('name')} no es MPRO (es {system_type})"
/app/backend/modules/comercial/queries/mpro.py:309:    fi = _format_fecha_mpro(fecha_ini, es_fin=False)
/app/backend/modules/comercial/queries/mpro.py:310:    ff = _format_fecha_mpro(fecha_fin, es_fin=True)
/app/backend/modules/comercial/queries/mpro.py:332:        codigo_sucursal_resuelto = _resolver_codigo_sucursal_mpro(sucursal)
/app/backend/modules/comercial/queries/mpro.py:338:            logging.info(f"[MPRO] Filtro resuelto por EmpresaResolver: '{sucursal}' -> '{codigo_sucursal_resuelto}'")
/app/backend/modules/comercial/queries/mpro.py:352:                logging.warning(f"[MPRO] Filtro LIKE legacy para '{sucursal}' - considerar agregar alias a EmpresaResolver")
/app/backend/modules/comercial/queries/mpro.py:362:    # QUERY SQL - Basada en routes.py dashboard MPRO
/app/backend/modules/comercial/queries/mpro.py:379:        print(f"*** [MPRO Query] Ejecutando query para {server.get('name')} sucursal={sucursal} ***")
/app/backend/modules/comercial/queries/mpro.py:389:        print(f"*** [MPRO Query] Resultado: {result[:1] if result else 'None/Empty'} ***")
/app/backend/modules/comercial/queries/mpro.py:396:            print(f"*** [MPRO Query] Ventas={ventas:,.2f}, PAX={pax}, Cheques={cheques} ***")
/app/backend/modules/comercial/queries/mpro.py:398:            # Lógica de estimación PAX (igual que query_ventas_periodo_mpro)
/app/backend/modules/comercial/queries/mpro.py:403:            logging.info(f"[{MODULE_NAME}] query_ventas_periodo_mpro_con_filtro_flexible: "
/app/backend/modules/comercial/queries/mpro.py:416:            logging.info(f"[{MODULE_NAME}] query_ventas_periodo_mpro_con_filtro_flexible: "
/app/backend/modules/comercial/queries/mpro.py:427:        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_periodo_mpro_con_filtro_flexible "
/app/backend/modules/comercial/queries/mpro.py:439:def _format_fecha_mpro(fecha_iso: str, es_fin: bool = False) -> str:
/app/backend/modules/comercial/queries/mpro.py:441:    Convierte fecha ISO (YYYY-MM-DD) a formato SQL con hora para MPRO.
/app/backend/modules/comercial/queries/mpro.py:457:def _build_sucursal_filter_mpro(sucursal_id: Optional[str], alias: str = "VE") -> str:
/app/backend/modules/comercial/queries/mpro.py:459:    Construye filtro SQL para sucursal en MPRO.
/app/backend/modules/comercial/queries/mpro.py:473:def _resolver_codigo_sucursal_mpro(sucursal: str) -> Optional[str]:
/app/backend/modules/comercial/queries/mpro.py:475:    FASE 5C HELPER: Resuelve un alias/nombre de sucursal a CodigoSucursalSistema MPRO.
/app/backend/modules/comercial/queries/mpro.py:512:                logging.debug(f"[MPRO] _resolver_codigo_sucursal_mpro: '{sucursal}' -> EmpresaID={empresa.empresa_id}")
/app/backend/modules/comercial/queries/mpro.py:518:                    logging.info(f"[MPRO] _resolver_codigo_sucursal_mpro: EmpresaID={empresa.empresa_id} -> CodigoSucursal={connection.codigo_sucursal_sistema}")
/app/backend/modules/comercial/queries/mpro.py:524:                    logging.info(f"[MPRO] _resolver_codigo_sucursal_mpro: EmpresaID={empresa.empresa_id} -> CodigoSucursal={connection_api.codigo_sucursal_sistema} (via API_LOCAL)")
/app/backend/modules/comercial/queries/mpro.py:528:            logging.warning(f"[MPRO] Error en _resolver_codigo_sucursal_mpro para '{sucursal}': {e}")
/app/backend/modules/comercial/queries/mpro.py:547:        logging.warning(f"[MPRO] _resolver_codigo_sucursal_mpro: Usando fallback hardcodeado para '{sucursal}' -> '{codigo}'")
/app/backend/modules/comercial/queries/mpro.py:553:def _build_sucursal_filter_mpro_flexible(
/app/backend/modules/comercial/queries/mpro.py:559:    Construye filtro SQL flexible para sucursal en MPRO.
/app/backend/modules/comercial/queries/mpro.py:561:    FASE 5C: Usa _resolver_codigo_sucursal_mpro() para resolución canónica.
/app/backend/modules/comercial/queries/mpro.py:576:    codigo_resuelto = _resolver_codigo_sucursal_mpro(sucursal)
/app/backend/modules/comercial/queries/mpro.py:609:def query_ventas_por_sucursal_mpro(
/app/backend/modules/comercial/queries/mpro.py:615:    Query base de ventas AGRUPADAS POR SUCURSAL para MPRO.
/app/backend/modules/comercial/queries/mpro.py:617:    ORIGEN: Extraída de service.py líneas 862-884 (get_kpis_mpro_por_sucursal)
/app/backend/modules/comercial/queries/mpro.py:620:    DIFERENCIA CON query_ventas_periodo_mpro():
/app/backend/modules/comercial/queries/mpro.py:638:    - get_kpis_mpro_por_sucursal() en service.py (migración Bloque 4)
/app/backend/modules/comercial/queries/mpro.py:651:    if not is_mpro_system(system_type):
/app/backend/modules/comercial/queries/mpro.py:654:            error=f"Server {server.get('name')} no es MPRO (es {system_type})"
/app/backend/modules/comercial/queries/mpro.py:667:    fi = _format_fecha_mpro(fecha_ini, es_fin=False)
/app/backend/modules/comercial/queries/mpro.py:668:    ff = _format_fecha_mpro(fecha_fin, es_fin=True)
/app/backend/modules/comercial/queries/mpro.py:710:            logging.info(f"[{MODULE_NAME}] query_ventas_por_sucursal_mpro: {len(sucursales)} sucursales para {server.get('name')}")
/app/backend/modules/comercial/queries/mpro.py:718:            logging.info(f"[{MODULE_NAME}] query_ventas_por_sucursal_mpro: Sin sucursales con ventas para {server.get('name')}")
/app/backend/modules/comercial/queries/mpro.py:726:        logging.warning(f"[{MODULE_NAME}] Error en query_ventas_por_sucursal_mpro para {server.get('name')}: {e}")
/app/backend/modules/comercial/queries/softrestaurant.py:2:EDARSA HUB - Queries Base para SoftRestaurant
/app/backend/modules/comercial/queries/softrestaurant.py:6:Centralizar las queries SQL homologadas para servidores SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:9:TABLAS PRINCIPALES SOFTRESTAURANT:
/app/backend/modules/comercial/queries/softrestaurant.py:33:- get_kpis_softrestaurant() en service.py
/app/backend/modules/comercial/queries/softrestaurant.py:50:from core.system_type_utils import is_softrestaurant_system
/app/backend/modules/comercial/queries/softrestaurant.py:56:# Tablas conocidas de SoftRestaurant para validación
/app/backend/modules/comercial/queries/softrestaurant.py:104:    Query base ÚNICA de ventas para SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:106:    ORIGEN: Extraída de service.py líneas 341-363 (get_kpis_softrestaurant)
/app/backend/modules/comercial/queries/softrestaurant.py:121:    - get_kpis_softrestaurant() en service.py (migración Bloque 4)
/app/backend/modules/comercial/queries/softrestaurant.py:136:    if not is_softrestaurant_system(system_type):
/app/backend/modules/comercial/queries/softrestaurant.py:139:            error=f"Server {server.get('name')} no es SoftRestaurant (es {system_type})"
/app/backend/modules/comercial/queries/softrestaurant.py:222:    Convierte fecha ISO (YYYY-MM-DD) a formato SoftRestaurant (YYYYMMDD).
/app/backend/modules/comercial/queries/softrestaurant.py:235:    Construye filtro SQL para sucursal en SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:239:    - La columna idestacion puede no existir en algunas versiones de SoftRestaurant.
/app/backend/modules/comercial/queries/softrestaurant.py:263:    # La columna idestacion en SoftRestaurant tiene IDs como '130GRADOSCAJA', no nombres
/app/backend/modules/comercial/adapters.py:25:Adaptadores para integración con APIs locales MPRO.
/app/backend/modules/comercial/adapters.py:57:# CONFIGURACIÓN APIs LOCALES MPRO (FALLBACK LEGACY - SOLO SI EmpresaResolver FALLA)
/app/backend/modules/comercial/adapters.py:62:APIS_MPRO_LOCALES_LEGACY = {
/app/backend/modules/comercial/adapters.py:65:        "url": os.environ.get("API_MPRO_ORIGEN_URL", "http://<REDACTED_EDARSAHUB_SQL_HOST>:8000/query"),
/app/backend/modules/comercial/adapters.py:66:        "api_key": os.environ.get("API_MPRO_KEY", "EDARSA_2026_SECURE_KEY"),
/app/backend/modules/comercial/adapters.py:73:        "url": os.environ.get("API_MPRO_QRO_URL", "http://<REDACTED_EDARSAHUB_SQL_HOST>:8001/query"),
/app/backend/modules/comercial/adapters.py:74:        "api_key": os.environ.get("API_MPRO_KEY", "EDARSA_2026_SECURE_KEY"),
/app/backend/modules/comercial/adapters.py:82:APIS_MPRO_LOCALES = APIS_MPRO_LOCALES_LEGACY
/app/backend/modules/comercial/adapters.py:150:                api_config["url"] = os.environ.get("API_MPRO_ORIGEN_URL", "http://<REDACTED_EDARSAHUB_SQL_HOST>:8000/query")
/app/backend/modules/comercial/adapters.py:152:                api_config["url"] = os.environ.get("API_MPRO_QRO_URL", "http://<REDACTED_EDARSAHUB_SQL_HOST>:8001/query")
/app/backend/modules/comercial/adapters.py:157:            api_config["api_key"] = os.environ.get("API_MPRO_KEY", "EDARSA_2026_SECURE_KEY")
/app/backend/modules/comercial/adapters.py:168:def query_api_mpro_local(api_config: dict, sql_query: str, timeout: int = 3) -> dict:
/app/backend/modules/comercial/adapters.py:170:    Consulta una API MPRO local y retorna los resultados.
/app/backend/modules/comercial/adapters.py:180:    print(f"*** query_api_mpro_local: Iniciando query a {api_config.get('nombre', 'N/A')} ***")
/app/backend/modules/comercial/adapters.py:181:    print(f"*** query_api_mpro_local: URL = {api_config.get('url', 'N/A')} ***")
/app/backend/modules/comercial/adapters.py:182:    print(f"*** query_api_mpro_local: activo = {api_config.get('activo', 'N/A')} ***")
/app/backend/modules/comercial/adapters.py:185:        print("*** query_api_mpro_local: API desactivada, omitiendo ***")
/app/backend/modules/comercial/adapters.py:189:        print("*** query_api_mpro_local: URL no configurada, omitiendo ***")
/app/backend/modules/comercial/adapters.py:196:        print("*** query_api_mpro_local: Enviando request... ***")
/app/backend/modules/comercial/adapters.py:197:        response = requests.get(
/app/backend/modules/comercial/adapters.py:204:        print(f"*** query_api_mpro_local: Response status = {response.status_code} ***")
/app/backend/modules/comercial/adapters.py:212:            print(f"*** query_api_mpro_local: Response body = {response.text[:200]} ***")
/app/backend/modules/comercial/adapters.py:228:    Obtiene las ventas del día actual desde una API MPRO local.
/app/backend/modules/comercial/adapters.py:267:    result = query_api_mpro_local(api_config, sql_ventas_hoy)
/app/backend/modules/comercial/adapters.py:406:    # ========== FALLBACK LEGACY: Buscar en APIS_MPRO_LOCALES_LEGACY ==========
/app/backend/modules/comercial/adapters.py:408:    print("*** API Local: Intentando fallback legacy (APIS_MPRO_LOCALES_LEGACY) ***")
/app/backend/modules/comercial/adapters.py:437:        for api_id, api_cfg in APIS_MPRO_LOCALES_LEGACY.items():
/app/backend/modules/comercial/adapters.py:475:    'APIS_MPRO_LOCALES',
/app/backend/modules/comercial/adapters.py:476:    'query_api_mpro_local',
/app/backend/modules/comercial/routes_precios_sugeridos.py:11:- CERO MongoDB
/app/backend/modules/comercial/inteligencia_comercial_routes.py:10:- No consulta SoftRestaurant/MPRO en vivo desde dashboard.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:11:- No usa MongoDB como fuente de datos comerciales.
/app/backend/modules/comercial/inteligencia_comercial_routes.py:51:    NO conecta a SoftRestaurant, MPRO, MongoDB ni sistemas externos.
/app/backend/modules/comercial/alertas_margen_service.py:4:EDARSAHUB SQL es el cerebro. CERO MongoDB.
/app/backend/modules/comercial/alertas_margen_repository.py:4:EDARSAHUB SQL es el cerebro. CERO MongoDB.
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:5:Este modulo contiene componentes legacy que pueden consultar fuentes externas, MongoDB, adaptadores MPRO/SoftRestaurant o configuracion de servidores.
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:38:- MongoDB como fuente comercial.
/app/backend/modules/comercial/LEGACY_NO_LIVE_MIGRATION.md:39:- APIs SoftRestaurant/MPRO desde endpoints ejecutivos.
/app/backend/modules/comercial/routes.py.bak:27:- ✅ Adapters (APIs locales MPRO) migrados a adapters.py
/app/backend/modules/comercial/routes.py.bak:40:   - APIS_MPRO_LOCALES (configuración)
/app/backend/modules/comercial/routes.py.bak:41:   - query_api_mpro_local()
/app/backend/modules/comercial/routes.py.bak:46:   - get_kpis_softrestaurant()
/app/backend/modules/comercial/routes.py.bak:47:   - get_kpis_mpro()
/app/backend/modules/comercial/routes.py.bak:48:   - get_kpis_mpro_por_sucursal()
/app/backend/modules/comercial/routes.py.bak:100:    get_kpis_softrestaurant,
/app/backend/modules/comercial/routes.py.bak:101:    get_kpis_mpro,
/app/backend/modules/comercial/routes.py.bak:102:    get_kpis_mpro_por_sucursal,
/app/backend/modules/comercial/routes.py.bak:113:from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
/app/backend/modules/comercial/routes.py.bak:114:# BLOQUE 5.2: Import de query MPRO centralizada con filtro flexible
/app/backend/modules/comercial/routes.py.bak:115:from modules.comercial.queries.mpro import query_ventas_periodo_mpro_con_filtro_flexible
/app/backend/modules/comercial/routes.py.bak:159:    is_mpro_system,
/app/backend/modules/comercial/routes.py.bak:160:    is_softrestaurant_system,
/app/backend/modules/comercial/routes.py.bak:179:# remotos (SoftRestaurant/MPRO) desde la UI. Los endpoints afectados devolverán
/app/backend/modules/comercial/routes.py.bak:881:            if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:991:                            kpis = get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
/app/backend/modules/comercial/routes.py.bak:994:                        logging.warning(f"[BLINDAJE] Error SoftRestaurant {server['name']}: {sr_error}")
/app/backend/modules/comercial/routes.py.bak:1165:                        # Para modo HUB, NO usar caché MongoDB como fallback.
/app/backend/modules/comercial/routes.py.bak:1167:                        # MongoDB NO debe ser fuente productiva de datos.
/app/backend/modules/comercial/routes.py.bak:1170:                            # HUB: Reportar error SQL, NO usar caché MongoDB
/app/backend/modules/comercial/routes.py.bak:1171:                            logging.warning(f"[HUB-EDARSAHUB-ERROR] {server['name']}: Error leyendo EDARSAHUB SQL - NO hay fallback MongoDB")
/app/backend/modules/comercial/routes.py.bak:1189:                            # LIVE-C: Mantener fallback a caché MongoDB (conexión real fallida)
/app/backend/modules/comercial/routes.py.bak:1386:            elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:1388:                # FASE P0.5 MPRO: Ventas del Día lee EDARSAHUB SQL (NO API_LOCAL)
/app/backend/modules/comercial/routes.py.bak:1390:                logging.info(f"Procesando servidor MPRO: {server['name']}")
/app/backend/modules/comercial/routes.py.bak:1393:                    # MPRO Ventas del Día: Leer de EDARSAHUB SQL (NO API_LOCAL)
/app/backend/modules/comercial/routes.py.bak:1401:                            unidad_codigo_mpro = 'ORIGEN'
/app/backend/modules/comercial/routes.py.bak:1403:                            unidad_codigo_mpro = '130QRO'
/app/backend/modules/comercial/routes.py.bak:1405:                            unidad_codigo_mpro = server.get('unidad_negocio_id') or server_name_upper.replace(' LOCAL', '').strip()
/app/backend/modules/comercial/routes.py.bak:1408:                            fecha_op = get_fecha_operacion(unidad_codigo_mpro)
/app/backend/modules/comercial/routes.py.bak:1414:                        ventas_dia_snapshot = get_ventas_dia_abiertas(fecha_op, [unidad_codigo_mpro])
/app/backend/modules/comercial/routes.py.bak:1424:                            if vd_id == unidad_codigo_mpro:
/app/backend/modules/comercial/routes.py.bak:1443:                            kpis_mpro = {
/app/backend/modules/comercial/routes.py.bak:1448:                                'unidad': unidad_codigo_mpro, 'fuente': 'EDARSAHUB_SQL',
/app/backend/modules/comercial/routes.py.bak:1451:                            logging.info(f"[P0.5-MPRO] {server['name']}: EDARSAHUB SQL = ${total_estimado:,.2f}")
/app/backend/modules/comercial/routes.py.bak:1454:                                server=server, kpis=kpis_mpro,
/app/backend/modules/comercial/routes.py.bak:1463:                                sucursal=unidad_codigo_mpro,
/app/backend/modules/comercial/routes.py.bak:1469:                                totales[k] += kpis_mpro.get(k, 0)
/app/backend/modules/comercial/routes.py.bak:1470:                            totales["pendiente_cerrar"] += kpis_mpro.get("pendiente_cerrar", 0)
/app/backend/modules/comercial/routes.py.bak:1472:                            logging.warning(f"[P0.5-MPRO] {server['name']}: Sin datos en EDARSAHUB")
/app/backend/modules/comercial/routes.py.bak:1483:                                sucursal=unidad_codigo_mpro,
/app/backend/modules/comercial/routes.py.bak:1487:                    except Exception as mpro_error:
/app/backend/modules/comercial/routes.py.bak:1488:                        logging.error(f"[P0.5-MPRO] Error: {mpro_error}")
/app/backend/modules/comercial/routes.py.bak:1499:                            error_code="MPRO_EDARSAHUB_ERROR",
/app/backend/modules/comercial/routes.py.bak:1500:                            error_message=str(mpro_error)[:100],
/app/backend/modules/comercial/routes.py.bak:1504:                    # MPRO modo HUB (NO ventas del día)
/app/backend/modules/comercial/routes.py.bak:1506:                        unidades_mpro = get_kpis_mpro_por_sucursal(
/app/backend/modules/comercial/routes.py.bak:1510:                        logging.info(f"MPRO {server['name']}: {len(unidades_mpro)} unidades")
/app/backend/modules/comercial/routes.py.bak:1511:                        unidades_mpro = await filtrar_unidades_por_visibilidad(unidades_mpro, server['id'])
/app/backend/modules/comercial/routes.py.bak:1514:                        for unidad in unidades_mpro:
/app/backend/modules/comercial/routes.py.bak:1534:                                    source_period_mpro, source_live_mpro = "MPRO_API_LOCAL", "LOCAL_API"
/app/backend/modules/comercial/routes.py.bak:1535:                                    live_status_mpro = LiveStatus.LIVE_CONNECTED
/app/backend/modules/comercial/routes.py.bak:1537:                                    source_period_mpro, source_live_mpro = "EDARSAHUB_SQL", "EDARSAHUB_SQL"
/app/backend/modules/comercial/routes.py.bak:1538:                                    live_status_mpro = LiveStatus.LIVE_NOT_APPLICABLE
/app/backend/modules/comercial/routes.py.bak:1540:                                    source_period_mpro, source_live_mpro = "MPRO_SQL_DIRECT", "SQL_DIRECT"
/app/backend/modules/comercial/routes.py.bak:1541:                                    live_status_mpro = LiveStatus.LIVE_CONNECTED
/app/backend/modules/comercial/routes.py.bak:1546:                                    live_status=live_status_mpro,
/app/backend/modules/comercial/routes.py.bak:1551:                                    source_period=source_period_mpro,
/app/backend/modules/comercial/routes.py.bak:1552:                                    source_live=source_live_mpro,
/app/backend/modules/comercial/routes.py.bak:1566:                    except Exception as mpro_error:
/app/backend/modules/comercial/routes.py.bak:1567:                        logging.error(f"[P0-LOG] MPRO error: {server['name']}: {mpro_error}")
/app/backend/modules/comercial/routes.py.bak:1570:                        live_status, source_real_status = classify_connection_error(mpro_error, server)
/app/backend/modules/comercial/routes.py.bak:1583:                                error_code="MPRO_ERROR",
/app/backend/modules/comercial/routes.py.bak:1584:                                error_message=f"MPRO no disponible: {str(mpro_error)[:100]}",
/app/backend/modules/comercial/routes.py.bak:1590:                                logging.info(f"[P0-LOG] MPRO caché: {len(cached_list)} unidades")
/app/backend/modules/comercial/routes.py.bak:1604:                                        cache_warning="MPRO caída, usando caché",
/app/backend/modules/comercial/routes.py.bak:1622:                                    error_message="Sin datos MPRO",
/app/backend/modules/comercial/routes.py.bak:1678:    # FUENTE: EDARSAHUB.Unidades_Negocio (NO MongoDB)
/app/backend/modules/comercial/routes.py.bak:1686:            # Para SoftRestaurant: 1 unidad por servidor (sucursal_origen_id es NULL)
/app/backend/modules/comercial/routes.py.bak:1687:            # Para MPRO: usar server_id + sucursal_origen_id (ya corregido en P0)
/app/backend/modules/comercial/routes.py.bak:1688:            if sid and not suc:  # SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:1700:        2. Resolver desde EDARSAHUB por server_id (SoftRestaurant)
/app/backend/modules/comercial/routes.py.bak:1809:                    'system_type': snapshot.get('sistema_origen', 'MPRO'),
/app/backend/modules/comercial/routes.py.bak:2044:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:2109:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:2133:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:2210:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:2211:            # IMPLEMENTACIÓN MPRO (Abril 2026)
/app/backend/modules/comercial/routes.py.bak:2216:            # Filtro de sucursal para MPRO
/app/backend/modules/comercial/routes.py.bak:2229:            # NOTA: En MPRO, la tabla Venta tiene Vn_Cantidad_1 y Vn_Precio_Neto_Importe
/app/backend/modules/comercial/routes.py.bak:2263:            # Ventas por vendedor (top 10) - En MPRO usar tabla Vendedor
/app/backend/modules/comercial/routes.py.bak:2381:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:2455:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:2481:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:2488:            # clasificacionventa puede no existir en algunas versiones de SoftRestaurant
/app/backend/modules/comercial/routes.py.bak:2668:        # PROHIBIDO: Abrir conexión a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py.bak:2683:            conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:2791:                conn_hoy = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:2900:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:2984:    # ARQUITECTURA: Obtener nombre de unidad desde EDARSAHUB (primario) o MongoDB (LEGACY_FALLBACK)
/app/backend/modules/comercial/routes.py.bak:2987:        logging.warning(f"[LEGACY_FALLBACK] Mesas: Nombre de sucursal {sucursal} obtenido de MongoDB")
/app/backend/modules/comercial/routes.py.bak:2995:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:3048:            # BLINDAJE: Usar nombre obtenido de MongoDB
/app/backend/modules/comercial/routes.py.bak:3103:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:3104:            # BLINDAJE: Definir f_fin para MPRO
/app/backend/modules/comercial/routes.py.bak:3107:            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
/app/backend/modules/comercial/routes.py.bak:3120:            # KPIs generales de mesas para MPRO
/app/backend/modules/comercial/routes.py.bak:3159:            # BLINDAJE MPRO: Usar nombre de MongoDB (ya obtenido arriba), con fallback a SQL si no se encontró
/app/backend/modules/comercial/routes.py.bak:3160:            nombre_final_mpro = nombre_unidad_mostrar
/app/backend/modules/comercial/routes.py.bak:3161:            # Si MongoDB no encontró el nombre (aún es server['name']), intentar con SQL
/app/backend/modules/comercial/routes.py.bak:3162:            if nombre_final_mpro == server['name'] and sucursal:
/app/backend/modules/comercial/routes.py.bak:3174:                            nombre_final_mpro = result_nombre[0]['nombre']
/app/backend/modules/comercial/routes.py.bak:3179:                "nombre": nombre_final_mpro,
/app/backend/modules/comercial/routes.py.bak:3192:            # Rotación por hora para MPRO
/app/backend/modules/comercial/routes.py.bak:3295:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:3296:            # Formato de fecha para SoftRestaurant (YYYYMMDD)
/app/backend/modules/comercial/routes.py.bak:3394:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:3395:            # Formato de fecha para MPRO (YYYYMMDD)
/app/backend/modules/comercial/routes.py.bak:3408:                sucursal_lower == 'mpro'
/app/backend/modules/comercial/routes.py.bak:3420:            logging.info(f"Detalle MPRO: f_ini={f_ini}, f_fin={f_fin}, sucursal={sucursal}, skip_filter={skip_sucursal_filter}, sucursal_filter={sucursal_filter}")
/app/backend/modules/comercial/routes.py.bak:3422:            # Query para MPRO - usa Venta_Encabezado con Comanda para PAX
/app/backend/modules/comercial/routes.py.bak:3441:            logging.info(f"Query MPRO detalle: {query_detalle[:200]}...")
/app/backend/modules/comercial/routes.py.bak:3572:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:3573:            # Formato YYYYMMDD para SoftRestaurant - usando CONVERT para evitar errores de conversión
/app/backend/modules/comercial/routes.py.bak:3606:            # NOTA: En SoftRestaurant la tabla de detalle es 'cheqdet' (no 'chequedetalle')
/app/backend/modules/comercial/routes.py.bak:3612:    'SoftRestaurant' as categoria,
/app/backend/modules/comercial/routes.py.bak:3659:                logging.warning(f"Precios Constantes SoftRestaurant {server['name']}: Sin datos en período base {periodo_base}")
/app/backend/modules/comercial/routes.py.bak:3690:            logging.info(f"SoftRestaurant - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
/app/backend/modules/comercial/routes.py.bak:3851:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:3852:            # Para MPRO - Las ventas están en la tabla 'venta' directamente
/app/backend/modules/comercial/routes.py.bak:3856:            # El frontend envía nombres (ORIGEN, QUERETARO) pero MPRO usa códigos (0023, 0021)
/app/backend/modules/comercial/routes.py.bak:3868:                logging.info(f"Precios Constantes MPRO: Traduciendo sucursal '{sucursal}' -> '{sucursal_codigo}'")
/app/backend/modules/comercial/routes.py.bak:3870:            # Filtro de sucursal - en MPRO se relaciona venta con sucursal
/app/backend/modules/comercial/routes.py.bak:3876:            query_ventas_reales_mpro = f"""
/app/backend/modules/comercial/routes.py.bak:3886:                server['username'], server['password'], query_ventas_reales_mpro
/app/backend/modules/comercial/routes.py.bak:3937:                logging.warning(f"Precios Constantes MPRO {server['name']}: Sin datos en período base {periodo_base}")
/app/backend/modules/comercial/routes.py.bak:3967:            logging.info(f"MPRO - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
/app/backend/modules/comercial/routes.py.bak:4129:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py.bak:4247:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:4402:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:4403:            # Implementación para MPRO
/app/backend/modules/comercial/routes.py.bak:4406:            # BLINDAJE (Abril 2026): Campo de cancelación en MPRO es Es_Cve_Estado, NO Vn_Cancelacion
/app/backend/modules/comercial/routes.py.bak:4410:                # CORRECCIÓN (Abril 2026): En MPRO, el nombre del vendedor está en tabla Vendedor, NO en Empleado
/app/backend/modules/comercial/routes.py.bak:4528:            # Comparativos para MPRO - helper interno
/app/backend/modules/comercial/routes.py.bak:4530:            def get_pax_mpro(f):
/app/backend/modules/comercial/routes.py.bak:4542:            pax_ant, total_ant = get_pax_mpro(fecha_dia_ant)
/app/backend/modules/comercial/routes.py.bak:4543:            pax_mes, total_mes = get_pax_mpro(fecha_mes_ant)
/app/backend/modules/comercial/routes.py.bak:4544:            pax_ano, total_ano = get_pax_mpro(fecha_ano_ant)
/app/backend/modules/comercial/routes.py.bak:4625:    Soporta SoftRestaurant y MPRO.
/app/backend/modules/comercial/routes.py.bak:4827:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:4839:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant para obtener "último día"
/app/backend/modules/comercial/routes.py.bak:4849:            logging.info(f"[NO-LIVE] SoftRestaurant Query - Período: {f_ini} a {f_fin} (EDARSAHUB-ONLY)")
/app/backend/modules/comercial/routes.py.bak:4914:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py.bak:4965:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py.bak:4967:            # FASE 7-FIX: EDARSAHUB COMO FUENTE PRINCIPAL PARA MPRO
/app/backend/modules/comercial/routes.py.bak:4969:            # MISMO FIX que SoftRestaurant: Usar EDARSAHUB primero.
/app/backend/modules/comercial/routes.py.bak:4976:            edarsahub_kpis_mpro = get_dashboard_kpis_from_edarsahub(
/app/backend/modules/comercial/routes.py.bak:4987:            if edarsahub_kpis_mpro:
/app/backend/modules/comercial/routes.py.bak:4988:                # EDARSAHUB tiene datos MPRO - usar estos como fuente principal
/app/backend/modules/comercial/routes.py.bak:4989:                logging.info(f"[DASHBOARD-FIX-MPRO] {server['name']}: Usando datos de EDARSAHUB (ventas=${edarsahub_kpis_mpro['ventas_periodo']:,.2f})")
/app/backend/modules/comercial/routes.py.bak:4993:                    "source_message": f"Datos consolidados de EDARSAHUB ({edarsahub_kpis_mpro['registros_consultados']} días)",
/app/backend/modules/comercial/routes.py.bak:4994:                    "source_type": edarsahub_kpis_mpro['source'],
/app/backend/modules/comercial/routes.py.bak:5000:                        "ventas_periodo": edarsahub_kpis_mpro['ventas_periodo'],
/app/backend/modules/comercial/routes.py.bak:5001:                        "ticket_promedio": edarsahub_kpis_mpro['ticket_promedio'],
/app/backend/modules/comercial/routes.py.bak:5002:                        "cheques_total": edarsahub_kpis_mpro['cheques_total'],
/app/backend/modules/comercial/routes.py.bak:5003:                        "pax_total": edarsahub_kpis_mpro['pax_total'],
/app/backend/modules/comercial/routes.py.bak:5004:                        "pax_promedio": edarsahub_kpis_mpro['pax_promedio'],
/app/backend/modules/comercial/routes.py.bak:5005:                        "consumo_persona": edarsahub_kpis_mpro['consumo_persona'],
/app/backend/modules/comercial/routes.py.bak:5006:                        "mesas_atendidas": edarsahub_kpis_mpro['mesas_atendidas'],
/app/backend/modules/comercial/routes.py.bak:5007:                        "rotacion_mesas": edarsahub_kpis_mpro['rotacion_mesas'],
/app/backend/modules/comercial/routes.py.bak:5008:                        "venta_por_hora": edarsahub_kpis_mpro['venta_por_hora']
/app/backend/modules/comercial/routes.py.bak:5011:                        "vs_periodo_anterior": edarsahub_kpis_mpro['vs_periodo_anterior'],
/app/backend/modules/comercial/routes.py.bak:5012:                        "vs_ano_anterior": edarsahub_kpis_mpro['vs_ano_anterior'],
/app/backend/modules/comercial/routes.py.bak:5013:                        "vs_presupuesto": edarsahub_kpis_mpro['vs_presupuesto'],
/app/backend/modules/comercial/routes.py.bak:5015:                        "ventas_anterior": edarsahub_kpis_mpro['ventas_anterior'],
/app/backend/modules/comercial/routes.py.bak:5016:                        "ventas_ano_anterior": edarsahub_kpis_mpro['ventas_ano_anterior']
/app/backend/modules/comercial/routes.py.bak:5023:            # FASE 1B-R1: CORRECCIÓN NO-LIVE DASHBOARD MPRO
/app/backend/modules/comercial/routes.py.bak:5025:            # PROHIBIDO: Abrir conexión remota a MPRO/Enterprise
/app/backend/modules/comercial/routes.py.bak:5028:            logging.warning(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: EDARSAHUB sin datos vigentes, verificando snapshot histórico")
/app/backend/modules/comercial/routes.py.bak:5033:            stale_snapshot_mpro = get_last_valid_snapshot_edarsahub(server_id)
/app/backend/modules/comercial/routes.py.bak:5035:            if stale_snapshot_mpro:
/app/backend/modules/comercial/routes.py.bak:5037:                logging.info(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: Retornando datos STALE de {stale_snapshot_mpro['fecha_snapshot']}")
/app/backend/modules/comercial/routes.py.bak:5041:                    "source_message": f"Datos históricos de EDARSAHUB. Última sincronización: {stale_snapshot_mpro['fecha_snapshot']}. Datos pueden estar desactualizados.",
/app/backend/modules/comercial/routes.py.bak:5047:                    "kpis": stale_snapshot_mpro.get('kpis'),
/app/backend/modules/comercial/routes.py.bak:5048:                    "comparativo": stale_snapshot_mpro.get('comparativo'),
/app/backend/modules/comercial/routes.py.bak:5051:                        "mensaje": f"Datos históricos. Última sincronización: {stale_snapshot_mpro['fecha_snapshot']}"
/app/backend/modules/comercial/routes.py.bak:5057:            logging.warning(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: Sin datos en EDARSAHUB, retornando SIN_DATOS_EDARSAHUB")
/app/backend/modules/comercial/routes_listas_competidores.py:8:- CERO MongoDB
/app/backend/modules/comercial/routes_alertas_margen.py:4:EDARSAHUB SQL es el cerebro. CERO MongoDB.
/app/backend/modules/comercial/repository.py:7:- ELIMINADA dependencia de MongoDB completamente
/app/backend/modules/comercial/repository.py:45:# DEPRECADO: MongoDB ya no se usa (Mayo 2026)
/app/backend/modules/comercial/repository.py:49:    """DEPRECADO: MongoDB eliminado. No hace nada."""
/app/backend/modules/comercial/repository.py:54:    """DEPRECADO: MongoDB eliminado. Retorna None siempre."""
/app/backend/modules/comercial/repository.py:82:    Garantiza paridad estructural con el esquema original de MongoDB.
/app/backend/modules/comercial/repository.py:153:        WHERE (id = '{server_id}' OR mongodb_id = '{server_id}')
/app/backend/modules/comercial/repository.py:205:    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
/app/backend/modules/comercial/repository.py:218:    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
/app/backend/modules/comercial/repository.py:292:        # Construir condición para sucursal_origen_id (puede ser NULL para SoftRestaurant)
/app/backend/modules/comercial/repository.py:296:            # Para SoftRestaurant sin código, buscar por server_id con sucursal_origen_id NULL
/app/backend/modules/comercial/repository.py:327:    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
/app/backend/modules/comercial/repository.py:361:# QUERIES SQL - VENTAS MPRO
/app/backend/modules/comercial/repository.py:364:def query_ventas_mpro(server: Dict, mes: int, anio: int, sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/comercial/repository.py:366:    Obtiene ventas de MPRO para un mes/año específico.
/app/backend/modules/comercial/repository.py:390:def query_ventas_softrestaurant(server: Dict, mes: int, anio: int) -> List[Dict]:
/app/backend/modules/comercial/repository.py:392:    Obtiene ventas de SoftRestaurant para un mes/año específico.
/app/backend/modules/comercial/repository.py:423:def query_ticket_perfecto_mpro(server: Dict, mes: int, anio: int, sucursal_id: str = None) -> List[Dict]:
/app/backend/modules/comercial/repository.py:425:    Obtiene datos de ticket perfecto para MPRO.
/app/backend/modules/comercial/repository.py:752:    'query_ventas_mpro',
/app/backend/modules/comercial/repository.py:753:    'query_ventas_softrestaurant',
/app/backend/modules/comercial/repository.py:755:    'query_ticket_perfecto_mpro',
/app/backend/modules/comercial/historical_kpis_repository.py:8:EDARSAHUB SQL es el cerebro. MongoDB NO es destino final de históricos.
/app/backend/modules/comercial/historical_kpis_repository.py:51:    """Obtiene credenciales de EDARSAHUB desde MongoDB servers."""
/app/backend/modules/comercial/historical_kpis_repository.py:57:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/comercial/historical_kpis_repository.py:59:    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
/app/backend/modules/comercial/historical_kpis_repository.py:475:# MIGRACIÓN DE STAGING MONGODB A SQL
/app/backend/modules/comercial/historical_kpis_repository.py:483:    Migra KPIs de staging en MongoDB a destino final en SQL.
/app/backend/modules/comercial/historical_kpis_repository.py:492:    from motor.motor_asyncio import AsyncIOMotorClient
/app/backend/modules/comercial/historical_kpis_repository.py:494:    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
/app/backend/modules/comercial/historical_kpis_repository.py:519:            # Mapear documento MongoDB a registro SQL
/app/backend/modules/comercial/kpis_repository.py:25:# INYECCIÓN DE DEPENDENCIA: MongoDB
/app/backend/modules/comercial/kpis_repository.py:33:    DEPRECADO: MongoDB ya no se usa para KPIs.
/app/backend/modules/comercial/kpis_repository.py:39:    logging.warning("[COMERCIAL] KPIs repository - MongoDB deprecado")
/app/backend/modules/comercial/kpis_repository.py:44:    DEPRECADO: MongoDB ya no se usa.
/app/backend/modules/comercial/kpis_repository.py:49:        logging.debug("[COMERCIAL] KPIs get_db() - MongoDB deprecado, retornando None")
/app/backend/modules/comercial/README_BLINDAJE.md:28:| SoftRestaurant | SQL (cheques+turnos) | SQL (tempcheques) |
/app/backend/modules/comercial/README_BLINDAJE.md:29:| MPRO | SQL (Venta_Encabezado) | API local |
/app/backend/modules/comercial/services/listas_competidores_service.py:10:- CERO MongoDB
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py:13:- CERO MongoDB
/app/backend/modules/comercial/services/pricing_ai_service.py:15:- NO usar MongoDB (todo en EDARSAHUB SQL)
/app/backend/modules/comercial/services/metricas_ia_service.py:16:- NO usar MongoDB
/app/backend/modules/comercial/routes.py:27:- ✅ Adapters (APIs locales MPRO) migrados a adapters.py
/app/backend/modules/comercial/routes.py:40:   - APIS_MPRO_LOCALES (configuración)
/app/backend/modules/comercial/routes.py:41:   - query_api_mpro_local()
/app/backend/modules/comercial/routes.py:46:   - get_kpis_softrestaurant()
/app/backend/modules/comercial/routes.py:47:   - get_kpis_mpro()
/app/backend/modules/comercial/routes.py:48:   - get_kpis_mpro_por_sucursal()
/app/backend/modules/comercial/routes.py:100:    get_kpis_softrestaurant,
/app/backend/modules/comercial/routes.py:101:    get_kpis_mpro,
/app/backend/modules/comercial/routes.py:102:    get_kpis_mpro_por_sucursal,
/app/backend/modules/comercial/routes.py:113:from modules.comercial.queries.softrestaurant import query_ventas_periodo_sr
/app/backend/modules/comercial/routes.py:114:# BLOQUE 5.2: Import de query MPRO centralizada con filtro flexible
/app/backend/modules/comercial/routes.py:115:from modules.comercial.queries.mpro import query_ventas_periodo_mpro_con_filtro_flexible
/app/backend/modules/comercial/routes.py:159:    is_mpro_system,
/app/backend/modules/comercial/routes.py:160:    is_softrestaurant_system,
/app/backend/modules/comercial/routes.py:179:# remotos (SoftRestaurant/MPRO) desde la UI. Los endpoints afectados devolverán
/app/backend/modules/comercial/routes.py:881:            if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:991:                            kpis = get_kpis_softrestaurant(server, fecha_ini, fecha_fin, fecha_ini_ant, fecha_fin_ant,
/app/backend/modules/comercial/routes.py:994:                        logging.warning(f"[BLINDAJE] Error SoftRestaurant {server['name']}: {sr_error}")
/app/backend/modules/comercial/routes.py:1165:                        # Para modo HUB, NO usar caché MongoDB como fallback.
/app/backend/modules/comercial/routes.py:1167:                        # MongoDB NO debe ser fuente productiva de datos.
/app/backend/modules/comercial/routes.py:1170:                            # HUB: Reportar error SQL, NO usar caché MongoDB
/app/backend/modules/comercial/routes.py:1171:                            logging.warning(f"[HUB-EDARSAHUB-ERROR] {server['name']}: Error leyendo EDARSAHUB SQL - NO hay fallback MongoDB")
/app/backend/modules/comercial/routes.py:1189:                            # LIVE-C: Mantener fallback a caché MongoDB (conexión real fallida)
/app/backend/modules/comercial/routes.py:1386:            elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:1388:                # FASE P0.5 MPRO: Ventas del Día lee EDARSAHUB SQL (NO API_LOCAL)
/app/backend/modules/comercial/routes.py:1390:                logging.info(f"Procesando servidor MPRO: {server['name']}")
/app/backend/modules/comercial/routes.py:1393:                    # MPRO Ventas del Día: Leer de EDARSAHUB SQL (NO API_LOCAL)
/app/backend/modules/comercial/routes.py:1401:                            unidad_codigo_mpro = 'ORIGEN'
/app/backend/modules/comercial/routes.py:1403:                            unidad_codigo_mpro = '130QRO'
/app/backend/modules/comercial/routes.py:1405:                            unidad_codigo_mpro = server.get('unidad_negocio_id') or server_name_upper.replace(' LOCAL', '').strip()
/app/backend/modules/comercial/routes.py:1408:                            fecha_op = get_fecha_operacion(unidad_codigo_mpro)
/app/backend/modules/comercial/routes.py:1414:                        ventas_dia_snapshot = get_ventas_dia_abiertas(fecha_op, [unidad_codigo_mpro])
/app/backend/modules/comercial/routes.py:1424:                            if vd_id == unidad_codigo_mpro:
/app/backend/modules/comercial/routes.py:1443:                            kpis_mpro = {
/app/backend/modules/comercial/routes.py:1448:                                'unidad': unidad_codigo_mpro, 'fuente': 'EDARSAHUB_SQL',
/app/backend/modules/comercial/routes.py:1451:                            logging.info(f"[P0.5-MPRO] {server['name']}: EDARSAHUB SQL = ${total_estimado:,.2f}")
/app/backend/modules/comercial/routes.py:1454:                                server=server, kpis=kpis_mpro,
/app/backend/modules/comercial/routes.py:1463:                                sucursal=unidad_codigo_mpro,
/app/backend/modules/comercial/routes.py:1469:                                totales[k] += kpis_mpro.get(k, 0)
/app/backend/modules/comercial/routes.py:1470:                            totales["pendiente_cerrar"] += kpis_mpro.get("pendiente_cerrar", 0)
/app/backend/modules/comercial/routes.py:1472:                            logging.warning(f"[P0.5-MPRO] {server['name']}: Sin datos en EDARSAHUB")
/app/backend/modules/comercial/routes.py:1483:                                sucursal=unidad_codigo_mpro,
/app/backend/modules/comercial/routes.py:1487:                    except Exception as mpro_error:
/app/backend/modules/comercial/routes.py:1488:                        logging.error(f"[P0.5-MPRO] Error: {mpro_error}")
/app/backend/modules/comercial/routes.py:1499:                            error_code="MPRO_EDARSAHUB_ERROR",
/app/backend/modules/comercial/routes.py:1500:                            error_message=str(mpro_error)[:100],
/app/backend/modules/comercial/routes.py:1504:                    # MPRO modo HUB (NO ventas del día)
/app/backend/modules/comercial/routes.py:1506:                        unidades_mpro = get_kpis_mpro_por_sucursal(
/app/backend/modules/comercial/routes.py:1510:                        logging.info(f"MPRO {server['name']}: {len(unidades_mpro)} unidades")
/app/backend/modules/comercial/routes.py:1511:                        unidades_mpro = await filtrar_unidades_por_visibilidad(unidades_mpro, server['id'])
/app/backend/modules/comercial/routes.py:1514:                        for unidad in unidades_mpro:
/app/backend/modules/comercial/routes.py:1534:                                    source_period_mpro, source_live_mpro = "MPRO_API_LOCAL", "LOCAL_API"
/app/backend/modules/comercial/routes.py:1535:                                    live_status_mpro = LiveStatus.LIVE_CONNECTED
/app/backend/modules/comercial/routes.py:1537:                                    source_period_mpro, source_live_mpro = "EDARSAHUB_SQL", "EDARSAHUB_SQL"
/app/backend/modules/comercial/routes.py:1538:                                    live_status_mpro = LiveStatus.LIVE_NOT_APPLICABLE
/app/backend/modules/comercial/routes.py:1540:                                    source_period_mpro, source_live_mpro = "MPRO_SQL_DIRECT", "SQL_DIRECT"
/app/backend/modules/comercial/routes.py:1541:                                    live_status_mpro = LiveStatus.LIVE_CONNECTED
/app/backend/modules/comercial/routes.py:1546:                                    live_status=live_status_mpro,
/app/backend/modules/comercial/routes.py:1551:                                    source_period=source_period_mpro,
/app/backend/modules/comercial/routes.py:1552:                                    source_live=source_live_mpro,
/app/backend/modules/comercial/routes.py:1566:                    except Exception as mpro_error:
/app/backend/modules/comercial/routes.py:1567:                        logging.error(f"[P0-LOG] MPRO error: {server['name']}: {mpro_error}")
/app/backend/modules/comercial/routes.py:1570:                        live_status, source_real_status = classify_connection_error(mpro_error, server)
/app/backend/modules/comercial/routes.py:1583:                                error_code="MPRO_ERROR",
/app/backend/modules/comercial/routes.py:1584:                                error_message=f"MPRO no disponible: {str(mpro_error)[:100]}",
/app/backend/modules/comercial/routes.py:1590:                                logging.info(f"[P0-LOG] MPRO caché: {len(cached_list)} unidades")
/app/backend/modules/comercial/routes.py:1604:                                        cache_warning="MPRO caída, usando caché",
/app/backend/modules/comercial/routes.py:1622:                                    error_message="Sin datos MPRO",
/app/backend/modules/comercial/routes.py:1678:    # FUENTE: EDARSAHUB.Unidades_Negocio (NO MongoDB)
/app/backend/modules/comercial/routes.py:1686:            # Para SoftRestaurant: 1 unidad por servidor (sucursal_origen_id es NULL)
/app/backend/modules/comercial/routes.py:1687:            # Para MPRO: usar server_id + sucursal_origen_id (ya corregido en P0)
/app/backend/modules/comercial/routes.py:1688:            if sid and not suc:  # SoftRestaurant
/app/backend/modules/comercial/routes.py:1700:        2. Resolver desde EDARSAHUB por server_id (SoftRestaurant)
/app/backend/modules/comercial/routes.py:1809:                    'system_type': snapshot.get('sistema_origen', 'MPRO'),
/app/backend/modules/comercial/routes.py:2044:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2109:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py:2133:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:2210:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:2211:            # IMPLEMENTACIÓN MPRO (Abril 2026)
/app/backend/modules/comercial/routes.py:2216:            # Filtro de sucursal para MPRO
/app/backend/modules/comercial/routes.py:2229:            # NOTA: En MPRO, la tabla Venta tiene Vn_Cantidad_1 y Vn_Precio_Neto_Importe
/app/backend/modules/comercial/routes.py:2263:            # Ventas por vendedor (top 10) - En MPRO usar tabla Vendedor
/app/backend/modules/comercial/routes.py:2381:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2455:    # FASE 3A.3: Incluir system_type para evitar colisiones MPRO/SoftRestaurant
/app/backend/modules/comercial/routes.py:2481:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:2488:            # clasificacionventa puede no existir en algunas versiones de SoftRestaurant
/app/backend/modules/comercial/routes.py:2668:        # PROHIBIDO: Abrir conexión a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py:2683:            conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2791:                conn_hoy = pymssql.connect(
/app/backend/modules/comercial/routes.py:2900:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:2984:    # ARQUITECTURA: Obtener nombre de unidad desde EDARSAHUB (primario) o MongoDB (LEGACY_FALLBACK)
/app/backend/modules/comercial/routes.py:2987:        logging.warning(f"[LEGACY_FALLBACK] Mesas: Nombre de sucursal {sucursal} obtenido de MongoDB")
/app/backend/modules/comercial/routes.py:2995:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:3048:            # BLINDAJE: Usar nombre obtenido de MongoDB
/app/backend/modules/comercial/routes.py:3103:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:3104:            # BLINDAJE: Definir f_fin para MPRO
/app/backend/modules/comercial/routes.py:3107:            # Filtro de sucursal para MPRO - no filtrar si es "default" o nombre del servidor
/app/backend/modules/comercial/routes.py:3120:            # KPIs generales de mesas para MPRO
/app/backend/modules/comercial/routes.py:3159:            # BLINDAJE MPRO: Usar nombre de MongoDB (ya obtenido arriba), con fallback a SQL si no se encontró
/app/backend/modules/comercial/routes.py:3160:            nombre_final_mpro = nombre_unidad_mostrar
/app/backend/modules/comercial/routes.py:3161:            # Si MongoDB no encontró el nombre (aún es server['name']), intentar con SQL
/app/backend/modules/comercial/routes.py:3162:            if nombre_final_mpro == server['name'] and sucursal:
/app/backend/modules/comercial/routes.py:3174:                            nombre_final_mpro = result_nombre[0]['nombre']
/app/backend/modules/comercial/routes.py:3179:                "nombre": nombre_final_mpro,
/app/backend/modules/comercial/routes.py:3192:            # Rotación por hora para MPRO
/app/backend/modules/comercial/routes.py:3295:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:3296:            # Formato de fecha para SoftRestaurant (YYYYMMDD)
/app/backend/modules/comercial/routes.py:3394:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:3395:            # Formato de fecha para MPRO (YYYYMMDD)
/app/backend/modules/comercial/routes.py:3408:                sucursal_lower == 'mpro'
/app/backend/modules/comercial/routes.py:3420:            logging.info(f"Detalle MPRO: f_ini={f_ini}, f_fin={f_fin}, sucursal={sucursal}, skip_filter={skip_sucursal_filter}, sucursal_filter={sucursal_filter}")
/app/backend/modules/comercial/routes.py:3422:            # Query para MPRO - usa Venta_Encabezado con Comanda para PAX
/app/backend/modules/comercial/routes.py:3441:            logging.info(f"Query MPRO detalle: {query_detalle[:200]}...")
/app/backend/modules/comercial/routes.py:3572:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:3573:            # Formato YYYYMMDD para SoftRestaurant - usando CONVERT para evitar errores de conversión
/app/backend/modules/comercial/routes.py:3606:            # NOTA: En SoftRestaurant la tabla de detalle es 'cheqdet' (no 'chequedetalle')
/app/backend/modules/comercial/routes.py:3612:    'SoftRestaurant' as categoria,
/app/backend/modules/comercial/routes.py:3659:                logging.warning(f"Precios Constantes SoftRestaurant {server['name']}: Sin datos en período base {periodo_base}")
/app/backend/modules/comercial/routes.py:3690:            logging.info(f"SoftRestaurant - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
/app/backend/modules/comercial/routes.py:3851:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:3852:            # Para MPRO - Las ventas están en la tabla 'venta' directamente
/app/backend/modules/comercial/routes.py:3856:            # El frontend envía nombres (ORIGEN, QUERETARO) pero MPRO usa códigos (0023, 0021)
/app/backend/modules/comercial/routes.py:3868:                logging.info(f"Precios Constantes MPRO: Traduciendo sucursal '{sucursal}' -> '{sucursal_codigo}'")
/app/backend/modules/comercial/routes.py:3870:            # Filtro de sucursal - en MPRO se relaciona venta con sucursal
/app/backend/modules/comercial/routes.py:3876:            query_ventas_reales_mpro = f"""
/app/backend/modules/comercial/routes.py:3886:                server['username'], server['password'], query_ventas_reales_mpro
/app/backend/modules/comercial/routes.py:3937:                logging.warning(f"Precios Constantes MPRO {server['name']}: Sin datos en período base {periodo_base}")
/app/backend/modules/comercial/routes.py:3967:            logging.info(f"MPRO - Ventas reales: {ventas_reales_periodo}, Suma productos: {suma_productos_actual}, Factor: {factor_ajuste}")
/app/backend/modules/comercial/routes.py:4129:        conn = pymssql.connect(
/app/backend/modules/comercial/routes.py:4236:    Soporta SoftRestaurant y MPRO.
/app/backend/modules/comercial/routes.py:4438:        if is_softrestaurant_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:4450:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant para obtener "último día"
/app/backend/modules/comercial/routes.py:4460:            logging.info(f"[NO-LIVE] SoftRestaurant Query - Período: {f_ini} a {f_fin} (EDARSAHUB-ONLY)")
/app/backend/modules/comercial/routes.py:4525:            # PROHIBIDO: Abrir conexión remota a SoftRestaurant/MPRO/Enterprise
/app/backend/modules/comercial/routes.py:4576:        elif is_mpro_system(server.get('system_type')):
/app/backend/modules/comercial/routes.py:4578:            # FASE 7-FIX: EDARSAHUB COMO FUENTE PRINCIPAL PARA MPRO
/app/backend/modules/comercial/routes.py:4580:            # MISMO FIX que SoftRestaurant: Usar EDARSAHUB primero.
/app/backend/modules/comercial/routes.py:4587:            edarsahub_kpis_mpro = get_dashboard_kpis_from_edarsahub(
/app/backend/modules/comercial/routes.py:4598:            if edarsahub_kpis_mpro:
/app/backend/modules/comercial/routes.py:4599:                # EDARSAHUB tiene datos MPRO - usar estos como fuente principal
/app/backend/modules/comercial/routes.py:4600:                logging.info(f"[DASHBOARD-FIX-MPRO] {server['name']}: Usando datos de EDARSAHUB (ventas=${edarsahub_kpis_mpro['ventas_periodo']:,.2f})")
/app/backend/modules/comercial/routes.py:4604:                    "source_message": f"Datos consolidados de EDARSAHUB ({edarsahub_kpis_mpro['registros_consultados']} días)",
/app/backend/modules/comercial/routes.py:4605:                    "source_type": edarsahub_kpis_mpro['source'],
/app/backend/modules/comercial/routes.py:4611:                        "ventas_periodo": edarsahub_kpis_mpro['ventas_periodo'],
/app/backend/modules/comercial/routes.py:4612:                        "ticket_promedio": edarsahub_kpis_mpro['ticket_promedio'],
/app/backend/modules/comercial/routes.py:4613:                        "cheques_total": edarsahub_kpis_mpro['cheques_total'],
/app/backend/modules/comercial/routes.py:4614:                        "pax_total": edarsahub_kpis_mpro['pax_total'],
/app/backend/modules/comercial/routes.py:4615:                        "pax_promedio": edarsahub_kpis_mpro['pax_promedio'],
/app/backend/modules/comercial/routes.py:4616:                        "consumo_persona": edarsahub_kpis_mpro['consumo_persona'],
/app/backend/modules/comercial/routes.py:4617:                        "mesas_atendidas": edarsahub_kpis_mpro['mesas_atendidas'],
/app/backend/modules/comercial/routes.py:4618:                        "rotacion_mesas": edarsahub_kpis_mpro['rotacion_mesas'],
/app/backend/modules/comercial/routes.py:4619:                        "venta_por_hora": edarsahub_kpis_mpro['venta_por_hora']
/app/backend/modules/comercial/routes.py:4622:                        "vs_periodo_anterior": edarsahub_kpis_mpro['vs_periodo_anterior'],
/app/backend/modules/comercial/routes.py:4623:                        "vs_ano_anterior": edarsahub_kpis_mpro['vs_ano_anterior'],
/app/backend/modules/comercial/routes.py:4624:                        "vs_presupuesto": edarsahub_kpis_mpro['vs_presupuesto'],
/app/backend/modules/comercial/routes.py:4626:                        "ventas_anterior": edarsahub_kpis_mpro['ventas_anterior'],
/app/backend/modules/comercial/routes.py:4627:                        "ventas_ano_anterior": edarsahub_kpis_mpro['ventas_ano_anterior']
/app/backend/modules/comercial/routes.py:4634:            # FASE 1B-R1: CORRECCIÓN NO-LIVE DASHBOARD MPRO
/app/backend/modules/comercial/routes.py:4636:            # PROHIBIDO: Abrir conexión remota a MPRO/Enterprise
/app/backend/modules/comercial/routes.py:4639:            logging.warning(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: EDARSAHUB sin datos vigentes, verificando snapshot histórico")
/app/backend/modules/comercial/routes.py:4644:            stale_snapshot_mpro = get_last_valid_snapshot_edarsahub(server_id)
/app/backend/modules/comercial/routes.py:4646:            if stale_snapshot_mpro:
/app/backend/modules/comercial/routes.py:4648:                logging.info(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: Retornando datos STALE de {stale_snapshot_mpro['fecha_snapshot']}")
/app/backend/modules/comercial/routes.py:4652:                    "source_message": f"Datos históricos de EDARSAHUB. Última sincronización: {stale_snapshot_mpro['fecha_snapshot']}. Datos pueden estar desactualizados.",
/app/backend/modules/comercial/routes.py:4658:                    "kpis": stale_snapshot_mpro.get('kpis'),
/app/backend/modules/comercial/routes.py:4659:                    "comparativo": stale_snapshot_mpro.get('comparativo'),
/app/backend/modules/comercial/routes.py:4662:                        "mensaje": f"Datos históricos. Última sincronización: {stale_snapshot_mpro['fecha_snapshot']}"
/app/backend/modules/comercial/routes.py:4668:            logging.warning(f"[DASHBOARD-NO-LIVE-MPRO] {server['name']}: Sin datos en EDARSAHUB, retornando SIN_DATOS_EDARSAHUB")
```

## Compilación Python

```text
/app/backend/modules/comercial/service.py
/app/backend/modules/comercial/routes_pricing_ai.py
/app/backend/modules/comercial/cache_service.py
/app/backend/modules/comercial/__init__.py
/app/backend/modules/comercial/queries/__init__.py
/app/backend/modules/comercial/queries/hub.py
/app/backend/modules/comercial/queries/mpro.py
/app/backend/modules/comercial/queries/softrestaurant.py
/app/backend/modules/comercial/adapters.py
/app/backend/modules/comercial/routes_precios_sugeridos.py
/app/backend/modules/comercial/crm_router.py
/app/backend/modules/comercial/inteligencia_comercial_routes.py
/app/backend/modules/comercial/alertas_margen_service.py
/app/backend/modules/comercial/inteligencia_repository.py
/app/backend/modules/comercial/alertas_margen_repository.py
/app/backend/modules/comercial/routes_pricing_ia.py
/app/backend/modules/comercial/routes_competidores_enterprise.py
/app/backend/modules/comercial/rentabilidad.py
/app/backend/modules/comercial/routes_listas_competidores.py
/app/backend/modules/comercial/routes_alertas_margen.py
/app/backend/modules/comercial/repository.py
/app/backend/modules/comercial/historical_kpis_repository.py
/app/backend/modules/comercial/kpis_repository.py
/app/backend/modules/comercial/services/impuestos_service.py
/app/backend/modules/comercial/services/__init__.py
/app/backend/modules/comercial/services/listas_competidores_service.py
/app/backend/modules/comercial/services/competidores_service.py
/app/backend/modules/comercial/services/competidores_enterprise_service.py
/app/backend/modules/comercial/services/benchmark_service.py
/app/backend/modules/comercial/services/precios_sugeridos_consolidado_service.py
/app/backend/modules/comercial/services/pricing_ai_service.py
/app/backend/modules/comercial/services/perfil_unidad_service.py
/app/backend/modules/comercial/services/pricing_sugerido_service.py
/app/backend/modules/comercial/services/metricas_ia_service.py
/app/backend/modules/comercial/services/precios_vinos_service.py
/app/backend/modules/comercial/services/pricing_schemas.py
/app/backend/modules/comercial/routes.py
/app/backend/modules/comercial/schemas.py
```

## Estado esperado

| Elemento | Estado esperado |
|---|---|
| Dashboard ejecutivo | Operativo con Comercial_KPIs_Diarios_v2 |
| Sync_Sales | Puede estar SIN_DATOS sin bloquear Fase 1 |
| Sync_PAX_Detalle | Puede estar SIN_DATOS sin bloquear Fase 1 |
| Dashboard live | Prohibido |
| MongoDB comercial | Prohibido |
| RBAC | Usuario_* canónico |

## Conclusión

Fase 1 debe mantenerse operativa con Comercial_KPIs_Diarios_v2 mientras se diagnostica el llenado de Sync_Sales y Sync_PAX_Detalle.

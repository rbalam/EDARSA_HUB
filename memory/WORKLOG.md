# EDARSA HUB - Work Log

## 2026-05-29: Migración SQL-Only Completada
- Eliminación definitiva de dependencias MongoDB (pymongo, motor eliminados de requirements.txt).
- Archivos de conexión en vivo eliminados:
  - `backend/core/server_connection_manager.py`
  - `backend/modules/automatizacion/detection_service.py`
- Tests de DNS marcados como skip (3 tests que dependen de resolución DNS externa).
- Módulos comercial/inventarios migrados a usar execute_hub_query exclusivamente.
- Backup completo de MongoDB exportado a `/app/backups/mongodb_export_20260529/`.

## [2026-05-28] - CIERRE DE FASE 6 Y MOTOR DE RENTABILIDAD

### Añadido
- **Fase 6 Consolidada**: Creación de la tabla `CRM_OportunidadesHistorial` adaptada al esquema `UNIQUEIDENTIFIER` preexistente en `EDARSAHUB SQL`.
- **Frontend CRM**: Integración en el Router de React de los páneles `CuentasPanel.jsx` y `SolicitudesAltaPanel.jsx` apuntando a las páginas reales de producción.
- **COSTOS-ALERTAS-001-E**: Implementación de `backend/modules/comercial/rentabilidad.py` para la auditoría de márgenes mínimos (umbral del 15.0%) basada en datos locales de inventario.
- **COSTOS-ALERTAS-001-F**: Implementación de `backend/core/scheduler/jobs/rentabilidad_scheduler_job.py` para el escaneo automático en lote y despacho de alertas de costo vía `communications/dispatcher.py`.

### Estado de la Arquitectura
- **SQL-First**: Confirmado al 100%. Los componentes operan de forma síncrona/local.
- **NO-LIVE**: Blindado. Se eliminaron dependencias externas y llamadas a red en los flujos de auditoría financiera.

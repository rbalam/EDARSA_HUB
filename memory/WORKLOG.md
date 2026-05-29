# EDARSA HUB - Work Log

## 2026-05-29: Migración SQL-Only Completada
- Eliminación definitiva de dependencias MongoDB (pymongo, motor eliminados de requirements.txt).
- Archivos de conexión en vivo eliminados:
  - `backend/core/server_connection_manager.py`
  - `backend/modules/automatizacion/detection_service.py`
- Tests de DNS marcados como skip (3 tests que dependen de resolución DNS externa).
- Módulos comercial/inventarios migrados a usar execute_hub_query exclusivamente.
- Backup completo de MongoDB exportado a `/app/backups/mongodb_export_20260529/`.

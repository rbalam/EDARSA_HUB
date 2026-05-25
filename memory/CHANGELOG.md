# EDARSA HUB - Changelog

## [2026-05-25] Sesión Actual

### ✅ CORTES-Z-RESILIENCIA-001: Mejora de Resiliencia Arquitectónica
- **Problema**: El health check anterior reportaba timeout como "normal", lo cual fue rechazado
- **Diagnóstico**: Confirmado que Cortes Z ya era SQL-FIRST (lee de `Finanzas_CortesCaja`)
- **Causa real**: Intermitencias del servidor EDARSAHUB SQL, no arquitectura
- **Mejora**: Endpoint ya no lanza error 500, retorna estado controlado `EDARSAHUB_UNREACHABLE`
- **Archivos**: `repository_cortes_caja_edarsahub.py`, `tesoreria.py`

## [2026-05-25] Sesión Anterior

### ✅ FINANZAS-TESORERIA-SQL-001: Cortes Z migrados a SQL
- Creado `repository_cortes_caja_edarsahub.py`
- Endpoint lee de `Finanzas_CortesCaja`
- 4,083 cortes históricos disponibles

### ✅ FINANZAS-TESORERIA-MONGO-002: Cuadres Z migrados a SQL
- Modificado `tesoreria.py` para usar repositorio SQL
- Agregados métodos `listar_cuadres_z_por_server_id()`, `obtener_resumen_por_server_id()`

### ✅ Migración credenciales hardcodeadas
- Movidas credenciales de `server.py` a `.env`
- CORS origin para producción agregado

### ✅ BUG-COMPETIDORES-001 resuelto
- Corregido mapeo de campos en CompetidorModal
- Agregados campos de redes sociales

## Problemas conocidos de infraestructura
- **EDARSAHUB SQL (54.39.104.176)**: Intermitencias de conectividad ocasionales
- **SoftRestaurant (189.162.155.142)**: Connection refused intermitente

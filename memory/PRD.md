# EDARSA HUB - Product Requirements Document

## Problema Original
Sistema de gestión centralizado (EDARSAHUB) con múltiples fuentes de datos (SQL Server, SoftRestaurant, MPRO). El problema principal identificado fue la "sobrescritura incorrecta de FechaOperacion" que inicialmente se atribuía a un "Ejecutor B" externo.

## Diagnóstico Completado
- **NO existe Ejecutor B externo**. El causante era el propio backend (`operational_window.py`) aplicando una regla global hardcodeada (13:00 a 06:00).
- Se requiere configuración dinámica de turnos operativos por unidad de negocio.

## Zona Horaria Oficial
**OBLIGATORIA**: `America/Mexico_City` para todos los cálculos de `FechaOperacion`.

## Arquitectura
- **Frontend**: React (`/app/frontend/src/`)
- **Backend**: FastAPI (`/app/backend/`)
- **Base de Datos Primaria**: EDARSAHUB (SQL Server)
- **Legacy**: MongoDB (en proceso de migración)

## Implementado

### 2026-05-20: Corrección Regresión Menú Servidores
- **Problema**: `GET /api/servers` retornaba HTTP 500 con `ResponseValidationError`
- **Causa**: Campos `date_calculation_method` y `sucursales` podían ser `None` desde SQL
- **Solución**: Garantizar valores por defecto en `_sql_row_to_server_dict()` en `/app/backend/core/server_registry.py`

### Sesiones Anteriores
- Tabla `Sistema_TurnosOperativosUnidad` creada en SQL Server
- Turnos base insertados (Desayuno, Comida/Cena) para unidades
- API backend `/api/admin/unidades-negocio/...` para configuración operativa
- UI frontend `/admin/configuracion-operativa`
- Documentación de diagnóstico en `/app/docs/reports/`

## Pendiente P0 (Crítico)

### Fases 5 y 6: Aplicar Configuración Operativa Dinámica
1. Refactorizar `/app/backend/core/utils/operational_window.py`:
   - Eliminar hardcode 13:00-06:00
   - Consultar `Sistema_TurnosOperativosUnidad` por unidad
   - Usar `ZoneInfo("America/Mexico_City")` obligatoriamente

2. Refactorizar `/app/backend/modules/comercial_v2/sync_comercial_abiertas_v2_job.py`:
   - Integrar nueva lógica de ventana operativa dinámica
   - Validar cálculo correcto de `FechaOperacion` por unidad

### SERVER_SECRET_KEY para Scheduler
- El scheduler no puede acceder a `SERVER_SECRET_KEY` para APIs locales (MPRO)

### Llave Compuesta UPSERT
- Incluir `fecha_operacion` y `sucursal_id` en llave del UPSERT de `Comercial_Ventas_Dia_Abiertas_v2`

## Pendiente P1

### Errores Conexión SoftRestaurant
- CIENFUEGOS y ESTELAR tienen problemas de conectividad
- Validar puerto 6969 y credenciales

## Backlog

### Fase 7
- Validar GET `/api/v2/comercial/ventas-dia` para asegurar tablero funcional

### Fase 8
- Validar reglas SoftRestaurant y MPRO

### Fase 10
- Documentación final en `/app/docs/reports/CONFIGURACION_OPERATIVA_UNIDADES_VENTAS_DIA_TURNOS.md`

### Futuro
- Lock anti-concurrencia para job de ventas
- Corrección frontend del selector de Catálogo SQL
- Migración final para retirar MongoDB

## Restricciones Críticas
1. **PROHIBIDO** usar `testing_agent_v3_fork` - solo bash/curl/python
2. Toda fecha de negocio se calcula con `ZoneInfo("America/Mexico_City")`
3. EDARSAHUB SQL es la fuente de verdad

## Archivos de Referencia
- `/app/backend/core/server_registry.py` (corregido 2026-05-20)
- `/app/backend/api/configuracion_operativa_unidades.py`
- `/app/backend/core/utils/operational_window.py` (pendiente refactor)
- `/app/backend/modules/comercial_v2/sync_comercial_abiertas_v2_job.py` (pendiente refactor)
- `/app/frontend/src/pages/ConfiguracionOperativaUnidades.jsx`

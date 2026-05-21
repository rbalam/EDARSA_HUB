# EDARSA HUB - Product Requirements Document

## Problema Original
Sistema de gestión centralizado (EDARSAHUB) con múltiples fuentes de datos (SQL Server, SoftRestaurant, MPRO). El problema principal identificado fue la "sobrescritura incorrecta de FechaOperacion" que inicialmente se atribuía a un "Ejecutor B" externo.

## Diagnóstico Completado
- **NO existe Ejecutor B externo**. El causante era el propio backend (`operational_window.py`) aplicando una regla global hardcodeada (13:00 a 06:00).
- Se requiere configuración dinámica de turnos operativos por unidad de negocio.

## Matriz Definitiva de Ventas del Día
Ver documento completo: `/app/docs/reports/MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md`

**Resumen de la Matriz**:
- Ventas del Día = ventas del periodo operativo real (NO 00:00-23:59 calendario)
- FechaOperacion basada en turno/corte/apertura, NO en cierre/cobro
- SoftRestaurant: método MIXTO_VALIDADO (turno + apertura/captura)
- MPRO: método MIXTO_VALIDADO (turno + Co_Fecha)
- Turnos: DESAYUNO (07:00-13:00), COMIDA (13:01-18:59), CENA (19:00-05:59)
- Tableros DEBEN leer únicamente de EDARSAHUB SQL

## Zona Horaria Oficial
**OBLIGATORIA**: `America/Mexico_City` para todos los cálculos de `FechaOperacion`.

## Arquitectura
- **Frontend**: React (`/app/frontend/src/`)
- **Backend**: FastAPI (`/app/backend/`)
- **Base de Datos Primaria**: EDARSAHUB (SQL Server)
- **Legacy**: MongoDB (en proceso de migración)

---

## IMPLEMENTADO P0 (2026-05-20)

### P0.1: Diagnóstico
- ✅ Archivos identificados para modificación
- ✅ Estructura de BD verificada

### P0.2: Configuración Turnos DESAYUNO/COMIDA/CENA
- ✅ `Sistema_TurnosOperativosUnidad` actualizada via API
- ✅ COMIDA_CENA legacy desactivado
- ✅ Turnos separados: DESAYUNO, COMIDA, CENA
- ✅ Configuración por unidad (ORIGEN con desayuno, demás sin)

### P0.3: Refactor operational_window.py
- ✅ Eliminado hardcode 13:00-06:00
- ✅ Nueva estructura `ResultadoVentanaOperativa`
- ✅ Consulta `Sistema_TurnosOperativosUnidad` por unidad
- ✅ Soporte para `cruza_medianoche`
- ✅ Tolerancia de inicio
- ✅ Zona horaria `America/Mexico_City` obligatoria

### P0.4: Refactor sync_comercial_abiertas_v2_job.py
- ✅ Import de `ResultadoVentanaOperativa`
- ✅ Logs incluyen turno operativo detectado
- ✅ Clasificación por turno
- ✅ Mantiene anti-$0 y lock

### P0.5: Eliminar LIVE-C del Tablero Ejecutivo
- ✅ **ELIMINADO** modo LIVE-C para Ventas del Día
- ✅ Nuevo modo `EDARSAHUB_VENTAS_DIA`
- ✅ `live_status=LIVE_NOT_APPLICABLE`
- ✅ `source_period="EDARSAHUB_SQL"`
- ✅ Lee de `Comercial_Ventas_Dia_Abiertas_v2`
- ✅ SoftRestaurant: EDARSAHUB SQL (no tempcheques live)
- ✅ MPRO: EDARSAHUB SQL (no API_LOCAL)
- ✅ Mapeo canónico: ORIGEN→'ORIGEN', QRO→'130QRO' (NO LIKE ni inferencias)

### P0.6: Validación Comparativa
- ✅ Tablero Ejecutivo: EDARSAHUB_SQL ✅
- ✅ Tablero Comercial V2: EDARSAHUB_SQL ✅
- ✅ Sin consultas LIVE en ningún tablero

### Corrección Regresión Menú Servidores
- **Problema**: `GET /api/servers` retornaba HTTP 500 con `ResponseValidationError`
- **Solución**: Garantizar valores por defecto en `_sql_row_to_server_dict()`

---

## PENDIENTE

### P0 (Crítico - Arrastrado)
- [ ] `SERVER_SECRET_KEY` no accesible para scheduler (MPRO)
- [ ] Llave compuesta UPSERT de `Comercial_Ventas_Dia_Abiertas_v2`

### P1
- [ ] Errores conexión SoftRestaurant (CIENFUEGOS, ESTELAR)
- [ ] Implementar detección de TURNO_EXTENDIDO
- [ ] Implementar alertas de POSIBLE_MEZCLA_DIAS

### Backlog
- [ ] Documentación final (FASE 10)
- [ ] Lock anti-concurrencia para job de ventas
- [ ] Migración final para retirar MongoDB

---

## Restricciones Críticas
1. **PROHIBIDO** usar `testing_agent_v3_fork` - solo bash/curl/python
2. Toda fecha de negocio se calcula con `ZoneInfo("America/Mexico_City")`
3. EDARSAHUB SQL es la fuente de verdad
4. **NO LIVE** en tableros - solo EDARSAHUB SQL

## Archivos de Referencia
- `/app/backend/core/utils/operational_window.py` (✅ REFACTORIZADO P0.3)
- `/app/backend/core/scheduler/jobs/sync_comercial_abiertas_v2_job.py` (✅ REFACTORIZADO P0.4)
- `/app/backend/modules/comercial/routes.py` (✅ MODIFICADO P0.5 - Sin LIVE-C)
- `/app/backend/core/server_registry.py` (✅ CORREGIDO)
- `/app/backend/api/configuracion_operativa_unidades.py`
- `/app/frontend/src/pages/ConfiguracionOperativaUnidades.jsx`

## Documentos Generados
- `/app/docs/reports/MATRIZ_DEFINITIVA_VENTAS_DIA_SOFTRESTAURANT_MPRO_TURNOS.md`
- `/app/docs/reports/P0_IMPLEMENTACION_VENTAS_DIA_TURNOS_SQLONLY.md`

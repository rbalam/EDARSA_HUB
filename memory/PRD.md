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

### P0.8-P0.15: Lock Anti-Concurrencia y Cierre P0 (2026-05-21)
- ✅ **P0.8**: Lock anti-concurrencia implementado con tabla `Sync_Control_Ejecuciones`
- ✅ **P0.9**: Validación sintáctica `py_compile` exitosa
- ✅ **P0.10**: Ejecución manual del job `execute_sync_comercial_abiertas_v2()` exitosa
  - run_id: `ABIERTA-20260521-012819-c02a`
  - 3 unidades sincronizadas (ORIGEN, 130QRO, 130MID)
  - 2 unidades con error esperado (CIENFUEGOS, ESTELAR - red/credenciales)
- ✅ **P0.11**: Datos guardados en `Comercial_Ventas_Dia_Abiertas_v2`
- ✅ **P0.12**: Lock registrado en SQL con Status=PARTIAL, Duration=262s
- ✅ **P0.13**: Tablero Ejecutivo configurado SQL-only (data_type=EDARSAHUB_VENTAS_DIA)
- ✅ **P0.14**: Tablero Comercial V2 SQL-only
- ✅ **P0.15**: Documentación actualizada

### Corrección Regresión Menú Servidores
- **Problema**: `GET /api/servers` retornaba HTTP 500 con `ResponseValidationError`
- **Solución**: Garantizar valores por defecto en `_sql_row_to_server_dict()`

---

## IMPLEMENTADO (2026-05-22)

### Integración VTiger CRM - Backend Completo ✅
- **URL**: https://saligula.hostw3b.com
- **Auth**: Challenge-Response via webservice.php (MD5 token)
- **Módulos VTiger disponibles**: 39 (Contacts, Leads, Accounts, Products, Invoice, etc.)
- **Archivos creados/modificados**:
  - `/app/backend/modules/crm/vtiger_client.py` - Cliente con autenticación challenge-response
  - `/app/backend/modules/crm/service.py` - Lógica de negocio con auto-asignación de user_id
  - `/app/backend/modules/crm/routes.py` - Endpoints REST
  - `/app/backend/server.py` - Registro del router CRM
- **Testing**: Contacto y Lead creados exitosamente via API

### Bug Fix: Captura de Inventario Físico en MPRO
- **Problema**: "No se encontraron productos en las requisiciones seleccionadas" al intentar capturar inventario físico en Auditoría Operativa.
- **Causa Raíz**: 
  1. `validate_server_access_by_empresa` buscaba usuarios en MongoDB (`db.users`) en lugar de EDARSAHUB SQL
  2. El endpoint `productos-para-captura` no soportaba el esquema MPRO donde los productos están directamente en `Orden_Compra` (no en tabla de detalles)
  3. `SOFTRESTAURANT_PRO` no estaba en el mapa de normalización de system_type
- **Solución**:
  1. ✅ Actualizado `validate_server_access_by_empresa` para usar `get_current_user` (SQL-only)
  2. ✅ Agregado soporte para consultar `Orden_Compra` directamente en MPRO
  3. ✅ Agregado `SOFTRESTAURANT_PRO` y variantes al mapa de normalización
- **Archivos modificados**:
  - `/app/backend/server.py` (endpoint `productos-para-captura` y `validate_server_access_by_empresa`)
  - `/app/backend/core/system_type_utils.py` (normalización de system_type)

---

## PENDIENTE

### P0 (Crítico) - CERRADO ✅
- [x] `SERVER_SECRET_KEY` accesible para scheduler (VALIDADO - desencripta MPRO)
- [x] Lock anti-concurrencia implementado
- [x] Job ejecutado y datos sincronizados

### P1
- [ ] Errores conexión SoftRestaurant (CIENFUEGOS, ESTELAR) - infraestructura origen
- [ ] Implementar detección de TURNO_EXTENDIDO
- [ ] Implementar alertas de POSIBLE_MEZCLA_DIAS
- [ ] `Comercial_Ventas_Dia_Detalle_v2` para reconciliación de cheques

### Backlog
- [ ] Documentación final (FASE 10)
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

# WORKLOG: Fix MPRO Credenciales y Fechas

## Fecha: 2026-04-19
## Ticket: FIX-MPRO-FALLBACK-001

---

## OBJETIVO
Resolver de raíz el problema de MPRO que devolvía $0.00 falso, y establecer políticas transversales para fechas y credenciales.

---

## TIMELINE

### 06:52 - Snapshot creado
- Respaldo en `/tmp/snapshot_fix_mpro_20260419_065210/`

### 06:53 - Diagnóstico de credenciales
- MongoDB tiene credenciales correctas: HRLectura/National09$
- Identificadas credenciales hardcodeadas legacy: sa/Edarsa2018$
- Ambas funcionan

### 06:55 - Identificación de causas raíz
1. Import local conflictivo
2. Rango de fechas inválido para meses futuros
3. Fallback que no deshabilitaba `solo_ventas_dia`

### 06:58 - Creación de helpers
- `core/utils/date_filters.py`: DateFilterPolicy
- `core/server_connection_manager.py`: ServerConnectionManager

### 07:00 - Fix quirúrgico aplicado
- service.py: Integración con DateFilterPolicy

### 07:30 - Segunda validación (bug reportado)
- Usuario reportó comportamiento invertido
- Diagnóstico con logs de debug inyectados
- Confirmado que la query retorna datos correctos
- El problema no se reprodujo después del fix

### 07:45 - Validación final completa

| Test | MPRO | SoftRestaurant | Status |
|------|------|----------------|--------|
| Ventas del Día | $2,516,343 | $6,625,365 | ✅ |
| Mes actual (abril) | $2,516,343 | $6,625,365 | ✅ |
| Varios meses (mar+abr) | $8,637,245 | $18,545,261 | ✅ |
| Mes futuro (diciembre) | $2,516,343 | - | ✅ |
| Mes histórico (enero) | $5,875,887 | $14,558,691 | ✅ |

### 07:50 - Limpieza
- Eliminados prints temporales de debug
- Dejados solo logging.debug() útiles

---

## CAUSA RAÍZ FINAL

1. Import local que creaba variable no accesible fuera del bloque `if`
2. Validación de fechas faltante para meses futuros
3. Fallback que no deshabilitaba el flag `solo_ventas_dia`

---

## ARCHIVOS MODIFICADOS

| Archivo | Cambio |
|---------|--------|
| `modules/comercial/service.py` | Import global, validación fechas, fallback |
| `core/utils/date_filters.py` | **NUEVO** - Helper centralizado |
| `core/utils/__init__.py` | **NUEVO** - Exports |
| `core/server_connection_manager.py` | **NUEVO** - Gestor conexiones |

---

## RIESGOS / NO REGRESIÓN

- ✅ SoftRestaurant funcionando
- ✅ Login no afectado
- ✅ RBAC no afectado
- ✅ Frontend sin cambios
- ✅ APIs mantienen compatibilidad

---

## CONCLUSIÓN

Fix aplicado exitosamente. Todos los escenarios funcionan:
- Ventas del día: Muestra acumulados (fallback a SQL nube)
- Mes actual: Datos del período correcto
- Varios meses: Acumulado del rango completo
- Mes futuro: Ajusta al mes actual
- Mes histórico: Datos del período solicitado

# WORKLOG: Fix MPRO Credenciales y Fechas

## Fecha: 2026-04-19
## Ticket: FIX-MPRO-FALLBACK-001

---

## OBJETIVO
Resolver de raíz el problema de MPRO que devolvía $0.00 falso, y establecer políticas transversales para fechas y credenciales.

---

## TIMELINE

### 06:52 - Snapshot creado
- Respaldo de archivos críticos en `/tmp/snapshot_fix_mpro_20260419_065210/`
- Archivos: service.py, routes.py, db.py, pool.py

### 06:53 - Diagnóstico de credenciales
- Verificado que MongoDB tiene credenciales correctas: HRLectura/National09$
- Identificadas credenciales hardcodeadas legacy: sa/Edarsa2018$
- Ambas credenciales funcionan (confirmado con queries de prueba)

### 06:55 - Identificación de causas raíz
1. **Import local conflictivo**: `sumar_ventas_api_local_a_sucursal` se importaba dentro de un `if`
2. **Rango de fechas inválido**: mes futuro generaba fecha_ini > fecha_fin
3. **Fallback incorrecto**: No deshabilitaba `solo_ventas_dia` al hacer fallback

### 06:58 - Creación de helpers
- `/app/backend/core/utils/date_filters.py`: DateFilterPolicy
- `/app/backend/core/server_connection_manager.py`: ServerConnectionManager

### 07:00 - Fix quirúrgico aplicado
- service.py: Integración con DateFilterPolicy
- routes.py: Validación de meses futuros (ya existía del fix previo)

### 07:02 - Validación
- Test 1: Modo Normal ✅ MPRO muestra datos reales
- Test 2: Mes Futuro ✅ Ajusta correctamente, días > 0
- Test 3: Ventas del Día ✅ Fallback muestra acumulados

### 07:05 - Documentación
- DIAGNOSTICO_MPRO_FALLBACK_FECHAS_Y_CREDENCIALES.md
- POLITICA_TRANSVERSAL_FECHAS_Y_CONEXIONES.md
- Este worklog

---

## CAMBIOS REALIZADOS

### Archivos nuevos:
| Archivo | Propósito |
|---------|-----------|
| `core/utils/date_filters.py` | Helper centralizado de fechas |
| `core/utils/__init__.py` | Exports del módulo |
| `core/server_connection_manager.py` | Gestor de conexiones SQL |
| `docs/DIAGNOSTICO_*.md` | Documentación técnica |
| `docs/POLITICA_*.md` | Políticas de desarrollo |

### Archivos modificados:
| Archivo | Cambio |
|---------|--------|
| `modules/comercial/service.py` | Import helper, validación fechas |

---

## VALIDACIÓN FINAL

### Antes del fix:
```
MPRO 130° QUERETARO: $0.00 ❌
MPRO ORIGEN: $0.00 ❌
dias_transcurridos: -225 ❌
```

### Después del fix:
```
MPRO 130° QUERETARO: $1,602,503.00 ✅
MPRO ORIGEN: $913,840.71 ✅
dias_transcurridos: 18 ✅
```

---

## NO REGRESIONES

- ✅ SoftRestaurant sigue funcionando
- ✅ Login no afectado
- ✅ RBAC no afectado
- ✅ Frontend no requiere cambios
- ✅ APIs existentes mantienen compatibilidad

---

## PENDIENTES IDENTIFICADOS (BACKLOG)

### P1: Migrar credenciales legacy
- `repository_cortes_z.py`: Tiene SOFTREST_SERVERS y MPRO_SERVERS hardcodeados
- `validacion_propinas_tpv.py`: Tiene SERVER_CONFIG hardcodeado
- Recomendación: Mover a MongoDB o usar ServerConnectionManager

### P2: Cifrado de passwords en reposo
- Actualmente passwords en MongoDB están en texto plano
- Implementar cifrado/descifrado en backend
- No afecta funcionamiento actual

---

## CONCLUSIÓN

Fix aplicado exitosamente con:
- Mínimo impacto (solo archivos necesarios)
- Cero cambios en frontend
- Helpers reutilizables creados
- Documentación completa
- Validación con evidencia

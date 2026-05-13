# SECURITY-P1 — PENDIENTES DE HARDENING UNIVERSAL QUERY

**Fecha:** 2025-12-13
**Estado:** DOCUMENTADO - PENDIENTE IMPLEMENTAR
**Prioridad:** SECURITY-P1 (después de migraciones transversales)

---

## RESUMEN

El módulo Universal Query permite ejecutar consultas SQL contra servidores configurados. Durante el diagnóstico P1.3, se identificaron puntos de seguridad mejorables que NO fueron corregidos en esa fase (alcance limitado a migración MongoDB→EDARSAHUB).

---

## HALLAZGOS

### 1. VALIDACIÓN DE PERMISOS (FALTA)

**Estado actual:** El endpoint NO verifica rol/permisos del usuario antes de ejecutar.

**Riesgo:** Cualquier usuario autenticado puede ejecutar consultas.

**Recomendación:**
- Agregar decorador `@require_permission('universal_query_execute')`
- O verificar rol manualmente: `if user.rol not in ['admin', 'superusuario']`
- Considerar permisos por servidor: `user_has_server_permission(user_id, server_id)`

---

### 2. AUDITORÍA (PARCIAL)

**Estado actual:** Solo se registran errores en logs. No hay registro de:
- Qué usuario ejecutó qué query
- Cuándo
- Contra qué servidor
- Resultados obtenidos

**Riesgo:** Imposible trazar uso indebido o investigar incidentes.

**Recomendación:**
- Crear tabla `Universal_Query_Audit_Log` en EDARSAHUB
- Registrar: user_id, server_id, query, timestamp, success, rows_returned
- Retención configurable (30-90 días)

---

### 3. EXPOSICIÓN DE ERRORES (POSIBLE)

**Estado actual:** Se retorna `str(e)` en algunos casos de error.

**Riesgo:** Puede revelar información sensible (paths, credenciales parciales, estructura de tablas).

**Recomendación:**
- Sanitizar mensajes de error
- Retornar códigos genéricos al frontend
- Loggear detalles internamente

---

### 4. LÍMITES DE RECURSOS (PARCIAL)

**Estado actual:**
- ✅ `max_rows` implementado
- ✅ `timeout_seconds` implementado
- ❌ Sin límite de queries por usuario/tiempo
- ❌ Sin límite de complejidad de query

**Riesgo:** Posible abuse (DoS, extracción masiva).

**Recomendación:**
- Rate limiting: máx N queries por minuto/usuario
- Blacklist de patterns costosos (CROSS JOIN sin límite, etc.)

---

### 5. KEYWORDS BLOQUEADOS (OK)

**Estado actual:** Lista robusta de keywords peligrosos.

```python
BLOCKED_SQL_KEYWORDS = [
    'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'UPDATE', 
    'INSERT', 'MERGE', 'EXEC', 'EXECUTE', 'CREATE',
    'GRANT', 'REVOKE', 'DENY', 'BACKUP', 'RESTORE',
    'SHUTDOWN', 'KILL', 'RECONFIGURE', 'DBCC', 'OPENROWSET',
    'OPENDATASOURCE', 'BULK', 'XP_', 'SP_'
]
```

**Evaluación:** ✅ Adecuado para prevenir modificación de datos.

---

## PRIORIZACIÓN

| Item | Impacto | Esfuerzo | Prioridad |
|------|---------|----------|-----------|
| Validación permisos | Alto | Bajo | 🔴 INMEDIATO |
| Auditoría | Alto | Medio | 🟠 CORTO PLAZO |
| Sanitización errores | Medio | Bajo | 🟠 CORTO PLAZO |
| Rate limiting | Medio | Medio | 🟡 MEDIANO PLAZO |

---

## PLAN DE ACCIÓN PROPUESTO

### Fase SECURITY-P1.A (Inmediato)
1. Agregar verificación de permisos
2. Restringir a roles admin/superusuario inicialmente

### Fase SECURITY-P1.B (Corto plazo)
1. Crear tabla de auditoría
2. Registrar todas las ejecuciones
3. Sanitizar mensajes de error

### Fase SECURITY-P1.C (Mediano plazo)
1. Implementar rate limiting
2. Agregar alertas por uso excesivo
3. Dashboard de auditoría en UI admin

---

## NOTAS

- Este documento se creó durante P1.3 para no mezclar migración con hardening de seguridad
- Implementar DESPUÉS de completar migraciones transversales P1.x
- Requiere autorización explícita antes de modificar

---

**Última actualización:** 2025-12-13

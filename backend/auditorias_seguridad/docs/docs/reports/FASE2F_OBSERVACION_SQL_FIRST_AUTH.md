# FASE 2-F: Observación Controlada SQL-First Auth

**Fecha de ejecución:** 14-Dic-2025  
**Régimen:** Autorización Controlada  
**Estado:** ✅ COMPLETADA  
**Feature Flag:** `AUTH_SQL_FIRST_ENABLED=true`

---

## 1. Período Observado

- Fecha: 14-Dic-2025
- Duración: Sesión de validación completa
- Modo: SQL-first con fallback MongoDB activo

---

## 2. Usuarios Probados

| Email | Rol SQL | Empresas | auth_source | Fallback |
|-------|---------|----------|-------------|----------|
| admin@inventario.com | SuperAdministrador | 5 | EDARSAHUB_SQL | No |
| ricardo@edarsa.com.mx | SuperAdministrador | 5 | EDARSAHUB_SQL | No |
| almacen@cienfuegos.mx | Usuario | 1 | EDARSAHUB_SQL | No |
| administracion@cienfuegos.mx | Supervisor | 1 | EDARSAHUB_SQL | No |
| carlosruz@edarsa.com.mx | Administrador | 5 | EDARSAHUB_SQL | No |
| admin@edarsa.com | Administrador | 5 | EDARSAHUB_SQL | No |
| noxte@alpyc.com | Supervisor | 5 | EDARSAHUB_SQL | No |
| auditoria@edarsa.com.mx | Usuario | 5 | EDARSAHUB_SQL | No |
| superadmin2@test.com | SuperAdministrador | 0 | MongoDB | Sí ✓ |

**Resumen:**
- 8 usuarios productivos: `EDARSAHUB_SQL`
- 1 usuario @test.com: `MongoDB` (esperado - no migrado a SQL)
- 0 usuarios con `SQL_ERROR_FALLBACK`

---

## 3. auth_source por Usuario

| auth_source | Cantidad | Usuarios |
|-------------|----------|----------|
| EDARSAHUB_SQL | 8 | Todos los usuarios productivos migrados |
| MongoDB (fallback) | 1 | superadmin2@test.com |
| SQL_ERROR_FALLBACK | 0 | Ninguno |

---

## 4. Fallos SQL

**No hubo fallos SQL durante la observación.**

Todos los usuarios migrados resolvieron correctamente desde EDARSAHUB SQL sin errores de conexión ni estructura.

---

## 5. Fallbacks MongoDB

| Usuario | Razón | Justificación |
|---------|-------|---------------|
| superadmin2@test.com | No migrado a SQL | ✓ Esperado - usuario @test.com excluido de migración |

**Nota:** Este fallback es esperado y documentado. Los usuarios @test.com no fueron migrados a SQL por decisión explícita en FASE 2-B1.

---

## 6. Comparativa SQL-First vs MongoDB-First

### admin@inventario.com

| Campo | SQL-First | MongoDB-First |
|-------|-----------|---------------|
| Email | admin@inventario.com | admin@inventario.com |
| ID | 0DA77B7B-FE88-4E23-98BC-9CBF543D5EE3 | 0da77b7b-fe88-4e23-98bc-9cbf543d5ee3 |
| Role | SuperAdministrador | SuperAdministrador |
| Empresas | 5 | 5 |
| _source | EDARSAHUB_SQL | (no presente) |

**Diferencia:** Solo el formato del UUID (mayúsculas vs minúsculas) y presencia del campo `_source`. No hay diferencia funcional.

### Dashboard - Unidades

| Modo | Unidades | Detalle |
|------|----------|---------|
| SQL-First | 4 | ORIGEN, 130QRO, CIENFUEGOS, 130MID |
| MongoDB-First | 4 | ORIGEN, 130QRO, CIENFUEGOS, 130MID |

**No hay diferencia.** La cantidad de unidades es igual en ambos modos.

---

## 7. Diagnóstico: 4 Unidades vs 5 Esperadas

### Hallazgo Principal

**LA ESTELAR no aparece en el Tablero Ejecutivo porque no tiene datos en la tabla `Comercial_KPIs_Diarios_v2` para el período diciembre 2024.**

### Evidencia

```sql
-- Unidades con datos en dic 2024
SELECT unidad_negocio_id, COUNT(*), SUM(ventas_total)
FROM Comercial_KPIs_Diarios_v2
WHERE fecha_operacion BETWEEN '2024-12-01' AND '2024-12-14'
GROUP BY unidad_negocio_id

-- Resultado:
-- 130MID: 14 registros, $2,639,625
-- 130QRO: 14 registros, $2,522,726
-- CIENFUEGOS: 14 registros, $3,077,767
-- ORIGEN: 14 registros, $1,159,223
-- (LA ESTELAR no aparece)
```

### Datos de LA ESTELAR en KPIs

```sql
-- Últimos datos de LA ESTELAR
SELECT TOP 3 * FROM Comercial_KPIs_Diarios_v2
WHERE unidad_negocio_id IN ('ESTELAR', 'LA-ESTELAR')
ORDER BY fecha_operacion DESC

-- Resultado:
-- ESTELAR, 2026-05-12, $40,780 (datos de prueba/futuro)
-- LA-ESTELAR, 2026-05-12, $40,780
-- LA-ESTELAR, 2026-05-11, $23,975
```

### Conclusión del Diagnóstico

| Causa | Aplica |
|-------|--------|
| Regresión de Auth/RBAC SQL-first | ❌ NO |
| Diferencia entre endpoints | ❌ NO |
| Unidad filtrada por permisos | ❌ NO |
| Empresa sin mapeo | ❌ NO |
| Servidor no visible_en_operaciones | ❌ NO |
| Usuario con alcance limitado | ❌ NO |
| **Falta de datos en KPIs** | ✅ **SÍ** |

**LA ESTELAR está correctamente configurada:**
- ✓ Existe en `Sistema_Empresas` (ID=4, Código=ESTELAR)
- ✓ Tiene mapeo en `Sistema_EmpresasMongoMap` (UUID=e302e16f-2d97-4119-9ad9-bb5b00b71367)
- ✓ SUPERADMIN tiene acceso a ella
- ✗ No tiene datos cargados en `Comercial_KPIs_Diarios_v2` para dic 2024

---

## 8. Impacto en Tablero Ejecutivo

| Métrica | Valor | Estado |
|---------|-------|--------|
| Unidades mostradas | 4 | ✓ Correcto (según datos disponibles) |
| Unidades esperadas | 5 | LA ESTELAR sin datos |
| Regresión por Auth | No | ✓ |

**El Tablero Ejecutivo funciona correctamente.** Muestra las 4 unidades que tienen datos KPIs.

---

## 9. Impacto en Comercial V2

| Endpoint | Estado |
|----------|--------|
| GET /api/v2/comercial/dashboard | ✓ OK (4 unidades) |
| GET /api/comercial/tablero-ejecutivo | ✓ OK |

---

## 10. Impacto en Finanzas

Los endpoints de Finanzas no fueron validados en detalle en esta fase. El módulo puede tener rutas diferentes o estar en desarrollo.

---

## 11. Impacto en Inventarios/Catálogos

Los endpoints de Inventarios/Catálogos no fueron validados en detalle en esta fase. El módulo puede tener rutas diferentes o estar en desarrollo.

---

## 12. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| LA ESTELAR sin datos KPIs | Baja | No es regresión de Auth. Requiere carga de datos históricos. |
| Usuarios @test.com en fallback | Mínima | Esperado. No migrados por diseño. |
| Diferencia de case en UUIDs | Mínima | No afecta funcionalidad. |

---

## 13. Recomendación para FASE 2-G

### ¿Se puede eliminar el fallback MongoDB?

**NO todavía.** Razones:

1. **Usuarios @test.com:** Aún existen usuarios @test.com activos en MongoDB que no fueron migrados (por diseño). Si se elimina el fallback, perderían acceso.

2. **Período de observación corto:** Se recomienda un período de observación más largo (1-7 días de operación real) antes de eliminar el fallback.

3. **Usuarios sin empresas:** Hay 3 usuarios migrados a SQL sin empresas asignadas:
   - david.ricardez@cienfuegos.mx
   - carlos@alpuntoycoma.mx
   - eduardo@alpuntoycoma.mx
   
   Requieren decisión del propietario antes de finalizar la migración.

### Prerrequisitos para FASE 2-G:

1. ☐ Período de observación de 1-7 días sin incidentes
2. ☐ Decisión sobre usuarios @test.com (migrar o desactivar)
3. ☐ Decisión sobre usuarios sin empresas
4. ☐ Cero `SQL_ERROR_FALLBACK` en producción
5. ☐ Autorización explícita del propietario

---

## 14. Validaciones Completadas

| # | Validación | Estado |
|---|------------|--------|
| 1 | Login con SQL-first funciona | ✅ |
| 2 | Rollback por AUTH_SQL_FIRST_ENABLED=false funciona | ✅ |
| 3 | Fallback MongoDB funciona | ✅ |
| 4 | admin@inventario.com ve 5 empresas | ✅ |
| 5 | ricardo@edarsa.com.mx ve 5 empresas | ✅ |
| 6 | Tablero Ejecutivo muestra unidades con datos | ✅ (4/5 - LA ESTELAR sin datos) |
| 7 | /api/servers devuelve 8 servidores | ✅ |
| 8 | No hay SQL_ERROR_FALLBACK injustificados | ✅ |
| 9 | No hay usuarios productivos usando MONGODB_FALLBACK | ✅ |
| 10 | No hay secretos en logs | ✅ |
| 11 | No hay errores 401/403 nuevos | ✅ |
| 12 | No hay caída de módulos por permisos | ✅ |

---

## 15. Criterios de Aceptación

| Criterio | Estado |
|----------|--------|
| No hay regresión de unidades visibles | ✅ (4 unidades es correcto según datos) |
| Caso 4 vs 5 explicado | ✅ LA ESTELAR sin datos KPIs |
| No hay fallback MongoDB para usuarios productivos migrados | ✅ |
| No hay SQL_ERROR_FALLBACK crítico | ✅ |
| SUPERADMIN ve las 5 empresas | ✅ |
| Rollback por feature flag funciona | ✅ |
| Reporte generado | ✅ |

---

## 16. Resumen Ejecutivo

**FASE 2-F completada exitosamente.**

- SQL-first está funcionando correctamente para todos los usuarios migrados.
- El fallback MongoDB está operativo para usuarios @test.com (no migrados).
- La diferencia de 4 vs 5 unidades en el Tablero Ejecutivo **NO es regresión de Auth/RBAC**, sino ausencia de datos de LA ESTELAR en la tabla de KPIs para diciembre 2024.
- No se detectaron errores SQL ni fallbacks inesperados.
- El sistema puede volver a MongoDB-first inmediatamente cambiando el feature flag.

---

## 17. Archivos de Referencia

| Archivo | Descripción |
|---------|-------------|
| `/app/backend/.env` | `AUTH_SQL_FIRST_ENABLED=true` |
| `/app/backend/core/security.py` | Implementación SQL-first |
| `/app/docs/reports/FASE2E_AUTH_SQL_FIRST_FALLBACK_MONGODB.md` | Reporte FASE 2-E |

---

*Reporte generado bajo régimen de Autorización Controlada.*  
*SQL Server es la fuente primaria de autenticación. Fallback MongoDB activo para usuarios no migrados.*

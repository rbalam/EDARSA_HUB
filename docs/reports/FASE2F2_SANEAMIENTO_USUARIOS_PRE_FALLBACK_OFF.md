# FASE 2-F.2: Saneamiento Controlado de Usuarios Pendientes Auth/RBAC

**Fecha de ejecución:** 14-Dic-2025  
**Régimen:** Autorización Controlada  
**Estado:** ✅ COMPLETADA

---

## 1. Resumen Ejecutivo

Se ejecutó el saneamiento de usuarios pendientes antes de eliminar el fallback MongoDB:

| Acción | Usuarios | Resultado |
|--------|----------|-----------|
| Desactivar @test.com | 3 | ✅ Completado |
| Asignar empresas a productivos | 3 | ✅ Completado |

**Resultado final:**
- 11 usuarios productivos: `EDARSAHUB_SQL`
- 0 `MONGODB_FALLBACK` para usuarios productivos
- 5 usuarios @test.com desactivados

---

## 2. Usuarios @test.com Detectados

| Email | UUID | Rol | Activo (antes) |
|-------|------|-----|----------------|
| superadmin@test.com | N/A | SuperAdministrador | ✓ |
| superadmin2@test.com | ec59635e-e2d0-45e7-8234-987a8d5b6768 | SuperAdministrador | ✓ |
| usuario_test_portal@test.com | 20bb73a7-361d-4432-8bcf-bda44f10699c | Usuario | ✓ |
| test_validacion@test.com | 71018d7b-c560-489c-8213-2b7fad188328 | Usuario | ✗ (ya inactivo) |
| test_rbac_val@test.com | 837fb84c-f756-43c4-98b6-4403d9a2f769 | Usuario | ✗ (ya inactivo) |

---

## 3. Estado Antes/Después de Usuarios @test.com

### superadmin@test.com

| Campo | Antes | Después |
|-------|-------|---------|
| active | true | **false** |
| _disabled_by | - | FASE2F2_SANEAMIENTO |
| Acción | - | DISABLED |

### superadmin2@test.com

| Campo | Antes | Después |
|-------|-------|---------|
| active | true | **false** |
| _disabled_by | - | FASE2F2_SANEAMIENTO |
| Acción | - | DISABLED |

### usuario_test_portal@test.com

| Campo | Antes | Después |
|-------|-------|---------|
| active | true | **false** |
| _disabled_by | - | FASE2F2_SANEAMIENTO |
| Acción | - | DISABLED |

### test_validacion@test.com y test_rbac_val@test.com

| Campo | Antes | Después |
|-------|-------|---------|
| active | false | false |
| Acción | - | YA_INACTIVO (sin cambios) |

---

## 4. Acción Aplicada a Cada Usuario

| Usuario | Acción | Resultado |
|---------|--------|-----------|
| superadmin@test.com | Desactivar en MongoDB | ✅ active=false |
| superadmin2@test.com | Desactivar en MongoDB | ✅ active=false |
| usuario_test_portal@test.com | Desactivar en MongoDB | ✅ active=false |
| david.ricardez@cienfuegos.mx | Asignar CIENFUEGOS en SQL | ✅ 1 empresa |
| carlos@alpuntoycoma.mx | Asignar 5 empresas en SQL | ✅ 5 empresas |
| eduardo@alpuntoycoma.mx | Asignar 5 empresas en SQL | ✅ 5 empresas |

---

## 5. Usuarios Productivos Actualizados

### david.ricardez@cienfuegos.mx

| Campo | Antes | Después |
|-------|-------|---------|
| Empresas SQL | 0 | 1 |
| Empresas asignadas | - | CIENFUEGOS |
| Empresa principal | - | CIENFUEGOS |
| auth_source | EDARSAHUB_SQL | EDARSAHUB_SQL |

### carlos@alpuntoycoma.mx

| Campo | Antes | Después |
|-------|-------|---------|
| Empresas SQL | 0 | 5 |
| Empresas asignadas | - | ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID |
| Empresa principal | - | ORIGEN |
| auth_source | EDARSAHUB_SQL | EDARSAHUB_SQL |

### eduardo@alpuntoycoma.mx

| Campo | Antes | Después |
|-------|-------|---------|
| Empresas SQL | 0 | 5 |
| Empresas asignadas | - | ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID |
| Empresa principal | - | ORIGEN |
| auth_source | EDARSAHUB_SQL | EDARSAHUB_SQL |

---

## 6. Empresas Asignadas por Usuario

| Usuario | Empresas | Principal |
|---------|----------|-----------|
| david.ricardez@cienfuegos.mx | CIENFUEGOS | CIENFUEGOS |
| carlos@alpuntoycoma.mx | ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID | ORIGEN |
| eduardo@alpuntoycoma.mx | ORIGEN, 130QRO, CIENFUEGOS, ESTELAR, 130MID | ORIGEN |

---

## 7. Validación de Login

| Usuario | Puede hacer login | Resultado |
|---------|-------------------|-----------|
| superadmin@test.com | ❌ NO | Sin UUID, desactivado |
| superadmin2@test.com | ❌ NO | Desactivado |
| usuario_test_portal@test.com | ❌ NO | Desactivado |
| david.ricardez@cienfuegos.mx | ✅ SÍ | EDARSAHUB_SQL |
| carlos@alpuntoycoma.mx | ✅ SÍ | EDARSAHUB_SQL |
| eduardo@alpuntoycoma.mx | ✅ SÍ | EDARSAHUB_SQL |

---

## 8. Validación de auth_source

| Email | auth_source | Status |
|-------|-------------|--------|
| admin@edarsa.com | EDARSAHUB_SQL | ✓ |
| admin@inventario.com | EDARSAHUB_SQL | ✓ |
| carlosruz@edarsa.com.mx | EDARSAHUB_SQL | ✓ |
| noxte@alpyc.com | EDARSAHUB_SQL | ✓ |
| auditoria@edarsa.com.mx | EDARSAHUB_SQL | ✓ |
| almacen@cienfuegos.mx | EDARSAHUB_SQL | ✓ |
| administracion@cienfuegos.mx | EDARSAHUB_SQL | ✓ |
| ricardo@edarsa.com.mx | EDARSAHUB_SQL | ✓ |
| david.ricardez@cienfuegos.mx | EDARSAHUB_SQL | ✓ |
| carlos@alpuntoycoma.mx | EDARSAHUB_SQL | ✓ |
| eduardo@alpuntoycoma.mx | EDARSAHUB_SQL | ✓ |

**Total: 11/11 usuarios productivos usando EDARSAHUB_SQL**

---

## 9. Validación de MONGODB_FALLBACK

| Métrica | Valor |
|---------|-------|
| Usuarios productivos con MONGODB_FALLBACK | **0** |
| Usuarios @test.com (desactivados) | 5 |
| Total usuarios usando MongoDB | 0 |

---

## 10. Validación de SQL_ERROR_FALLBACK

| Métrica | Valor |
|---------|-------|
| SQL_ERROR_FALLBACK detectados | **0** |

---

## 11. Evidencia de No Regresión

| Endpoint | Resultado |
|----------|-----------|
| GET /api/auth/me | ✓ OK para todos los usuarios |
| GET /api/servers | ✓ 8 servidores |
| GET /api/v2/comercial/dashboard | ✓ 4 unidades |
| GET /api/comercial/tablero-ejecutivo | ✓ OK |
| SUPERADMIN admin@inventario.com | ✓ 5 empresas |
| SUPERADMIN ricardo@edarsa.com.mx | ✓ 5 empresas |

---

## 12. Riesgos Residuales

| Riesgo | Severidad | Descripción |
|--------|-----------|-------------|
| david.ricardez@ ve 0 servidores | Media | No es problema de Auth. Los servidores no tienen `empresa_id` en MongoDB. El filtrado usa `allowed_servers` que no tiene. Requiere FASE 3 o asignación manual. |
| Usuarios @test.com eliminación física pendiente | Baja | Están desactivados pero aún existen en MongoDB. Eliminación física puede hacerse en limpieza posterior. |

### Nota sobre david.ricardez@cienfuegos.mx

El usuario puede autenticarse correctamente y tiene acceso a CIENFUEGOS. Sin embargo, ve 0 servidores porque:

1. Su rol es `Usuario` (no Admin/SuperAdmin)
2. El sistema filtra servidores por `allowed_servers` para usuarios no-admin
3. No tiene `allowed_servers` configurado
4. Los servidores en MongoDB no tienen `empresa_id` para filtrar por empresas

**Esto NO es un problema de Auth/RBAC**, sino de la configuración de permisos de servidores que es anterior a la migración.

---

## 13. Recomendación Final sobre FASE 2-G

### ¿Se puede proceder con FASE 2-G (Eliminar fallback MongoDB)?

**SÍ, se puede proceder.**

Justificación:
- ✅ Todos los usuarios productivos (11) usan EDARSAHUB_SQL
- ✅ MONGODB_FALLBACK = 0 para productivos
- ✅ SQL_ERROR_FALLBACK = 0
- ✅ Usuarios @test.com desactivados (ya no generan fallback)
- ✅ No hay dependencia de MongoDB para autenticación productiva

### Prerrequisitos cumplidos:

| # | Prerrequisito | Estado |
|---|---------------|--------|
| 1 | Usuarios @test.com desactivados | ✅ |
| 2 | Usuarios productivos sin empresas resueltos | ✅ |
| 3 | MONGODB_FALLBACK = 0 para productivos | ✅ |
| 4 | SQL_ERROR_FALLBACK = 0 | ✅ |

### Riesgo de eliminar fallback:

**MÍNIMO.** Si se elimina el fallback MongoDB ahora:
- Los 11 usuarios productivos seguirán funcionando (SQL)
- Los 5 usuarios @test.com no podrán autenticarse (ya están desactivados)
- No hay usuarios que dependan de MongoDB

---

## 14. Archivos de Respaldo

| Archivo | Descripción |
|---------|-------------|
| `/app/docs/backups/FASE2F2_BACKUP_TEST_USERS.json` | Respaldo de usuarios @test.com antes de desactivar |

---

## 15. Criterios de Aceptación

| Criterio | Estado |
|----------|--------|
| Usuarios @test.com activos quedan inactivos | ✅ |
| No pueden iniciar sesión | ✅ |
| 3 usuarios productivos tienen empresas asignadas | ✅ |
| No hay usuarios productivos usando MongoDB fallback | ✅ |
| No hay SQL_ERROR_FALLBACK | ✅ |
| No se rompió ningún módulo principal | ✅ |
| Reporte generado | ✅ |

---

## 16. Resumen de Cambios

### En MongoDB:
- `superadmin@test.com`: active=false
- `superadmin2@test.com`: active=false
- `usuario_test_portal@test.com`: active=false

### En SQL (Usuario_EmpresasAsignacion):
- `david.ricardez@cienfuegos.mx` (UsuarioID=9): +1 asignación (CIENFUEGOS)
- `carlos@alpuntoycoma.mx` (UsuarioID=11): +5 asignaciones
- `eduardo@alpuntoycoma.mx` (UsuarioID=12): +5 asignaciones

**Total inserciones SQL: 11**

---

*Reporte generado bajo régimen de Autorización Controlada.*  
*Saneamiento completado. Sistema listo para FASE 2-G (eliminar fallback MongoDB).*

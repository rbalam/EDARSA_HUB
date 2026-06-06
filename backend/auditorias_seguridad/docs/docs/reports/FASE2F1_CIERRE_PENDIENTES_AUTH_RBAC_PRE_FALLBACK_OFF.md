# FASE 2-F.1: Cierre de Pendientes Auth/RBAC Pre-Fallback MongoDB Off

**Fecha de ejecución:** 14-Dic-2025  
**Régimen:** Autorización Controlada  
**Estado:** ✅ COMPLETADA  
**Objetivo:** Resolver formalmente usuarios pendientes antes de eliminar fallback MongoDB

---

## 1. Resumen Ejecutivo

Se auditaron 9 usuarios pendientes:
- 5 usuarios @test.com (no migrados a SQL)
- 3 usuarios productivos sin empresas_permitidas (migrados a SQL pero con 0 empresas)
- 1 usuario especial (superadmin@test.com sin UUID)

**Hallazgo principal:** Solo los 5 usuarios @test.com dependen de MongoDB fallback. Los 3 usuarios productivos sin empresas ya resuelven desde SQL pero tienen acceso funcional limitado.

---

## 2. Auditoría Detallada de Usuarios

### 2.1 Usuarios @test.com

| Email | MongoDB | SQL | Activo | Rol | Empresas | auth_source | Clasificación |
|-------|---------|-----|--------|-----|----------|-------------|---------------|
| superadmin@test.com | ✓ | ✗ | ✓ | SuperAdministrador | 0 | MongoDB | TEST |
| superadmin2@test.com | ✓ | ✗ | ✓ | SuperAdministrador | 0 | MongoDB | TEST |
| usuario_test_portal@test.com | ✓ | ✗ | ✓ | Usuario | 0 | MongoDB | TEST |
| test_validacion@test.com | ✓ | ✗ | ✗ | Usuario | 0 | N/A | TEST (inactivo) |
| test_rbac_val@test.com | ✓ | ✗ | ✗ | Usuario | 0 | N/A | TEST (inactivo) |

**Notas:**
- `superadmin@test.com` no tiene UUID en MongoDB (campo `id` vacío)
- Ninguno fue migrado a SQL por decisión de FASE 2-B1
- 3 activos, 2 inactivos

### 2.2 Usuarios Productivos Sin Empresas

| Email | MongoDB | SQL | Activo | Rol | Empresas | auth_source | Clasificación |
|-------|---------|-----|--------|-----|----------|-------------|---------------|
| david.ricardez@cienfuegos.mx | ✓ | ✓ | ✓ | Usuario | 0 | EDARSAHUB_SQL | PRODUCTIVO |
| carlos@alpuntoycoma.mx | ✓ | ✓ | ✓ | Administrador | 0 | EDARSAHUB_SQL | PRODUCTIVO |
| eduardo@alpuntoycoma.mx | ✓ | ✓ | ✓ | Administrador | 0 | EDARSAHUB_SQL | PRODUCTIVO |

**Notas:**
- Los 3 están migrados a SQL correctamente
- Los 3 tienen 0 empresas tanto en MongoDB como en SQL (consistente)
- Resuelven desde `EDARSAHUB_SQL` (no dependen de fallback)

---

## 3. Detalle por Usuario

### 3.1 superadmin2@test.com

| Campo | Valor |
|-------|-------|
| En MongoDB | ✓ SÍ |
| En SQL | ✗ NO |
| Activo | ✓ SÍ |
| Rol MongoDB | SuperAdministrador |
| Empresas | 0 |
| UUID | ec59635e-e2d0-45e7-8234-987a8d5b6768 |
| auth_source | MongoDB (fallback) |
| Nombre | Super Admin Test |

**Clasificación:** TEST  
**Recomendación:** DESACTIVAR en MongoDB  
**Riesgo si elimina fallback:** Perdería acceso (no crítico - es usuario de prueba)  
**Acción requerida:** Desactivar antes de FASE 2-G o migrar a SQL si se necesita para pruebas

### 3.2 superadmin@test.com

| Campo | Valor |
|-------|-------|
| En MongoDB | ✓ SÍ |
| En SQL | ✗ NO |
| Activo | ✓ SÍ |
| Rol MongoDB | SuperAdministrador |
| Empresas | 0 |
| UUID | **N/A (vacío)** |
| auth_source | MongoDB (fallback) |

**Clasificación:** TEST (problemático)  
**Recomendación:** DESACTIVAR en MongoDB  
**Riesgo si elimina fallback:** Perdería acceso  
**Acción requerida:** Desactivar (no se puede migrar a SQL sin UUID)

### 3.3 usuario_test_portal@test.com

| Campo | Valor |
|-------|-------|
| En MongoDB | ✓ SÍ |
| En SQL | ✗ NO |
| Activo | ✓ SÍ |
| Rol MongoDB | Usuario |
| Empresas | 0 |
| UUID | 20bb73a7-361d-4432-8bcf-bda44f10699c |
| auth_source | MongoDB (fallback) |

**Clasificación:** TEST (portal proveedores?)  
**Recomendación:** DESACTIVAR o migrar si se usa en portal  
**Riesgo si elimina fallback:** Perdería acceso  
**Acción requerida:** Verificar si se usa en portal_proveedores

### 3.4 test_validacion@test.com y test_rbac_val@test.com

| Campo | Valor |
|-------|-------|
| En MongoDB | ✓ SÍ |
| En SQL | ✗ NO |
| Activo | ✗ NO |
| auth_source | N/A (inactivos) |

**Clasificación:** TEST (inactivos)  
**Recomendación:** MANTENER inactivos (ya no afectan)  
**Riesgo si elimina fallback:** Ninguno (ya están inactivos)  
**Acción requerida:** Ninguna

### 3.5 david.ricardez@cienfuegos.mx

| Campo | Valor |
|-------|-------|
| En MongoDB | ✓ SÍ |
| En SQL | ✓ SÍ |
| Activo | ✓ SÍ |
| Rol | Usuario (USUARIO) |
| Empresas MongoDB | 0 |
| Empresas SQL | 0 |
| UUID | F3BA4A2F-9CB9-4982-BE09-31FBB67866B5 |
| auth_source | EDARSAHUB_SQL |
| Nombre | David Ricaldes Mendes |

**Clasificación:** PRODUCTIVO (empleado Cienfuegos)  
**Recomendación:** ASIGNAR EMPRESA CIENFUEGOS  
**Riesgo si elimina fallback:** Ninguno (ya usa SQL)  
**Riesgo actual:** No puede ver servidores ni dashboard  
**Acción requerida:** Decisión del propietario sobre asignar empresa

### 3.6 carlos@alpuntoycoma.mx

| Campo | Valor |
|-------|-------|
| En MongoDB | ✓ SÍ |
| En SQL | ✓ SÍ |
| Activo | ✓ SÍ |
| Rol | Administrador (ADMIN) |
| Empresas MongoDB | 0 |
| Empresas SQL | 0 |
| UUID | 9DD2A053-4473-454A-B871-B257361F4701 |
| auth_source | EDARSAHUB_SQL |
| Nombre | Carlos Alberto Aguirre de Leon |

**Clasificación:** PRODUCTIVO (administrador alpuntoycoma)  
**Recomendación:** ASIGNAR EMPRESAS o DESACTIVAR  
**Riesgo si elimina fallback:** Ninguno (ya usa SQL)  
**Riesgo actual:** No puede ver servidores ni dashboard  
**Acción requerida:** Decisión del propietario

### 3.7 eduardo@alpuntoycoma.mx

| Campo | Valor |
|-------|-------|
| En MongoDB | ✓ SÍ |
| En SQL | ✓ SÍ |
| Activo | ✓ SÍ |
| Rol | Administrador (ADMIN) |
| Empresas MongoDB | 0 |
| Empresas SQL | 0 |
| UUID | 12D4041C-F013-4414-BD96-592E9D61559C |
| auth_source | EDARSAHUB_SQL |
| Nombre | Eduardo Jose Medina García |

**Clasificación:** PRODUCTIVO (administrador alpuntoycoma)  
**Recomendación:** ASIGNAR EMPRESAS o DESACTIVAR  
**Riesgo si elimina fallback:** Ninguno (ya usa SQL)  
**Riesgo actual:** No puede ver servidores ni dashboard  
**Acción requerida:** Decisión del propietario

---

## 4. Impacto de Usuarios Sin Empresas

### Test realizado con david.ricardez@cienfuegos.mx (0 empresas)

| Endpoint | Resultado | Impacto |
|----------|-----------|---------|
| GET /api/auth/me | ✓ OK | Puede autenticarse |
| GET /api/servers | 0 servidores | No ve ningún servidor |
| GET /api/v2/comercial/dashboard | Error: "No tiene unidades de negocio asignadas" | No puede usar tablero |

**Conclusión:** Los usuarios sin empresas pueden hacer login pero no tienen acceso funcional a datos de negocio.

---

## 5. Dependencia de MongoDB Fallback

### Usuarios que dependen de MongoDB fallback:

| Usuario | Razón |
|---------|-------|
| superadmin@test.com | No migrado, sin UUID |
| superadmin2@test.com | No migrado |
| usuario_test_portal@test.com | No migrado |

**Total: 3 usuarios activos**

### Usuarios que NO dependen de fallback:

| Usuario | Razón |
|---------|-------|
| david.ricardez@cienfuegos.mx | Ya usa EDARSAHUB_SQL |
| carlos@alpuntoycoma.mx | Ya usa EDARSAHUB_SQL |
| eduardo@alpuntoycoma.mx | Ya usa EDARSAHUB_SQL |
| test_validacion@test.com | Inactivo |
| test_rbac_val@test.com | Inactivo |

---

## 6. Impacto de Eliminar Fallback MongoDB Hoy

### Si se elimina fallback MongoDB:

| Impacto | Usuarios afectados | Severidad |
|---------|-------------------|-----------|
| Pérdida de acceso | 3 (@test.com activos) | BAJA (son usuarios de prueba) |
| Usuarios sin cambio | 3 (productivos sin empresas) | NINGUNO |
| Usuarios productivos | 8 (migrados con empresas) | NINGUNO |

### Riesgo total: BAJO

Los únicos usuarios afectados serían los 3 @test.com activos, que son usuarios de prueba.

---

## 7. Recomendaciones por Usuario

| Usuario | Recomendación | Prioridad |
|---------|---------------|-----------|
| superadmin@test.com | DESACTIVAR en MongoDB | Alta |
| superadmin2@test.com | DESACTIVAR en MongoDB | Alta |
| usuario_test_portal@test.com | Verificar uso en portal, luego DESACTIVAR o MIGRAR | Media |
| test_validacion@test.com | MANTENER inactivo | Baja |
| test_rbac_val@test.com | MANTENER inactivo | Baja |
| david.ricardez@cienfuegos.mx | Asignar CIENFUEGOS o DESACTIVAR | Media |
| carlos@alpuntoycoma.mx | Asignar empresas o DESACTIVAR | Media |
| eduardo@alpuntoycoma.mx | Asignar empresas o DESACTIVAR | Media |

---

## 8. Prerrequisitos para FASE 2-G

### Obligatorios:

| # | Prerrequisito | Estado |
|---|---------------|--------|
| 1 | Desactivar superadmin@test.com | ⬜ Pendiente autorización |
| 2 | Desactivar superadmin2@test.com | ⬜ Pendiente autorización |
| 3 | Decisión sobre usuario_test_portal@test.com | ⬜ Pendiente autorización |
| 4 | Decisión sobre usuarios sin empresas (3) | ⬜ Pendiente autorización |
| 5 | Período de observación adicional (opcional) | ⬜ A criterio del propietario |

### Opcionales pero recomendados:

| # | Acción | Beneficio |
|---|--------|-----------|
| 1 | Asignar CIENFUEGOS a david.ricardez@ | Usuario funcional |
| 2 | Definir empresas para carlos@ y eduardo@ | Usuarios funcionales |

---

## 9. Decisión Requerida

### ¿Se puede proceder con FASE 2-G?

**SÍ, condicionalmente**, si el propietario autoriza:

1. **Desactivar los 3 usuarios @test.com activos** (superadmin@test.com, superadmin2@test.com, usuario_test_portal@test.com)

2. **Aceptar que los 3 usuarios sin empresas** (david.ricardez@, carlos@, eduardo@) seguirán con acceso limitado hasta que se les asigne empresas.

### Alternativa:

Mantener fallback MongoDB activo hasta:
- Desactivar usuarios @test.com
- Resolver usuarios sin empresas

---

## 10. Resumen de Acciones Pendientes

| Acción | Autorización requerida |
|--------|----------------------|
| Desactivar superadmin@test.com en MongoDB | SÍ |
| Desactivar superadmin2@test.com en MongoDB | SÍ |
| Desactivar usuario_test_portal@test.com en MongoDB | SÍ |
| Asignar CIENFUEGOS a david.ricardez@cienfuegos.mx en SQL | SÍ |
| Definir empresas para carlos@alpuntoycoma.mx | SÍ |
| Definir empresas para eduardo@alpuntoycoma.mx | SÍ |
| Proceder con FASE 2-G (eliminar fallback) | SÍ |

---

## 11. Criterios de Aceptación

| Criterio | Estado |
|----------|--------|
| Todos los usuarios pendientes tienen decisión recomendada | ✅ |
| Se sabe exactamente quién depende de MongoDB fallback | ✅ (3 @test.com activos) |
| Se puede decidir con seguridad si FASE 2-G procede | ✅ (Sí, si se desactivan @test.com) |
| Reporte generado | ✅ |

---

## 12. Archivos de Referencia

| Archivo | Descripción |
|---------|-------------|
| `/app/docs/reports/FASE2F_OBSERVACION_SQL_FIRST_AUTH.md` | Reporte FASE 2-F |
| `/app/docs/reports/FASE2B1_POBLADO_USUARIOS_BASE_SQL.md` | Decisión original de excluir @test.com |

---

*Reporte generado bajo régimen de Autorización Controlada.*  
*No se ejecutaron cambios. Solo diagnóstico y recomendaciones.*

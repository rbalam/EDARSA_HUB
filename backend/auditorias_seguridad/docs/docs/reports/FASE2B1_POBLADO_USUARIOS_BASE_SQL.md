# FASE 2-B1: POBLADO DE USUARIOS BASE AUTH/RBAC SQL

**Fecha:** 14-Dic-2025  
**Estado:** COMPLETADO  
**Autor:** Agente E1 (Régimen de Autorización Controlada)

---

## 1. SCRIPT EJECUTADO

### 1.1 Lógica del script

```python
# FASE 2-B1: Poblar usuarios base en Usuario_Catalogo
# - Actualizar 9 usuarios existentes con PublicUUID y MongoLegacyID desde MongoDB
# - Insertar usuarios productivos activos faltantes
# - NO poblar roles ni asignaciones
# - NO modificar código de autenticación

# PASO 1: UPDATE para usuarios existentes
UPDATE Usuario_Catalogo 
SET PublicUUID = <uuid_mongo>,
    MongoLegacyID = <objectid_mongo>,
    FechaModificacion = GETUTCDATE(),
    ModifiedBy = 'FASE2B1_MIGRATION'
WHERE LOWER(Email) = <email> 
  AND (PublicUUID IS NULL OR MongoLegacyID IS NULL)

# PASO 2: INSERT para usuarios faltantes (sin especificar UsuarioID - IDENTITY)
INSERT INTO Usuario_Catalogo (
    CodigoUsuario, Username, Email, PasswordHashTexto,
    Nombre, Activo, FechaAlta, CreatedBy, PublicUUID, MongoLegacyID
) VALUES (...)

# PASO 3: INSERT trazabilidad
INSERT INTO Usuario_MigracionMongoTrace (...)
```

### 1.2 Reglas aplicadas

| Regla | Implementación |
|-------|----------------|
| Idempotente | UPDATE solo si PublicUUID/MongoLegacyID es NULL |
| No duplicar emails | Verificación previa de existencia |
| No sobrescribir hashes | UPDATE no toca PasswordHashTexto |
| Excluir inactivos | `active = False` → omitir |
| Excluir sin UUID | `id = None` → omitir |
| Excluir @test.com | Dominio test → omitir |
| Trazabilidad | INSERT en Usuario_MigracionMongoTrace |

---

## 2. USUARIOS ACTUALIZADOS (9)

| UsuarioID | Email | Acción | PublicUUID | MongoLegacyID |
|-----------|-------|--------|------------|---------------|
| 1 | admin@edarsa.com | UPDATE_UUID_AND_MONGOID | F648DD3F-... | 69d88ca7cca4... |
| 2 | admin@inventario.com | UPDATE_UUID_AND_MONGOID | 0DA77B7B-... | 69e4576bbfb5... |
| 3 | carlosruz@edarsa.com.mx | UPDATE_UUID_AND_MONGOID | A5E56ED0-... | 69e4576bbfb5... |
| 4 | noxte@alpyc.com | UPDATE_UUID_AND_MONGOID | A72B325B-... | 69e4576bbfb5... |
| 5 | auditoria@edarsa.com.mx | UPDATE_UUID_AND_MONGOID | E200DE9E-... | 69e4576bbfb5... |
| 6 | almacen@cienfuegos.mx | UPDATE_UUID_AND_MONGOID | 30702651-... | 69e4576bbfb5... |
| 7 | administracion@cienfuegos.mx | UPDATE_UUID_AND_MONGOID | 57DBB5AD-... | 69e4576bbfb5... |
| 8 | ricardo@edarsa.com.mx | UPDATE_UUID_AND_MONGOID | 1E18A085-... | 69e6f703a9e9... |
| 9 | david.ricardez@cienfuegos.mx | UPDATE_UUID_AND_MONGOID | F3BA4A2F-... | 69e75b91bfb9... |

**Resultado:** 9 usuarios actualizados con trazabilidad MongoDB completa.

---

## 3. USUARIOS INSERTADOS (2)

| UsuarioID | Email | Role (MongoDB) | PublicUUID | MongoLegacyID |
|-----------|-------|----------------|------------|---------------|
| 11 | carlos@alpuntoycoma.mx | Administrador | 9DD2A053-... | 6a03dc89004c... |
| 12 | eduardo@alpuntoycoma.mx | Administrador | 12D4041C-... | 6a03dcf3004c... |

**Nota:** UsuarioID 10 no existe (gap en IDENTITY, posiblemente borrado anterior).

---

## 4. USUARIOS OMITIDOS (6)

| Email | Razón |
|-------|-------|
| test_validacion@test.com | Usuario inactivo (role=Usuario) |
| test_rbac_val@test.com | Usuario inactivo (role=Usuario) |
| **superadmin@test.com** | **Usuario sin PublicUUID (no se genera UUID arbitrario)** |
| superadmin2@test.com | Usuario de prueba (@test.com) - requiere decisión explícita |
| usuario_test_portal@test.com | Usuario de prueba (@test.com) - requiere decisión explícita |
| test_propinas@edarsa.com | Usuario inactivo (role=DESHABILITADO) |

---

## 5. DECISIÓN: superadmin@test.com

### 5.1 Hallazgo
- Email: `superadmin@test.com`
- Role: `SuperAdministrador`
- Active: `True`
- UUID (`id`): **AUSENTE**
- Password hash: Existe

### 5.2 Decisión tomada
**NO MIGRAR** - El usuario no tiene `id` (PublicUUID) en MongoDB.

### 5.3 Justificación
1. El campo `id` (UUID) es crítico para el JWT actual
2. Generar un UUID arbitrario violaría la trazabilidad
3. El dominio `@test.com` indica usuario de prueba
4. Si es necesario, crear manualmente con UUID nuevo

### 5.4 Alternativas para el usuario
- **Opción A:** Crear manualmente en MongoDB con UUID y luego migrar
- **Opción B:** Excluir permanentemente (recomendado para usuarios test)
- **Opción C:** Migrar con UUID generado y documentar (no autorizado en esta fase)

---

## 6. VALIDACIÓN DE HASHES BCRYPT

### 6.1 Usuarios originales (9)

| UsuarioID | Email | Hash Prefijo | Estado |
|-----------|-------|--------------|--------|
| 1 | admin@edarsa.com | $2b$12$wSYE3uHWCzV3C | ✓ INTACTO |
| 2 | admin@inventario.com | $2b$12$gwYTEWCA93G92 | ✓ INTACTO |
| 3 | carlosruz@edarsa.com.mx | $2b$12$O/16/yfoE2Lic | ✓ INTACTO |
| 4 | noxte@alpyc.com | $2b$12$kEluKx1PCSJMu | ✓ INTACTO |
| 5 | auditoria@edarsa.com.mx | $2b$12$IfDAUVS.iuv4w | ✓ INTACTO |
| 6 | almacen@cienfuegos.mx | $2b$12$2ZjKStf5sAESy | ✓ INTACTO |
| 7 | administracion@cienfuegos.mx | $2b$12$BBpGbxMJ6qsHX | ✓ INTACTO |
| 8 | ricardo@edarsa.com.mx | $2b$12$XHQU24O/awrID | ✓ INTACTO |
| 9 | david.ricardez@cienfuegos.mx | $2b$12$q/ITr2B/3be5z | ✓ INTACTO |

### 6.2 Usuarios nuevos (2)

| UsuarioID | Email | Hash Prefijo | Fuente |
|-----------|-------|--------------|--------|
| 11 | carlos@alpuntoycoma.mx | $2b$12$... | MongoDB (copiado) |
| 12 | eduardo@alpuntoycoma.mx | $2b$12$... | MongoDB (copiado) |

**RESULTADO:** Todos los hashes bcrypt preservados sin modificación.

---

## 7. VALIDACIÓN PublicUUID

| Métrica | Valor |
|---------|-------|
| Total usuarios SQL | 11 |
| Con PublicUUID | 11 |
| Sin PublicUUID | 0 |
| Activos sin PublicUUID | 0 |

**RESULTADO:** ✓ Todos los usuarios activos tienen PublicUUID.

---

## 8. VALIDACIÓN MongoLegacyID

| Métrica | Valor |
|---------|-------|
| Total usuarios SQL | 11 |
| Con MongoLegacyID | 11 |
| Sin MongoLegacyID | 0 |

**RESULTADO:** ✓ Todos los usuarios tienen trazabilidad MongoDB.

---

## 9. CONTEOS ANTES/DESPUÉS

### 9.1 MongoDB

| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| Total usuarios | 17 | 17 | Sin cambios |
| Activos | 14 | 14 | Sin cambios |
| Inactivos | 3 | 3 | Sin cambios |

### 9.2 SQL

| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| Total usuarios | 9 | 11 | +2 insertados |
| Activos | 9 | 11 | +2 insertados |
| Con PublicUUID | 0 | 11 | +11 poblados |
| Con MongoLegacyID | 0 | 11 | +11 poblados |
| Emails duplicados | 0 | 0 | Sin cambios |
| Hashes nulos | 0 | 0 | Sin cambios |

### 9.3 Tablas de asignación (sin cambios)

| Tabla | Antes | Después |
|-------|-------|---------|
| Usuario_RolesAsignacion | 0 | 0 |
| Usuario_EmpresasAsignacion | 0 | 0 |

### 9.4 Trazabilidad

| Tabla | Antes | Después |
|-------|-------|---------|
| Usuario_MigracionMongoTrace | 9 | 11 |

---

## 10. EVIDENCIA DE NO REGRESIÓN

### 10.1 Archivos de código NO modificados

| Archivo | MD5 |
|---------|-----|
| core/security.py | 66a841928ccb2d40d8f93a15f86e06be |
| modules/auth/repository.py | add919775f233265d4fbd6a7cd6c1a6e |
| modules/auth/service.py | 01693a1c6ca4e4e20edd7c8d6f2402ed |
| modules/auth/routes.py | 94caa2db6808241165e280b020dd1b26 |

### 10.2 Verificación de flujo de login

```
✓ MongoDB sigue siendo fuente de login
✓ Usuario admin@inventario.com encontrado en MongoDB
✓ UUID en MongoDB: 0da77b7b-fe88-4e23-98bc-9cbf543d5ee3
✓ Usuario carlos@alpuntoycoma.mx existe en MongoDB (nuevo, puede hacer login)
```

### 10.3 Endpoints verificados

| Endpoint | Estado |
|----------|--------|
| /api/servers (sin auth) | 403 (esperado) |
| Health check | ✓ Backend running |

### 10.4 Confirmaciones

- [x] Login/JWT/get_current_user NO modificados
- [x] MongoDB sigue siendo fuente de autenticación
- [x] EDARSAHUB SQL preparado pero NO activo para auth
- [x] Usuario_RolesAsignacion vacía
- [x] Usuario_EmpresasAsignacion vacía

---

## 11. RIESGOS RESIDUALES

| ID | Riesgo | Probabilidad | Impacto | Mitigación |
|----|--------|--------------|---------|------------|
| R1 | Usuario superadmin@test.com sin acceso SQL | Baja | Bajo | Es usuario test, crear manualmente si necesario |
| R2 | Usuarios @test.com activos sin migrar | Baja | Bajo | Decisión explícita requerida |
| R3 | Gap en UsuarioID (10 faltante) | Baja | Ninguno | No afecta funcionalidad |

---

## 12. RECOMENDACIÓN PARA FASE 2-B2

### 12.1 Siguiente paso: Poblar Usuario_RolesAsignacion

Mapeo propuesto de roles MongoDB → SQL:

| Role MongoDB | RolID SQL | CodigoRol SQL |
|--------------|-----------|---------------|
| SuperAdministrador | 6 | SUPERADMIN |
| Administrador | 1 | ADMIN |
| Supervisor | 7 | SUPERVISOR |
| Usuario | 8 | USUARIO |

### 12.2 Acciones requeridas en FASE 2-B2

1. Insertar registros en `Usuario_RolesAsignacion` para los 11 usuarios
2. Mapear `user.role` de MongoDB al `RolID` correspondiente en SQL
3. Establecer `EsPrincipal = 1` para el rol único de cada usuario

### 12.3 Decisiones pendientes

- [ ] Confirmar mapeo de roles
- [ ] Decidir si migrar usuarios @test.com activos
- [ ] Decidir si crear superadmin@test.com con UUID nuevo

---

## 13. CRITERIOS DE ACEPTACIÓN CUMPLIDOS

| Criterio | Estado |
|----------|--------|
| 9 usuarios SQL existentes conservan su hash | ✓ |
| Usuarios productivos activos faltantes insertados | ✓ (2 de 2) |
| No hay emails duplicados | ✓ |
| No hay usuarios activos productivos sin PublicUUID | ✓ |
| No se poblaron roles/asignaciones | ✓ |
| Login/JWT/get_current_user no modificados | ✓ |
| MongoDB sigue siendo fuente de login | ✓ |
| Reporte generado | ✓ |

---

**ESTADO:** FASE 2-B1 COMPLETADA — ESPERANDO AUTORIZACIÓN PARA FASE 2-B2

*Documento generado bajo régimen de Autorización Controlada.*  
*Solo se ejecutó DML (UPDATE/INSERT) en EDARSAHUB. No se modificó código de autenticación.*

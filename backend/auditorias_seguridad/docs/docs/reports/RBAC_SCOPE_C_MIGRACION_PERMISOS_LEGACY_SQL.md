# RBAC-SCOPE-C: Migración de Permisos Legacy MongoDB → SQL

**Fecha:** 14 de Diciembre de 2025  
**Estado:** ✅ COMPLETADA  
**Autor:** Agente E1  
**Régimen:** Autorización Controlada

---

## 1. Script Ejecutado

```python
# Conexión a MongoDB (solo lectura)
mongo_users = await mongo_db.users.find({
    "id": 1, "email": 1, "name": 1,
    "allowed_servers": 1, "allowed_sucursales": 1, "allowed_warehouses": 1
}).to_list(100)

# Mapeo de usuarios: MongoDB ID → SQL UsuarioID
# Via: Usuario_Catalogo.PublicUUID (case-insensitive)

# Mapeo de servidores: MongoDB UUID → SQL Servidores_Conexiones.id
# Via: comparación directa de UUID (case-insensitive)

# Inserción idempotente (verifica existencia antes de insertar)
INSERT INTO Usuario_ServidoresAsignacion 
    (UsuarioID, ServidorID, LegacyMongoValue, Activo, FechaCreacion, Observaciones)
VALUES (@UsuarioID, @ServidorID, @LegacyMongoValue, 1, GETDATE(), 
        'Migrado RBAC-SCOPE-C desde MongoDB 2025-12-14')
```

---

## 2. Usuarios Procesados

| # | Email | Nombre | UsuarioID SQL |
|---|-------|--------|---------------|
| 1 | admin@inventario.com | Administrador | 2 |
| 2 | carlosruz@edarsa.com.mx | Carlos Ruz | 3 |
| 3 | noxte@alpyc.com | Nestor Oxte | 4 |
| 4 | auditoria@edarsa.com.mx | William Chuc | 5 |
| 5 | almacen@cienfuegos.mx | Cristina Chi | 6 |
| 6 | administracion@cienfuegos.mx | Daniel Pool | 7 |
| 7 | david.ricardez@cienfuegos.mx | David Ricaldes Mendes | 9 |

**Total usuarios procesados:** 7

---

## 3. Permisos Migrados por Usuario

| Usuario | Servidores | Sucursales | Almacenes | Total |
|---------|------------|------------|-----------|-------|
| admin@inventario.com | 8 | 0 | 0 | 8 |
| carlosruz@edarsa.com.mx | 1 | 0 | 2 | 3 |
| noxte@alpyc.com | 1 | 2 | 5 | 8 |
| auditoria@edarsa.com.mx | 3 | 2 | 20 | 25 |
| almacen@cienfuegos.mx | 1 | 0 | 10 | 11 |
| administracion@cienfuegos.mx | 1 | 1 | 9 | 11 |
| david.ricardez@cienfuegos.mx | 4 | 0 | 6 | 10 |
| **TOTAL** | **19** | **5** | **52** | **76** |

---

## 4. Servidores Migrados por Usuario

### admin@inventario.com (8 servidores)
| ServidorID (UUID) | Servidor |
|-------------------|----------|
| 1b230a06-ffaf-4c70-bd27-b1be3579dea6 | ManagmentPro |
| 6d053c22-523e-48c0-b72b-96081e2d781b | CIENFUEGOS |
| a5547321-1139-4d2b-9d53-182ca737b6b6 | 130° MERIDA |
| a5ff0e25-f029-43db-b634-d4ac814c904f | LA ESTELAR |
| d1d8c70f-c3d0-4407-ae50-f09e8e5992ee | MPRO TABLAJERIA |
| 6d859026-710a-4920-9a44-6da98fabc690 | CIENFUEGOS TABLAJERIA |
| b5175237-5e57-41f3-ab6d-b5ae2f5e780b | HR2020 ESCRITURA |
| d8425038-5e57-42d9-8f3a-62e287888874 | PRUEBAS SOFTRESTAURANT |

### carlosruz@edarsa.com.mx (1 servidor)
| ServidorID | Servidor |
|------------|----------|
| 6d053c22-523e-48c0-b72b-96081e2d781b | CIENFUEGOS |

### noxte@alpyc.com (1 servidor)
| ServidorID | Servidor |
|------------|----------|
| 1b230a06-ffaf-4c70-bd27-b1be3579dea6 | ManagmentPro |

### auditoria@edarsa.com.mx (3 servidores)
| ServidorID | Servidor |
|------------|----------|
| 1b230a06-ffaf-4c70-bd27-b1be3579dea6 | ManagmentPro |
| 6d053c22-523e-48c0-b72b-96081e2d781b | CIENFUEGOS |
| a5ff0e25-f029-43db-b634-d4ac814c904f | LA ESTELAR |

### almacen@cienfuegos.mx (1 servidor)
| ServidorID | Servidor |
|------------|----------|
| 6d053c22-523e-48c0-b72b-96081e2d781b | CIENFUEGOS |

---

## 5. Sucursales Migradas por Usuario

| Usuario | Servidor | SucursalCodigo | LegacyMongoValue |
|---------|----------|----------------|------------------|
| noxte@alpyc.com | ManagmentPro | 0023 | 0023 |
| noxte@alpyc.com | ManagmentPro | 0021 | 0021 |
| auditoria@edarsa.com.mx | ManagmentPro | 0021 | 0021 |
| auditoria@edarsa.com.mx | ManagmentPro | 0023 | 0023 |
| administracion@cienfuegos.mx | CIENFUEGOS | default | default |

**Total sucursales migradas:** 5

---

## 6. Almacenes Migrados por Usuario

### carlosruz@edarsa.com.mx (CIENFUEGOS)
`003`, `004`

### noxte@alpyc.com (ManagmentPro)
`0003`, `0006`, `0004`, `0007`, `0002`

### auditoria@edarsa.com.mx
- **ManagmentPro:** `0003`, `0006`, `0001`, `0004`, `0007`, `0002`
- **CIENFUEGOS:** `004`, `002`, `003`, `100`, `200`, `400`, `300`
- **LA ESTELAR:** `001`, `100`, `002`, `200`, `003`, `300`, `900`

### almacen@cienfuegos.mx (CIENFUEGOS)
`001`, `004`, `200`, `400`, `002`, `005`, `299`, `003`, `100`, `300`

### administracion@cienfuegos.mx (CIENFUEGOS)
`001`, `004`, `200`, `400`, `002`, `299`, `003`, `100`, `300`

### david.ricardez@cienfuegos.mx (CIENFUEGOS)
`004`, `200`, `400`, `002`, `100`, `300`

**Total almacenes migrados:** 52

---

## 7. Valores No Mapeados

| Tipo | Valor | Usuario | Razón |
|------|-------|---------|-------|
| Ninguno | - | - | Todos los valores fueron mapeados correctamente |

**✅ No hubo valores no mapeados.**

---

## 8. Duplicados Evitados

| Métrica | Valor |
|---------|-------|
| Duplicados detectados en re-ejecución | 19 |
| Duplicados insertados | 0 |

**✅ El script es idempotente.** Al re-ejecutar, detecta 19 servidores ya existentes y no los duplica.

---

## 9. Conteos Antes/Después

### Antes de Migración (MongoDB)

| Métrica | Valor |
|---------|-------|
| Usuarios con allowed_servers | 7 |
| Usuarios con allowed_sucursales | 3 |
| Usuarios con allowed_warehouses | 6 |
| Total asignaciones servidores | 19 |
| Total asignaciones sucursales | 5 |
| Total asignaciones almacenes | 52 |

### Después de Migración (SQL)

| Tabla | Registros |
|-------|-----------|
| Usuario_ServidoresAsignacion | 19 |
| Usuario_SucursalesAsignacion | 5 |
| Usuario_AlmacenesAsignacion | 52 |

**✅ Conteos coinciden exactamente.**

---

## 10. Validación de Usuarios Críticos

| Usuario | Esperado Serv. | SQL Serv. | Esperado Suc. | SQL Suc. | Esperado Alm. | SQL Alm. | Estado |
|---------|----------------|-----------|---------------|----------|---------------|----------|--------|
| admin@inventario.com | 8 | 8 | 0 | 0 | 0 | 0 | ✅ |
| carlosruz@edarsa.com.mx | 1 | 1 | 0 | 0 | 2 | 2 | ✅ |
| noxte@alpyc.com | 1 | 1 | 2 | 2 | 5 | 5 | ✅ |
| auditoria@edarsa.com.mx | 3 | 3 | 2 | 2 | 20 | 20 | ✅ |
| almacen@cienfuegos.mx | 1 | 1 | 0 | 0 | 10 | 10 | ✅ |

**✅ TODOS LOS USUARIOS CRÍTICOS VALIDADOS**

---

## 11. Confirmación MongoDB No Modificado

| Verificación | Estado |
|--------------|--------|
| MongoDB solo fue leído (find) | ✅ |
| No se ejecutó update en MongoDB | ✅ |
| No se ejecutó delete en MongoDB | ✅ |
| No se ejecutó insert en MongoDB | ✅ |
| allowed_servers preservados | ✅ |
| allowed_sucursales preservados | ✅ |
| allowed_warehouses preservados | ✅ |

---

## 12. Confirmación Comportamiento Productivo No Cambió

| Validación | Estado | Resultado |
|------------|--------|-----------|
| Login funciona | ✅ | admin@inventario.com OK |
| JWT válido | ✅ | Token generado correctamente |
| GET /api/users | ✅ | 11 usuarios |
| GET /api/servers | ✅ | 8 servidores |
| PUT /api/users/{id}/permissions | ✅ | HTTP 200 (hotfix MongoDB) |
| Hotfix MongoDB activo | ✅ | Carlos Ruz muestra permisos via API |
| Departamentos endpoint | ✅ | 6 departamentos CIENFUEGOS |

**✅ El comportamiento productivo NO cambió.** El sistema sigue usando el hotfix MongoDB para lectura/escritura de permisos. Las tablas SQL están pobladas pero aún no se usan productivamente.

---

## 13. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| SQL y MongoDB podrían desincronizarse | **Media** | Próxima fase (RBAC-SCOPE-D/E) cambiará lectura/escritura a SQL |
| Hotfix MongoDB sigue activo | **Baja** | Intencionalmente preservado hasta RBAC-SCOPE-D |
| Datos duplicados si se re-migra sin verificación | **Baja** | Script ya es idempotente |

---

## 14. Recomendación para RBAC-SCOPE-D

**Próximo paso autorizado:** FASE RBAC-SCOPE-D - Lectura de Permisos desde SQL

**Acciones propuestas:**
1. Modificar `get_all_users()` en `repository.py`:
   - Eliminar lectura de `allowed_servers`, `allowed_sucursales`, `allowed_warehouses` desde MongoDB
   - Agregar JOINs a las nuevas tablas SQL:
     - `Usuario_ServidoresAsignacion`
     - `Usuario_SucursalesAsignacion`
     - `Usuario_AlmacenesAsignacion`
   - Mantener estructura JSON compatible con frontend

2. Modificar `get_users_by_empresas()` para usar misma lógica

3. Preservar hotfix MongoDB como fallback temporal durante validación

4. Validar que frontend renderiza correctamente los permisos desde SQL

**NO modificar todavía:**
- `update_user_permissions()` (RBAC-SCOPE-E)
- Frontend
- Login/JWT

---

## Conclusión

**FASE RBAC-SCOPE-C COMPLETADA EXITOSAMENTE.**

Los permisos legacy han sido migrados de MongoDB a EDARSAHUB SQL:
- ✅ 19 asignaciones de servidores migradas
- ✅ 5 asignaciones de sucursales migradas
- ✅ 52 asignaciones de almacenes migradas
- ✅ 0 valores no mapeados
- ✅ 0 duplicados insertados
- ✅ Todos los usuarios críticos validados
- ✅ MongoDB solo fue leído, no modificado
- ✅ Comportamiento productivo sin cambios
- ✅ Script idempotente confirmado

**Próximo paso:** Esperar autorización para RBAC-SCOPE-D (Lectura de Permisos desde SQL)

---

**Validado por:** Agente E1  
**Fecha validación:** 14 de Diciembre de 2025

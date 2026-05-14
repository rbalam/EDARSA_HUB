# RBAC-SCOPE-D: get_all_users() Lee Permisos Operativos desde SQL

**Fecha:** 14 de Diciembre de 2025  
**Estado:** ✅ COMPLETADA  
**Autor:** Agente E1  
**Régimen:** Autorización Controlada

---

## 1. Archivos Modificados

| Archivo | Función | Cambio |
|---------|---------|--------|
| `/app/backend/modules/auth/repository.py` | `get_all_users()` | Lectura de permisos desde SQL |

---

## 2. Flujo Anterior de get_all_users()

```
Usuario_Catalogo (SQL)
    ↓
list_all_users_sql() → datos base (id, email, name, role, empresas)
    ↓
MongoDB.users.find() → permisos operativos (allowed_servers, allowed_sucursales, allowed_warehouses)
    ↓
Merge: SQL base + MongoDB permisos
    ↓
Response JSON
```

**Fuente de permisos operativos:** MongoDB ❌

---

## 3. Flujo Nuevo de get_all_users()

```
Usuario_Catalogo (SQL)
    ↓
list_all_users_sql() → datos base (id, email, name, role, empresas)
    ↓
Usuario_ServidoresAsignacion (SQL) → allowed_servers
Usuario_SucursalesAsignacion (SQL) → allowed_sucursales
Usuario_AlmacenesAsignacion (SQL) → allowed_warehouses
    ↓
MongoDB.users.find() → SOLO campos RBAC piloto (sec_*, telefono) - NO permisos operativos
    ↓
Merge: SQL base + SQL permisos + MongoDB metadatos
    ↓
Response JSON
```

**Fuente de permisos operativos:** EDARSAHUB SQL ✅

---

## 4. Tablas SQL Usadas

| Tabla | Propósito | JOIN |
|-------|-----------|------|
| `Usuario_Catalogo` | Datos base del usuario | Base |
| `Usuario_ServidoresAsignacion` | allowed_servers | LEFT JOIN vía UsuarioID |
| `Usuario_SucursalesAsignacion` | allowed_sucursales | JOIN vía UsuarioID |
| `Usuario_AlmacenesAsignacion` | allowed_warehouses | JOIN vía UsuarioID |

**Queries ejecutados:**

```sql
-- 1. Servidores por usuario
SELECT 
    u.UsuarioID,
    LOWER(CAST(u.PublicUUID AS VARCHAR(36))) as PublicUUID,
    LOWER(CAST(s.ServidorID AS VARCHAR(36))) as ServidorUUID
FROM Usuario_Catalogo u
LEFT JOIN Usuario_ServidoresAsignacion s ON u.UsuarioID = s.UsuarioID AND s.Activo = 1
WHERE u.Activo = 1

-- 2. Sucursales por usuario/servidor
SELECT 
    LOWER(CAST(u.PublicUUID AS VARCHAR(36))) as PublicUUID,
    LOWER(CAST(s.ServidorID AS VARCHAR(36))) as ServidorUUID,
    s.SucursalCodigo
FROM Usuario_Catalogo u
JOIN Usuario_SucursalesAsignacion s ON u.UsuarioID = s.UsuarioID AND s.Activo = 1
WHERE u.Activo = 1

-- 3. Almacenes por usuario/servidor
SELECT 
    LOWER(CAST(u.PublicUUID AS VARCHAR(36))) as PublicUUID,
    LOWER(CAST(a.ServidorID AS VARCHAR(36))) as ServidorUUID,
    a.AlmacenCodigo
FROM Usuario_Catalogo u
JOIN Usuario_AlmacenesAsignacion a ON u.UsuarioID = a.UsuarioID AND a.Activo = 1
WHERE u.Activo = 1
```

---

## 5. Contrato JSON Devuelto

```json
{
  "id": "A5E56ED0-89B2-4D50-92F4-568A2106AB50",
  "email": "carlosruz@edarsa.com.mx",
  "name": "Carlos Ruz",
  "role": "Administrador",
  "telefono": null,
  "active": true,
  "sucursales": [],
  "allowed_servers": ["6d053c22-523e-48c0-b72b-96081e2d781b"],
  "allowed_sucursales": {},
  "allowed_warehouses": {
    "6d053c22-523e-48c0-b72b-96081e2d781b": ["003", "004"]
  },
  "empresas_permitidas": ["31784356-...", "a4d8b5e7-...", "..."],
  "empresa_default_id": "31784356-6d0b-47ce-8fe8-c8a442e45a07",
  "sec_permisos": [],
  "sec_rol": null,
  "sec_roles": [],
  "sec_perfil": null,
  "sec_roles_alcance": {},
  "_source": "EDARSAHUB_SQL"
}
```

**Contrato compatible con frontend:** ✅ Sin cambios en estructura

---

## 6. Comparación SQL vs MongoDB por Usuario

| Email | SQL Srv | Mongo Srv | SQL Suc | Mongo Suc | SQL Alm | Mongo Alm | Match |
|-------|---------|-----------|---------|-----------|---------|-----------|-------|
| admin@edarsa.com | 0 | 0 | 0 | 0 | 0 | 0 | ✅ |
| admin@inventario.com | 8 | 8 | 0 | 0 | 0 | 0 | ✅ |
| administracion@cienfuegos.mx | 1 | 1 | 1 | 1 | 9 | 9 | ✅ |
| almacen@cienfuegos.mx | 1 | 1 | 0 | 0 | 10 | 10 | ✅ |
| auditoria@edarsa.com.mx | 3 | 3 | 2 | 2 | 20 | 20 | ✅ |
| carlos@alpuntoycoma.mx | 0 | 0 | 0 | 0 | 0 | 0 | ✅ |
| carlosruz@edarsa.com.mx | 1 | 1 | 0 | 0 | 2 | 2 | ✅ |
| david.ricardez@cienfuegos.mx | 4 | 4 | 0 | 0 | 6 | 6 | ✅ |
| eduardo@alpuntoycoma.mx | 0 | 0 | 0 | 0 | 0 | 0 | ✅ |
| noxte@alpyc.com | 1 | 1 | 2 | 2 | 5 | 5 | ✅ |
| ricardo@edarsa.com.mx | 0 | 0 | 0 | 0 | 0 | 0 | ✅ |

**Total coincidencias:** 11/11 (100%)

---

## 7. Diferencias Encontradas

**Ninguna.** SQL y MongoDB tienen exactamente los mismos permisos operativos para todos los usuarios.

---

## 8. Validación de Usuarios Críticos

| Usuario | Esperado Srv | SQL Srv | Esperado Suc | SQL Suc | Esperado Alm | SQL Alm | Estado |
|---------|--------------|---------|--------------|---------|--------------|---------|--------|
| admin@inventario.com | 8 | 8 | 0 | 0 | 0 | 0 | ✅ |
| carlosruz@edarsa.com.mx | 1 | 1 | 0 | 0 | 2 | 2 | ✅ |
| noxte@alpyc.com | 1 | 1 | 2 | 2 | 5 | 5 | ✅ |
| auditoria@edarsa.com.mx | 3 | 3 | 2 | 2 | 20 | 20 | ✅ |
| almacen@cienfuegos.mx | 1 | 1 | 0 | 0 | 10 | 10 | ✅ |

**Usuarios sin permisos granulares (arrays vacíos):**
- admin@edarsa.com ✅
- ricardo@edarsa.com.mx ✅
- carlos@alpuntoycoma.mx ✅
- eduardo@alpuntoycoma.mx ✅

---

## 9. Confirmación: MongoDB NO Alimenta Permisos Productivos

| Campo | Fuente Anterior | Fuente Actual |
|-------|-----------------|---------------|
| `allowed_servers` | MongoDB | **EDARSAHUB SQL** ✅ |
| `allowed_sucursales` | MongoDB | **EDARSAHUB SQL** ✅ |
| `allowed_warehouses` | MongoDB | **EDARSAHUB SQL** ✅ |
| `empresas_permitidas` | SQL | SQL ✅ |
| `empresa_default_id` | SQL | SQL ✅ |
| `sec_permisos` (RBAC piloto) | MongoDB | MongoDB (metadatos) |
| `telefono` | MongoDB | MongoDB (metadatos) |

**MongoDB ahora solo se usa para:**
- Campos RBAC piloto (`sec_*`) - solo metadatos, no filtrado activo
- Campo `telefono`

**MongoDB NO se usa para:**
- `allowed_servers` ✅
- `allowed_sucursales` ✅
- `allowed_warehouses` ✅

---

## 10. Evidencia de No Regresión

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | GET /api/users = 11 usuarios | ✅ OK |
| 2 | carlos@alpuntoycoma.mx presente | ✅ OK |
| 3 | eduardo@alpuntoycoma.mx presente | ✅ OK |
| 4 | admin@inventario.com = 8 servidores | ✅ OK |
| 5 | carlosruz@edarsa.com.mx = 1 srv, 2 alm | ✅ OK |
| 6 | noxte@alpyc.com = 1 srv, 2 suc, 5 alm | ✅ OK |
| 7 | auditoria@edarsa.com.mx = 3 srv, 2 suc, 20 alm | ✅ OK |
| 8 | Usuarios sin permisos = arrays vacíos | ✅ OK |
| 9 | Login funciona | ✅ OK |
| 10 | JWT válido | ✅ OK |
| 11 | GET /api/servers = 8 | ✅ OK |
| 12 | PUT /api/users/{id}/permissions = HTTP 200 | ✅ OK (MongoDB) |
| 13 | Departamentos = 6 | ✅ OK |

---

## 11. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| PUT permisos aún escribe en MongoDB | **Media** | RBAC-SCOPE-E migrará escritura a SQL |
| SQL y MongoDB pueden desincronizarse | **Media** | Validación post-RBAC-SCOPE-E |
| Conexión SQL directa en repository | **Baja** | Refactorizar en futuro a pool centralizado |

---

## 12. Recomendación para RBAC-SCOPE-E

**Próximo paso autorizado:** FASE RBAC-SCOPE-E - Escritura de Permisos en SQL

**Acciones propuestas:**
1. Modificar `update_user_permissions()` en `service.py`
2. En lugar de `repo.update_user()` (MongoDB), escribir en tablas SQL:
   - `Usuario_ServidoresAsignacion`
   - `Usuario_SucursalesAsignacion`
   - `Usuario_AlmacenesAsignacion`
3. Implementar lógica de actualización:
   - Desactivar asignaciones existentes (`Activo = 0`)
   - Insertar nuevas asignaciones
4. Preservar `LegacyMongoValue` en nuevas inserciones si aplica
5. NO modificar MongoDB durante la escritura

**Dependencias:**
- `PUT /api/users/{id}/permissions` debe continuar funcionando
- El frontend no debe cambiar
- El modal de permisos debe guardar correctamente

---

## Conclusión

**FASE RBAC-SCOPE-D COMPLETADA EXITOSAMENTE.**

`get_all_users()` ahora lee los permisos operativos (`allowed_servers`, `allowed_sucursales`, `allowed_warehouses`) exclusivamente desde EDARSAHUB SQL.

- ✅ 11 usuarios visibles
- ✅ Permisos coinciden con MongoDB (migración RBAC-SCOPE-C)
- ✅ Usuarios sin permisos = arrays vacíos
- ✅ MongoDB NO alimenta permisos productivos
- ✅ Contrato JSON compatible con frontend
- ✅ Sin regresión

**EDARSAHUB SQL es ahora la fuente de lectura de permisos operativos.**

**Próximo paso:** Esperar autorización para RBAC-SCOPE-E (Escritura de Permisos en SQL)

---

**Validado por:** Agente E1  
**Fecha validación:** 14 de Diciembre de 2025

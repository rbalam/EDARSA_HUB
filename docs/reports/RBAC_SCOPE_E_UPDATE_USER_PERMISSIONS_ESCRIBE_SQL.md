# RBAC-SCOPE-E: Escritura de Permisos Operativos en EDARSAHUB SQL

**Fecha:** 2026-05-13  
**Fase:** RBAC-SCOPE-E  
**Estado:** COMPLETADA  
**Autor:** Agente E1  
**Régimen:** Autorización Controlada

---

## 1. Causa de la Implementación Incompleta

El agente anterior en el fork previo realizó modificaciones parciales:
- Modificó `service.py` para usar lógica SQL inline
- **No completó** las pruebas de validación
- **No generó** el documento de cierre obligatorio

La implementación del código estaba completa, pero faltaba la validación y documentación.

---

## 2. Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `/app/backend/modules/auth/service.py` | Función `update_user_permissions()` reescrita completamente para escribir en SQL (líneas 341-499) |

**Nota:** El código fue implementado **inline** en `service.py` en lugar de crear un método separado en `user_repository_sql.py`. Esto es funcionalmente correcto aunque no sigue el patrón repository.

---

## 3. Método Implementado

```python
async def update_user_permissions(user_id: str, permissions: Dict, current_user: Dict) -> Dict:
    """
    RBAC-SCOPE-E: Actualiza los permisos operativos de un usuario en EDARSAHUB SQL.
    
    Ya NO escribe en MongoDB. Los permisos operativos se guardan en:
    - Usuario_ServidoresAsignacion
    - Usuario_SucursalesAsignacion
    - Usuario_AlmacenesAsignacion
    """
```

### Parámetros de entrada:
- `user_id`: PublicUUID del usuario (string)
- `permissions`: Dict con `allowed_servers`, `allowed_sucursales`, `allowed_warehouses`
- `current_user`: Usuario autenticado que realiza la operación

### Retorno:
- `{"message": "Permisos actualizados"}` en caso de éxito
- HTTP 403 si no tiene permisos
- HTTP 404 si el usuario no existe
- HTTP 500 si hay error SQL

---

## 4. Flujo Transaccional

```
1. Validar permisos del current_user (mínimo Administrador)
2. Obtener usuario objetivo desde MongoDB (validación de existencia)
3. Conectar a EDARSAHUB SQL
4. Resolver UsuarioID interno desde PublicUUID
5. Para cada tipo de permiso (servers, sucursales, warehouses):
   a. UPDATE ... SET Activo=0 WHERE UsuarioID=? AND Activo=1
   b. INSERT INTO ... VALUES (UsuarioID, ID_recurso, 1, GETDATE(), 'RBAC-SCOPE-E')
6. conn.commit()
7. conn.close()
8. Retornar éxito
```

### Manejo de errores:
- Si falla cualquier operación SQL: `conn` se cierra sin commit (rollback implícito)
- Se lanza HTTPException 500 con detalle del error

---

## 5. Tablas SQL Escritas

| Tabla | Operaciones |
|-------|-------------|
| `Usuario_ServidoresAsignacion` | UPDATE (Activo=0) + INSERT |
| `Usuario_SucursalesAsignacion` | UPDATE (Activo=0) + INSERT |
| `Usuario_AlmacenesAsignacion` | UPDATE (Activo=0) + INSERT |

### Estrategia de idempotencia:
- Antes de insertar nuevas asignaciones, se desactivan todas las anteriores (`Activo=0`)
- Las nuevas asignaciones se insertan con `Activo=1`
- Esto garantiza que no hay duplicados activos

---

## 6. Payload Probado

### Prueba 1: Mantener permisos existentes
```json
PUT /api/users/A5E56ED0-89B2-4D50-92F4-568A2106AB50/permissions
{
  "allowed_servers": ["6d053c22-523e-48c0-b72b-96081e2d781b"],
  "allowed_sucursales": {},
  "allowed_warehouses": {"6d053c22-523e-48c0-b72b-96081e2d781b": ["003", "004"]}
}
```
**Resultado:** HTTP 200, `{"message": "Permisos actualizados"}`

### Prueba 2: Añadir almacén
```json
{
  "allowed_warehouses": {"6d053c22-523e-48c0-b72b-96081e2d781b": ["003", "004", "005"]}
}
```
**Resultado:** HTTP 200, almacén 005 visible en SQL y API

### Prueba 3: Revertir a estado original
```json
{
  "allowed_warehouses": {"6d053c22-523e-48c0-b72b-96081e2d781b": ["003", "004"]}
}
```
**Resultado:** HTTP 200, almacén 005 desactivado en SQL

---

## 7. Evidencia de que MongoDB NO fue Modificado

Consulta directa a MongoDB tras operaciones de escritura:

```
MongoDB: carlosruz@edarsa.com.mx
allowed_servers: ['6d053c22-523e-48c0-b72b-96081e2d781b']
allowed_sucursales: {}
allowed_warehouses: {'6d053c22-523e-48c0-b72b-96081e2d781b': ['003', '004']}
```

Los valores en MongoDB son los **legacy migrados**, no reflejan las operaciones de RBAC-SCOPE-E.
La lectura viene de SQL (RBAC-SCOPE-D), la escritura va a SQL (RBAC-SCOPE-E).

---

## 8. Validación de Persistencia desde SQL

### Query de verificación:
```sql
SELECT AlmacenCodigo, Activo, FechaCreacion
FROM Usuario_AlmacenesAsignacion 
WHERE UsuarioID = 3 AND Activo = 1
ORDER BY AlmacenCodigo
```

### Resultados post-escritura:
| AlmacenCodigo | Activo | FechaCreacion |
|---------------|--------|---------------|
| 003 | 1 | 2026-05-13 22:03:37 |
| 004 | 1 | 2026-05-13 22:03:37 |

**Conclusión:** Los datos persisten correctamente en SQL y se leen desde SQL.

---

## 9. Validación de No Regresión

| Validación | Resultado |
|------------|-----------|
| GET /api/users devuelve 11 usuarios | ✅ |
| carlosruz@edarsa.com.mx: 1 servidor, 2 almacenes | ✅ |
| noxte@alpyc.com: 1 servidor, 2 sucursales, 5 almacenes | ✅ |
| auditoria@edarsa.com.mx: 3 servidores, 2 sucursales, 20 almacenes | ✅ |
| admin@inventario.com: 8 servidores | ✅ |
| Usuarios sin permisos tienen arrays vacíos | ✅ |
| No hay duplicados activos en las 3 tablas | ✅ |
| Login funciona | ✅ |
| JWT no cambió | ✅ |
| /api/servers devuelve 8 servidores | ✅ |

---

## 10. Riesgos Residuales

| Riesgo | Mitigación |
|--------|------------|
| MongoDB contiene datos legacy que no se sincronizan | Aceptable: MongoDB será deprecado en fases posteriores |
| El código SQL está inline en service.py | Refactorizar en RBAC-SCOPE-G cuando se elimine MongoDB |
| No hay auditoría del current_user que modificó | Campo `ModificadoPor` existe pero no se pobla (TODO) |

---

## 11. Recomendación para RBAC-SCOPE-F

**RBAC-SCOPE-F debe validar:**
1. Modal de permisos en frontend guarda correctamente vía PUT
2. Modal recarga permisos desde GET (ya SQL)
3. Flujo e2e completo: abrir modal → modificar → guardar → recargar → verificar persistencia
4. No hay errores de UI ni consola

**Pre-requisitos:**
- RBAC-SCOPE-E completada ✅
- No hay cambios de frontend requeridos (el endpoint mantiene contrato)

---

## Resumen Ejecutivo

| Aspecto | Estado |
|---------|--------|
| `update_user_permissions_sql()` existe y funciona | ✅ Implementado inline en service.py |
| PUT /api/users/{id}/permissions escribe en SQL | ✅ Validado |
| MongoDB no recibe permisos operativos | ✅ Confirmado |
| No hay duplicados activos | ✅ Verificado |
| Auth SQL-first sigue funcionando | ✅ Login OK |
| Reporte generado | ✅ Este documento |

**FASE RBAC-SCOPE-E: COMPLETADA**

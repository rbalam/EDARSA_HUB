# DIAGNÓSTICO PASIVO — RBAC-DUPKEY-001
## DuplicateKeyError en índice rbac_usuarios_roles

**Fecha:** 14-Mayo-2026  
**Estado:** DIAGNÓSTICO COMPLETADO  
**Tipo:** Incidencia de infraestructura MongoDB  
**Prioridad:** MEDIA (no bloquea login ni permisos principales)  

---

## 1. Error Observado

```
pymongo.errors.DuplicateKeyError
collection: edarsa_hub.rbac_usuarios_roles
index: user_id_1_rol_id_1_sucursal_id_1
dup key: {
  user_id: "0da77b7b-fe88-4e23-98bc-9cbf543d5ee3",
  rol_id: "757bddd6-c631-4ddc-bd8f-0feb803c420f",
  sucursal_id: null
}
```

---

## 2. Archivo donde se crea el índice

**Archivo:** `/app/backend/core/rbac/repository.py`  
**Línea:** 42  
**Código:**
```python
self.db.rbac_usuarios_roles.create_index(
    [("user_id", 1), ("rol_id", 1), ("sucursal_id", 1)], 
    unique=True
)
```

---

## 3. Momento de Ejecución

| Evento | Archivo | Línea |
|--------|---------|-------|
| **Startup de backend** | `server.py` | 16025-16026 |
| Instanciación | `RBACService(db)` | service.py:50 |
| Llamada | `rbac_service.ensure_initialized()` | server.py:16026 |
| Índices | `self._ensure_indexes()` | repository.py:26 |

**Secuencia:**
1. Backend inicia → `server.py`
2. Se instancia `RBACService(db)` → línea 16025
3. `__init__` llama a `self.repo = RBACRepository(db)` → service.py:50
4. `RBACRepository.__init__` llama a `self._ensure_indexes()` → repository.py:26
5. `_ensure_indexes()` intenta crear el índice único → **FALLA CON DUPLICADOS**

---

## 4. Conteo de Duplicados

| Métrica | Valor |
|---------|-------|
| **Total documentos** | 72 |
| **Grupos duplicados** | 14 |
| **Duplicados por grupo** | 5 (consistente) |
| **Timestamp único** | `2026-04-19 04:52:16.957000` |

---

## 5. Causa Raíz Identificada

### 5.1 Esquema Real vs Índice Esperado

**Índice que el código intenta crear:**
```
(user_id, rol_id, sucursal_id) UNIQUE
```

**Índice que realmente existe en producción:**
```
(user_id, empresa_id) UNIQUE
```

### 5.2 Estructura Real de los Documentos

```json
{
  "id": "uuid",
  "user_id": "0da77b7b-fe88-4e23-98bc-9cbf543d5ee3",
  "rol_id": "757bddd6-c631-4ddc-bd8f-0feb803c420f",
  "empresa_id": "31784356-6d0b-47ce-8fe8-c8a442e45a07",  // ← DIFERENTE POR DOCUMENTO
  "sucursales_ids": [],  // ← ARRAY, no string
  "sucursal_id": null,   // ← NO EXISTE en datos reales
  "activo": true,
  "created_at": "2026-04-19 04:52:16.957000",
  "created_by": "fase2_migration"
}
```

### 5.3 Origen de los Datos

- **Creador:** `fase2_migration` (script de migración FASE 2)
- **Timestamp:** Todos con el mismo timestamp exacto = inserción batch
- **Intención:** Asignar rol a usuario POR EMPRESA (multitenancy)

### 5.4 Discrepancia de Diseño

| Aspecto | Código `repository.py` | Datos Reales |
|---------|------------------------|--------------|
| Campo de sucursal | `sucursal_id` (string) | `sucursales_ids` (array) |
| Índice único | `(user_id, rol_id, sucursal_id)` | `(user_id, empresa_id)` |
| Modelo conceptual | Rol por sucursal | Rol por empresa |

---

## 6. Impacto Real

| Área | Impacto |
|------|---------|
| **Login** | ✅ No afectado (el error es warning async) |
| **Permisos** | ✅ No afectado (SuperAdministrador tiene bypass) |
| **Visibilidad menús** | ✅ No afectado |
| **RBAC nuevo** | ⚠️ Parcial - el índice no se crea |
| **Startup** | ⚠️ Warning en logs pero no fatal |
| **Funcionalidad** | ✅ Sistema operativo |

---

## 7. Índices Actuales en Producción

```
_id_:           {_id: 1}           UNIQUE (automático)
user_id_1:      {user_id: 1}       NO UNIQUE
rol_id_1:       {rol_id: 1}        NO UNIQUE
user_id_1_empresa_id_1: {user_id: 1, empresa_id: 1} UNIQUE
```

**Nota:** El índice `user_id_1_rol_id_1_sucursal_id_1` **NO existe** porque falla al crearse.

---

## 8. Usuarios Afectados

| User ID | Email | Rol Legacy | Rol RBAC |
|---------|-------|------------|----------|
| 0da77b7b-... | admin@inventario.com | SuperAdministrador | ADMIN |

**Roles RBAC involucrados:**
- `757bddd6-...` = ADMIN (Administrador)
- `da992126-...` = OPERADOR
- `5bbe0356-...` = SUPERVISOR

---

## 9. Propuesta de Corrección

### Opción A: Corregir el índice según el modelo real (RECOMENDADA)

El modelo real es **rol por empresa**, no **rol por sucursal**.

**Corrección en `repository.py` línea 42:**
```python
# ANTES (incorrecto):
self.db.rbac_usuarios_roles.create_index(
    [("user_id", 1), ("rol_id", 1), ("sucursal_id", 1)], 
    unique=True
)

# DESPUÉS (correcto según datos reales):
self.db.rbac_usuarios_roles.create_index(
    [("user_id", 1), ("rol_id", 1), ("empresa_id", 1)], 
    unique=True
)
```

**Nota:** Este índice es compatible con los datos existentes. No requiere eliminar duplicados.

### Opción B: Limpiar duplicados y crear índice original

Si se desea mantener el modelo `(user_id, rol_id, sucursal_id)`:

1. Eliminar el campo `empresa_id` o consolidarlo
2. Eliminar 4 de cada 5 duplicados (conservar uno por grupo)
3. Crear el índice único

**Script de backup propuesto (NO EJECUTAR):**
```javascript
// SOLO BACKUP - NO EJECUTAR SIN AUTORIZACIÓN
db.rbac_usuarios_roles.aggregate([
  {$match: {}},
  {$out: "rbac_usuarios_roles_backup_20260514"}
])
```

**Script de limpieza propuesto (NO EJECUTAR):**
```javascript
// SOLO PROPUESTA - NO EJECUTAR SIN AUTORIZACIÓN
db.rbac_usuarios_roles.aggregate([
  {$group: {
    _id: {user_id: "$user_id", rol_id: "$rol_id", sucursal_id: "$sucursal_id"},
    docs: {$push: "$_id"},
    count: {$sum: 1}
  }},
  {$match: {count: {$gt: 1}}}
]).forEach(function(group) {
  // Conservar el primero, eliminar el resto
  var toDelete = group.docs.slice(1);
  db.rbac_usuarios_roles.deleteMany({_id: {$in: toDelete}});
});
```

---

## 10. Confirmación de No Modificación

- ✅ **NO se modificó** ningún archivo
- ✅ **NO se modificó** MongoDB
- ✅ **NO se modificó** EDARSAHUB SQL
- ✅ **NO se ejecutó** ningún script de corrección
- ✅ Diagnóstico 100% pasivo (solo lectura)

---

## 11. Recomendación

**OPCIÓN A es la recomendada** porque:

1. No requiere eliminar datos
2. Es compatible con el modelo de multitenancy por empresa
3. El índice `(user_id, empresa_id)` ya existe y funciona
4. Solo requiere cambiar 1 línea de código en `repository.py`

**Próximos pasos pendientes de autorización:**
1. Modificar línea 42 de `repository.py`
2. Reiniciar backend
3. Verificar que el warning desaparece

---

## 12. Archivos de Referencia

- `/app/backend/core/rbac/repository.py` (línea 42)
- `/app/backend/core/rbac/service.py` (líneas 50, 71-82)
- `/app/backend/server.py` (líneas 16025-16026)

---

**Reporte generado:** 14-Mayo-2026  
**Autor:** Agente E1 (Diagnóstico Pasivo)  
**Pendiente:** Autorización para implementar corrección

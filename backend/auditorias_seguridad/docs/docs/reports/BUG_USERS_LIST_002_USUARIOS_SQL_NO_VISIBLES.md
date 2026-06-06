# BUG-USERS-LIST-002: Usuarios SQL No Visibles en Listado

**Fecha:** 14 de Diciembre de 2025  
**Estado:** ✅ RESUELTO  
**Prioridad:** P0 (Crítico)  
**Régimen:** Autorización Controlada

---

## 1. Causa Raíz

El modelo Pydantic `User` en `/app/backend/modules/auth/schemas.py` **no incluía los campos**:
- `empresas_permitidas`
- `empresa_default_id`

Al usar `response_model=List[User]` en el endpoint `GET /api/users`, Pydantic eliminaba estos campos de la respuesta porque el modelo tenía `extra="ignore"`.

**Resultado:** Usuarios como carlos@alpuntoycoma.mx y eduardo@alpuntoycoma.mx aparecían en el listado pero mostraban `empresas_permitidas: []` aunque tenían 5 empresas asignadas en EDARSAHUB SQL.

**NOTA IMPORTANTE:** Los usuarios SÍ aparecían en el listado (11 usuarios). El problema era que sus campos `empresas_permitidas` y `empresa_default_id` no se serializaban en la respuesta JSON.

---

## 2. Endpoint Afectado

| Endpoint | Método | Archivo | Response Model |
|----------|--------|---------|----------------|
| `/api/users` | GET | `routes.py:597` | `List[User]` |

---

## 3. Query/Función Afectada

| Archivo | Función | Estado |
|---------|---------|--------|
| `/app/backend/modules/auth/schemas.py` | `class User(BaseModel)` | **CORREGIDO** |
| `/app/backend/modules/auth/repository.py` | `get_all_users()` | OK (ya devolvía empresas) |
| `/app/backend/core/auth/user_repository_sql.py` | `list_all_users_sql()` | OK (ya devolvía empresas) |

---

## 4. Confirmación de Existencia en SQL

### carlos@alpuntoycoma.mx

| Tabla | Verificación | Resultado |
|-------|--------------|-----------|
| Usuario_Catalogo | UsuarioID | 10 |
| Usuario_Catalogo | Activo | ✅ TRUE |
| Usuario_Catalogo | PublicUUID | 9DD2A053-4473-454A-B871-B257361F4701 |
| Usuario_RolesAsignacion | Rol | Administrador |
| Usuario_EmpresasAsignacion | Empresas | 5 |
| Usuario_ServidoresAsignacion | Servidores | 0 (sin granulares) |

### eduardo@alpuntoycoma.mx

| Tabla | Verificación | Resultado |
|-------|--------------|-----------|
| Usuario_Catalogo | UsuarioID | 11 |
| Usuario_Catalogo | Activo | ✅ TRUE |
| Usuario_Catalogo | PublicUUID | 9F422D46-3F09-4A5D-AAC6-3D1F81DC1CF0 |
| Usuario_RolesAsignacion | Rol | Administrador |
| Usuario_EmpresasAsignacion | Empresas | 5 |
| Usuario_ServidoresAsignacion | Servidores | 0 (sin granulares) |

---

## 5. Motivo por el que No Aparecían Correctamente

| Capa | Comportamiento |
|------|----------------|
| `list_all_users_sql()` | ✅ Devolvía `empresas_permitidas: [5 UUIDs]` |
| `get_all_users()` | ✅ Devolvía `empresas_permitidas: [5 UUIDs]` |
| `service.get_users()` | ✅ Devolvía `empresas_permitidas: [5 UUIDs]` |
| `response_model=List[User]` | ❌ Eliminaba `empresas_permitidas` (campo no definido en modelo) |
| **Respuesta JSON final** | ❌ `empresas_permitidas: []` (default del modelo) |

---

## 6. Corrección Aplicada

**Archivo:** `/app/backend/modules/auth/schemas.py`

```python
class User(BaseModel):
    """Modelo de usuario completo"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(...)
    email: EmailStr
    name: str
    role: str
    telefono: Optional[str] = None
    sucursales: List[str] = []
    allowed_servers: List[str] = []
    allowed_sucursales: Dict[str, List[str]] = {}
    allowed_warehouses: Dict[str, List[str]] = {}
    # BUG-USERS-LIST-002: Campos de empresas asignadas desde EDARSAHUB SQL
    empresas_permitidas: List[str] = []  # UUIDs de empresas asignadas
    empresa_default_id: Optional[str] = None  # UUID de empresa principal
    created_at: datetime = Field(...)
    active: bool = True
    # ... campos RBAC ...
```

---

## 7. Respuesta Antes/Después

### ANTES

```json
{
  "email": "carlos@alpuntoycoma.mx",
  "name": "Carlos Alberto Aguirre de Leon",
  "role": "Administrador",
  "allowed_servers": [],
  "allowed_sucursales": {},
  "allowed_warehouses": {},
  "active": true
  // empresas_permitidas NO aparecía en la respuesta
}
```

### DESPUÉS

```json
{
  "email": "carlos@alpuntoycoma.mx",
  "name": "Carlos Alberto Aguirre de Leon",
  "role": "Administrador",
  "allowed_servers": [],
  "allowed_sucursales": {},
  "allowed_warehouses": {},
  "empresas_permitidas": [
    "31784356-6d0b-47ce-8fe8-c8a442e45a07",
    "a4d8b5e7-de51-4ba4-9d2c-0e1996ac82ff",
    "1118f83c-fd45-4681-8006-5e92dd6d01c1",
    "c6e8e7e8-1d1c-42fd-875e-0a3c90f0e79a",
    "e3bac4e5-98cb-456d-b0be-8b4e7a5c16c1"
  ],
  "empresa_default_id": "31784356-6d0b-47ce-8fe8-c8a442e45a07",
  "active": true
}
```

---

## 8. Validación de No Regresión

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Total usuarios = 11 | ✅ OK |
| 2 | carlos@alpuntoycoma.mx presente | ✅ OK (5 empresas) |
| 3 | eduardo@alpuntoycoma.mx presente | ✅ OK (5 empresas) |
| 4 | admin@inventario.com presente | ✅ OK (5 empresas) |
| 5 | ricardo@edarsa.com.mx presente | ✅ OK |
| 6 | Carlos Ruz mantiene permisos | ✅ OK (1 servidor, 2 almacenes) |
| 7 | No usuarios @test.com activos | ✅ OK |
| 8 | Login funciona | ✅ OK |
| 9 | JWT válido | ✅ OK |
| 10 | GET /api/servers = 8 | ✅ OK |
| 11 | PUT /api/users/{id}/permissions | ✅ HTTP 200 |

---

## 9. Confirmación EDARSAHUB SQL como Fuente

| Componente | Fuente | Confirmación |
|------------|--------|--------------|
| Lista base de usuarios | EDARSAHUB SQL (Usuario_Catalogo) | ✅ |
| Roles de usuarios | EDARSAHUB SQL (Usuario_RolesAsignacion) | ✅ |
| Empresas asignadas | EDARSAHUB SQL (Usuario_EmpresasAsignacion) | ✅ |
| Empresa default | EDARSAHUB SQL | ✅ |
| Permisos granulares (allowed_*) | MongoDB (hotfix temporal) | ⚠️ Pendiente RBAC-SCOPE-D |

---

## 10. Riesgos Residuales

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Frontend puede no mostrar `empresas_permitidas` si no lo usa | **Baja** | Frontend ya manejaba el campo, ahora lo recibe |
| Otros modelos Pydantic pueden tener campos faltantes | **Baja** | Revisar otros response_model en endpoints críticos |

---

## Conclusión

**BUG-USERS-LIST-002 RESUELTO.**

El modelo Pydantic `User` ahora incluye los campos `empresas_permitidas` y `empresa_default_id`, permitiendo que la respuesta JSON del endpoint `/api/users` serialice correctamente estos datos desde EDARSAHUB SQL.

**Usuarios afectados ahora visibles correctamente:**
- ✅ carlos@alpuntoycoma.mx (5 empresas)
- ✅ eduardo@alpuntoycoma.mx (5 empresas)
- ✅ admin@inventario.com (5 empresas)
- ✅ Todos los demás usuarios con empresas asignadas

---

**Validado por:** Agente E1  
**Fecha validación:** 14 de Diciembre de 2025

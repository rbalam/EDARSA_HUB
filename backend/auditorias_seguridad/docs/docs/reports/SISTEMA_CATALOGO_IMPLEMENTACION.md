# Implementación: Sistema_Catalogo - Tipos de Sistema Dinámicos

**Fecha:** 14-Mayo-2026  
**Autor:** E1 Agent  
**Estado:** COMPLETADO

---

## Resumen Ejecutivo

Se implementó un catálogo dinámico para administrar los tipos de sistema que aparecen en el combo "Tipo de Sistema" del modal de servidores. Ahora los tipos se cargan desde EDARSAHUB SQL en lugar de estar hardcodeados, permitiendo crear/solicitar nuevos tipos desde el mismo combo.

---

## 1. Tabla SQL Creada

### Nombre: `Sistema_Catalogo`

```sql
CREATE TABLE Sistema_Catalogo (
    SistemaID INT IDENTITY(1,1) PRIMARY KEY,
    Codigo NVARCHAR(50) NOT NULL UNIQUE,
    Descripcion NVARCHAR(100) NOT NULL,
    Activo BIT NOT NULL DEFAULT 1,
    Estado NVARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    SolicitadoPorUsuarioID INT NULL,
    AutorizadoPorUsuarioID INT NULL,
    SolicitadoPorEmail NVARCHAR(200) NULL,
    AutorizadoPorEmail NVARCHAR(200) NULL,
    FechaSolicitud DATETIME2 NULL,
    FechaAutorizacion DATETIME2 NULL,
    FechaCreacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    FechaActualizacion DATETIME2 NULL
);
```

### Estados Permitidos:
- `PENDIENTE` - Solicitud esperando autorización
- `ACTIVO` - Sistema disponible en combo
- `INACTIVO` - Sistema deshabilitado
- `RECHAZADO` - Solicitud rechazada

### Datos Base Insertados:
| SistemaID | Codigo | Descripcion | Estado |
|-----------|--------|-------------|--------|
| 1 | MPRO | ManagementPro (MPRO) | ACTIVO |
| 2 | SOFTRESTAURANT | SoftRestaurant | ACTIVO |
| 3 | OTRO | Otro | ACTIVO |

---

## 2. Endpoints Backend Creados

### Archivo: `/app/backend/modules/catalogos/routes.py`

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/catalogos/sistemas` | Lista todos los sistemas | Cualquier usuario autenticado |
| GET | `/api/catalogos/sistemas/activos` | Lista sistemas activos para combo | Cualquier usuario autenticado |
| POST | `/api/catalogos/sistemas/solicitar` | Solicita nuevo sistema (PENDIENTE) | CATALOGOS_SISTEMAS_SOLICITAR |
| POST | `/api/catalogos/sistemas` | Crea sistema directamente (ACTIVO) | CATALOGOS_SISTEMAS_CREAR |
| PUT | `/api/catalogos/sistemas/{id}` | Edita descripción | CATALOGOS_SISTEMAS_EDITAR |
| PATCH | `/api/catalogos/sistemas/{id}/toggle-activo` | Activa/Inactiva | CATALOGOS_SISTEMAS_ACTIVAR_INACTIVAR |
| PATCH | `/api/catalogos/sistemas/{id}/autorizar` | Autoriza solicitud pendiente | CATALOGOS_SISTEMAS_AUTORIZAR |
| PATCH | `/api/catalogos/sistemas/{id}/rechazar` | Rechaza solicitud pendiente | CATALOGOS_SISTEMAS_AUTORIZAR |

---

## 3. Permisos Implementados

| Permiso | Descripción |
|---------|-------------|
| `CATALOGOS_SISTEMAS_SOLICITAR` | Puede solicitar nuevos sistemas |
| `CATALOGOS_SISTEMAS_CREAR` | Puede crear sistemas directamente |
| `CATALOGOS_SISTEMAS_AUTORIZAR` | Puede aprobar/rechazar solicitudes |
| `CATALOGOS_SISTEMAS_EDITAR` | Puede editar descripciones |
| `CATALOGOS_SISTEMAS_ACTIVAR_INACTIVAR` | Puede activar/inactivar sistemas |

### Lógica de Permisos por Rol:
- **Administrador/SuperAdministrador**: Todos los permisos
- **Supervisor**: Solicitar, Crear, Editar
- **Otros roles**: Solo solicitar (si tienen el permiso específico)

---

## 4. Archivos Modificados

### Backend:
- `/app/backend/modules/catalogos/routes.py` - Endpoints de sistemas
- `/app/backend/modules/catalogos/schemas.py` - Estructura de tabla y dominio

### Frontend:
- `/app/frontend/src/pages/Servidores.js` - Combo dinámico con opción "+ Nuevo"
- `/app/frontend/src/pages/Catalogos.js` - Icono de dominio Configuración

---

## 5. Flujo de Usuario

### Crear Nuevo Sistema (con permiso CREAR):
1. Usuario abre modal "Agregar Nuevo Servidor"
2. En combo "Tipo de Sistema" ve opción "+ Nuevo tipo de sistema"
3. Click en "+ Nuevo tipo de sistema"
4. Abre modal secundario con campo "Nombre/Descripción"
5. Ingresa nombre (ej: "SAP Business One")
6. Click "Crear Sistema"
7. Sistema se crea ACTIVO inmediatamente
8. Modal se cierra
9. Combo se actualiza mostrando el nuevo sistema

### Solicitar Nuevo Sistema (solo permiso SOLICITAR):
1. Usuario abre modal "Agregar Nuevo Servidor"
2. En combo "Tipo de Sistema" ve opción "+ Nuevo tipo de sistema"
3. Click en "+ Nuevo tipo de sistema"
4. Ve mensaje: "Su solicitud será enviada para autorización"
5. Ingresa nombre
6. Click "Solicitar"
7. Sistema se crea con Estado = 'PENDIENTE'
8. Toast: "Solicitud enviada para autorización"
9. Sistema NO aparece en combo hasta autorización

### Autorizar Sistema (desde Catálogos):
1. Administrador va a Catálogos > Configuración > Sistemas
2. Ve sistemas pendientes primero
3. Click "Autorizar" en sistema pendiente
4. Sistema pasa a Estado = 'ACTIVO'
5. Sistema aparece en combo de Servidores

---

## 6. Validaciones

| # | Validación | Resultado |
|---|------------|-----------|
| 1 | Catálogos > Configuración > Sistemas visible | ✅ |
| 2 | Muestra ManagementPro, SoftRestaurant, Otro | ✅ |
| 3 | Crear sistema nuevo desde combo | ✅ |
| 4 | Sistema nuevo aparece en combo inmediatamente | ✅ |
| 5 | Editar descripción | ✅ (Backend listo) |
| 6 | Inactivar sistema | ✅ (Backend listo) |
| 7 | Sistema inactivo no aparece en combo | ✅ |
| 8 | Servidores existentes funcionan | ✅ |
| 9 | Comercial NO tocado | ✅ |
| 10 | Finanzas NO tocado | ✅ |
| 11 | Compras NO tocado | ✅ |
| 12 | Inventarios NO tocado | ✅ |
| 13 | Operaciones NO tocado | ✅ |
| 14 | Tablero Ejecutivo NO tocado | ✅ |
| 15 | MongoDB NO participa | ✅ |

---

## 7. Evidencia de Prueba

### Sistema Creado Dinámicamente:
```
SistemaID: 4
Codigo: SAP_BUSINESS_ONE
Descripcion: SAP Business One
Estado: ACTIVO
Activo: True
```

### Endpoint de Activos (con permisos):
```json
{
  "success": true,
  "data": [
    {"SistemaID": 1, "Codigo": "MPRO", "Descripcion": "ManagementPro (MPRO)"},
    {"SistemaID": 3, "Codigo": "OTRO", "Descripcion": "Otro"},
    {"SistemaID": 4, "Codigo": "SAP_BUSINESS_ONE", "Descripcion": "SAP Business One"},
    {"SistemaID": 2, "Codigo": "SOFTRESTAURANT", "Descripcion": "SoftRestaurant"}
  ],
  "permisos": {
    "puede_crear": true,
    "puede_solicitar": true,
    "mostrar_nuevo": true
  }
}
```

---

## 8. Confirmaciones

- ✅ EDARSAHUB SQL es la única fuente de datos
- ✅ MongoDB NO participa
- ✅ No se usan listas hardcodeadas para tipos de sistema
- ✅ No se modificó lógica interna de conexión
- ✅ Servidores existentes funcionan igual
- ✅ No se tocaron otros módulos

---

## 9. Próximos Pasos (Opcional)

1. Implementar pantalla completa de administración en Catálogos > Sistemas
2. Agregar filtros por estado (Pendientes, Activos, Inactivos, Rechazados)
3. Implementar notificaciones cuando hay solicitudes pendientes

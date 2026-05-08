# EDARSA HUB - Documento de Diseño Técnico-Funcional
# Módulo Maestro de Catálogos del Sistema

## 1. Objetivo

Implementar un módulo centralizado para la gestión de catálogos del sistema EDARSA HUB, con arquitectura reutilizable que permita:
- **Acceso central** desde el menú "Catálogos"
- **Acceso contextual** desde módulos nativos (RH, Compras, Finanzas, etc.)
- **Sin duplicidad** de catálogos entre módulos

---

## 2. Arquitectura Funcional

### 2.1 Organización por Dominios

| Dominio | Descripción | Catálogos |
|---------|-------------|-----------|
| **Generales** | Catálogos globales compartidos | Empresas, Sucursales, Departamentos, Puestos, Bancos, Monedas, Unidades de Medida, Centros de Costo |
| **RH** | Recursos Humanos | Tipos de Contrato, Tipos de Ausencia, Motivos de Baja, Jornadas, Turnos, Áreas, Beneficios, Régimen Contratación |
| **Nómina** | Catálogos de nómina | Conceptos de Nómina, Tipos de Concepto, Tipos de Período, Estatus de Período |
| **Compras** | Compras y Proveedores | Estatus de Compras/Órdenes/Pedidos/Recepciones, Tipos de Proveedor/Contacto/Documento |
| **Inventarios** | Inventarios y Productos | Tipos de Movimiento, Familias, Subfamilias, Líneas, Marcas |
| **Activos Fijos** | Activos de la empresa | Tipos de Activo/Baja/Ubicación/Medidor/OT, Estatus de Activo/OT |
| **Finanzas** | Catálogos financieros | Cuentas Bancarias, Formas de Pago SAT, Métodos de Pago SAT, Usos CFDI, Regímenes Fiscales |
| **Ventas** | Catálogos de ventas | Estatus de Venta/Pedidos/Cotizaciones |
| **Seguridad** | Usuarios y permisos | Roles, Módulos, Tipos de Autorización |
| **Homologación** | Mapeo entre sistemas | Equivalencias |

### 2.2 Mapa de Navegación

```
EDARSA HUB
├── [Menú Principal]
│   ├── Catálogos (Nuevo) ────────────────┐
│   │   ├── Panel Dominios               │
│   │   │   ├── Generales               │
│   │   │   ├── RH                       │
│   │   │   ├── Nómina                   │
│   │   │   ├── Compras                  │
│   │   │   ├── Inventarios             │
│   │   │   ├── Activos Fijos           │
│   │   │   ├── Finanzas                │
│   │   │   ├── Ventas                   │
│   │   │   ├── Seguridad               │
│   │   │   └── Homologación            │
│   │   └── Vista de Registros          │
│   │       ├── Listado                 │
│   │       ├── Crear/Editar            │
│   │       ├── Activar/Desactivar      │
│   │       └── Buscar/Filtrar          │
│   │                                    │
│   ├── Recursos Humanos ────────────────┤ (Acceso contextual → Catálogos RH)
│   ├── Compras ─────────────────────────┤ (Acceso contextual → Catálogos Compras)
│   ├── Finanzas ────────────────────────┤ (Acceso contextual → Catálogos Finanzas)
│   └── ...                              │
└───────────────────────────────────────-┘
```

---

## 3. Arquitectura Técnica

### 3.1 Estructura Backend

```
/app/backend/modules/catalogos/
├── __init__.py          # Inicialización del módulo
├── schemas.py           # Modelos Pydantic y configuración de dominios/tablas
├── repository.py        # Acceso a datos SQL Server
├── service.py           # Lógica de negocio
└── routes.py            # Endpoints FastAPI
```

### 3.2 Endpoints API

| Método | Ruta | Descripción | Rol Requerido |
|--------|------|-------------|---------------|
| GET | `/api/catalogos/dominios` | Lista dominios con conteos | Usuario |
| GET | `/api/catalogos/tabla/{tabla}` | Lista registros de un catálogo | Usuario |
| GET | `/api/catalogos/tabla/{tabla}/{id}` | Obtiene registro específico | Usuario |
| POST | `/api/catalogos/tabla/{tabla}` | Crea nuevo registro | Admin/Supervisor |
| PUT | `/api/catalogos/tabla/{tabla}/{id}` | Actualiza registro | Admin/Supervisor |
| PUT | `/api/catalogos/tabla/{tabla}/{id}/desactivar` | Desactiva registro | Admin |
| PUT | `/api/catalogos/tabla/{tabla}/{id}/activar` | Reactiva registro | Admin |
| GET | `/api/catalogos/estructura/{tabla}` | Obtiene estructura de tabla | Usuario |
| POST | `/api/catalogos/admin/crear-tablas` | Ejecuta DDL tablas nuevas | Admin |
| GET | `/api/catalogos/admin/verificar-tablas` | Verifica estado tablas | Usuario |

### 3.3 Estructura Frontend

```
/app/frontend/src/pages/
├── Catalogos.js         # Página principal del módulo
└── ...

/app/frontend/src/App.js # Ruta /catalogos agregada
/app/frontend/src/pages/Layout.js # Menú "Catálogos" agregado
```

---

## 4. Modelo de Datos

### 4.1 Catálogos Existentes (Reutilizados)

| Tabla | Registros | Estado |
|-------|-----------|--------|
| RH_Cat_Sucursales | 8 | ✅ Activo |
| RH_Cat_Departamentos | 11 | ✅ Activo |
| RH_Cat_Puestos | 37 | ✅ Activo |
| RH_Cat_TiposContrato | 3 | ✅ Activo |
| RH_Cat_MotivosBaja | 3 | ✅ Activo |
| RH_Cat_TiposAusencia | 5 | ✅ Activo |
| RH_Cat_ConceptosNomina | 10 | ✅ Activo |
| Usuario_Roles | 5 | ✅ Activo |
| Usuario_Modulos | 8 | ✅ Activo |
| ... (ver diagnóstico completo) | | |

### 4.2 Catálogos Nuevos (DDL Incluido)

```sql
-- Tablas creadas por el módulo:
- Global_Cat_Empresas
- Global_Cat_Bancos
- Global_Cat_UnidadesMedida
- Global_Cat_CentrosCosto
- Global_Cat_FormaPagoSAT
- Global_Cat_MetodoPagoSAT
- Global_Cat_UsoCFDI
- Global_Cat_RegimenFiscal
- Finanzas_Cat_CuentasBancarias
```

### 4.3 Estructura Base Común

Todos los catálogos siguen un patrón estándar:

```sql
- [Entidad]ID      INT IDENTITY PRIMARY KEY
- Codigo[Entidad]  VARCHAR UNIQUE (opcional)
- Nombre/Descripcion VARCHAR NOT NULL
- Activo           BIT DEFAULT 1
- FechaAlta        DATETIME2 DEFAULT GETDATE()
- FechaModificacion DATETIME2 NULL
```

---

## 5. Reglas de Gobierno

### 5.1 Permisos por Rol

| Acción | Usuario | Supervisor | Administrador |
|--------|---------|------------|---------------|
| Ver catálogos | ✅ | ✅ | ✅ |
| Crear registros | ❌ | ✅ | ✅ |
| Editar registros | ❌ | ✅ | ✅ |
| Desactivar registros | ❌ | ❌ | ✅ |
| Activar registros | ❌ | ❌ | ✅ |
| Crear tablas (DDL) | ❌ | ❌ | ✅ |

### 5.2 Reglas de Negocio

1. **No duplicidad**: Un catálogo existe una sola vez
2. **Soft delete**: Los registros se desactivan, no se eliminan
3. **Trazabilidad**: Campos FechaAlta y FechaModificacion
4. **Validación**: Solo campos editables pueden modificarse

---

## 6. Implementación Realizada

### 6.1 Archivos Creados

| Archivo | Descripción |
|---------|-------------|
| `/app/backend/modules/catalogos/__init__.py` | Inicialización del módulo |
| `/app/backend/modules/catalogos/schemas.py` | Configuración de dominios y tablas |
| `/app/backend/modules/catalogos/repository.py` | Acceso a datos con DDL incluido |
| `/app/backend/modules/catalogos/service.py` | Lógica de negocio |
| `/app/backend/modules/catalogos/routes.py` | Endpoints REST |
| `/app/frontend/src/pages/Catalogos.js` | Página principal del módulo |

### 6.2 Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `/app/backend/server.py` | Registro del router de catálogos |
| `/app/frontend/src/App.js` | Ruta /catalogos agregada |
| `/app/frontend/src/pages/Layout.js` | Menú "Catálogos" agregado |

---

## 7. Acceso Contextual (Pendiente)

Para implementar acceso contextual desde módulos:

### 7.1 Desde RH → Catálogos RH
```jsx
// En RecursosHumanos.js agregar botón:
<Button onClick={() => navigate('/catalogos?dominio=rh')}>
  Catálogos RH
</Button>
```

### 7.2 Desde Compras → Catálogos Compras
```jsx
// En Compras.js agregar botón:
<Button onClick={() => navigate('/catalogos?dominio=compras')}>
  Catálogos Compras
</Button>
```

---

## 8. Próximos Pasos

1. **Ejecutar DDL** desde Administración → Crear Tablas
2. **Poblar datos iniciales** (bancos, SAT, etc.) - Ya incluidos en DDL
3. **Agregar accesos contextuales** desde módulos existentes
4. **Implementar filtro por parámetro URL** (?dominio=rh)

---

## 9. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Performance con muchos catálogos | Query optimizado con verificación batch de tablas existentes |
| Tablas inexistentes causan errores | Verificación previa de existencia antes de contar |
| Cambios accidentales en datos críticos | Solo Administradores pueden desactivar |

---

**Documento generado: Diciembre 2025**
**Módulo: Catálogos del Sistema - EDARSA HUB**

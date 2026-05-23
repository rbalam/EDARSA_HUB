# FASE 0 - DIAGNÓSTICO PASIVO TABLAJERÍA
## Reporte de Hallazgos

**Fecha**: 2026-05-23
**Módulo**: Tablajería
**Estado**: Diagnóstico Completado (Sin modificaciones)

---

## 1. ESTRUCTURA FRONTEND DE OPERACIONES

### Archivos Identificados
- `/app/frontend/src/pages/Produccion.js` - **Página placeholder "En Desarrollo"**
- `/app/frontend/src/pages/Layout.js` - Menú lateral principal
- Ruta registrada: `/produccion` en App.js

### Estado Actual
- La página `Produccion.js` muestra un banner "Módulo en Desarrollo"
- Muestra preview de funcionalidades:
  - Órdenes de Fabricación
  - Lista de Materiales (BOM)
  - Control de Tiempos
  - Mantenimiento
- **NO hay implementación real**, solo placeholder visual

### Menú Layout.js
```javascript
{ 
  name: 'Producción', 
  href: '/produccion', 
  icon: Factory, 
  roles: ['Supervisor', 'Administrador'],
  badge: 'Próx.'  // <-- Marcado como "Próximamente"
}
```

**Conclusión**: Producción es un módulo vacío, ideal para alojar Tablajería.

---

## 2. SERVIDORES DE TABLAJERÍA REGISTRADOS

| ID | Nombre | Sistema | Host | Base de Datos | Activo |
|----|--------|---------|------|---------------|--------|
| 6d859026... | **CIENFUEGOS TABLAJERIA** | SOFTRESTAURANT_PRO | servercienfuegos.ddns.net,6669\nationalsoft | Tablajeria | ✅ Sí |
| d1d8c70f... | **MPRO TABLAJERIA** | MPRO | 54.39.104.176:1433 | tablajeria_mpro | ✅ Sí |

### Servidores Relacionados (para contexto)
| Nombre | Sistema | Base de Datos | Activo |
|--------|---------|---------------|--------|
| 130° MERIDA | SOFTRESTAURANT_PRO | softrestaurant10 | ✅ |
| 130° QRO LOCAL | MPRO | QUERETARO | ✅ |
| LA ESTELAR | SOFTRESTAURANT_PRO | softrestaurant12 | ✅ |
| ORIGEN LOCAL | MPRO | ORIGEN | ✅ |

**Conclusión**: Los servidores de tablajería YA están registrados en `Servidores_Conexiones`. Se puede reutilizar la infraestructura existente.

---

## 3. TABLAS EXISTENTES EN EDARSAHUB SQL

### Tablas de Inventario (Reutilizables)
| Tabla | Propósito |
|-------|-----------|
| `Inventario_Almacenes` | Catálogo de almacenes |
| `Inventario_Existencias` | Existencias por producto/almacén |
| `Inventario_Movimientos` | Movimientos de inventario |
| `Inventario_MovimientosDetalle` | Detalle de movimientos |
| `Inventario_TipoMovimiento` | Catálogo tipos de movimiento |

### Estructura `Inventario_Almacenes`
```sql
AlmacenID: int (PK)
EmpresaID: int
SucursalID: int
CodigoAlmacen: varchar
NombreAlmacen: varchar
TipoAlmacen: varchar
PermiteCompras: bit
PermiteVentas: bit
Activo: bit
FechaAlta: datetime2
FechaModificacion: datetime2
```

### Tablas de Tablajería/Producción
**NO EXISTEN** tablas de tablajería en EDARSAHUB.

Las tablas `Finanzas_CortesCaja*` NO son de tablajería (son cortes de caja financieros).

**Conclusión**: Se deben crear TODAS las tablas de tablajería desde cero.

---

## 4. TABLAS RBAC/PERMISOS

### Tablas Principales
| Tabla | Uso |
|-------|-----|
| `Usuario_Catalogo` | Catálogo de usuarios |
| `Usuario_Roles` | Definición de roles |
| `Usuario_RolesAsignacion` | Asignación usuario-rol |
| `Usuario_Modulos` | Catálogo de módulos |
| `Usuario_PermisosRolModulo` | Permisos por rol/módulo |
| `Usuario_EmpresasAsignacion` | Empresas asignadas a usuario |
| `Usuario_SucursalesAsignacion` | Sucursales asignadas |
| `Usuario_AlmacenesAsignacion` | Almacenes asignados |
| `Usuario_ServidoresAsignacion` | Servidores asignados |
| `Usuario_Autorizaciones` | Autorizaciones pendientes |
| `Usuario_MatrizAutorizacion` | Matriz de autorizaciones |
| `Usuario_TiposAutorizacion` | Tipos de autorización |

**Conclusión**: El RBAC está completamente implementado en SQL. Se pueden agregar permisos de TABLAJERIA siguiendo el patrón existente.

---

## 5. ANÁLISIS DE RIESGOS

### Riesgo BAJO
| Área | Riesgo | Mitigación |
|------|--------|------------|
| Página Producción | Reemplazar placeholder | Es página vacía, sin lógica |
| Menú Layout | Agregar submenús | Solo agregar ítems, no modificar existentes |
| Crear tablas nuevas | Ningún impacto | No hay tablas de tablajería existentes |

### Riesgo MEDIO
| Área | Riesgo | Mitigación |
|------|--------|------------|
| RBAC | Agregar permisos | Seguir patrón existente exactamente |
| Inventario | Integración | Solo LECTURA y EVENTOS, no modificar tablas |

### Riesgo ALTO
| Área | Riesgo | Mitigación |
|------|--------|------------|
| Servidores externos | Conectividad | Solo SELECT, no modificar estructura |
| Módulos blindados | NO TOCAR | Tablero Ejecutivo, Comercial, Compras, Finanzas |

---

## 6. MÓDULOS BLINDADOS - VERIFICACIÓN

| Módulo | Estado | Impacto Tablajería |
|--------|--------|-------------------|
| Tablero Ejecutivo | PROTEGIDO | ❌ No tocar |
| Comercial | PROTEGIDO | ❌ No tocar |
| Compras | PROTEGIDO | ⚠️ Solo lectura futura (Fase 7) |
| Finanzas | PROTEGIDO | ⚠️ Solo eventos contables (Fase 9) |
| Operaciones/Inventarios | PROTEGIDO | ⚠️ Solo integración lectura (Fase 6) |
| RBAC | PROTEGIDO | ⚠️ Agregar permisos siguiendo patrón |

---

## 7. PROPUESTA DE IMPLEMENTACIÓN

### Fase 1 - Tablas SQL (SIN RIESGO)
Crear tablas nuevas con prefijo `Operaciones_Tablaje_`:
- `Operaciones_Tablaje_Plantillas`
- `Operaciones_Tablaje_PlantillasDetalle`
- `Operaciones_Tablaje_PlantillasVersiones`
- `Operaciones_Tablaje_Ordenes`
- `Operaciones_Tablaje_OrdenesDetalle`
- `Operaciones_Tablaje_Rendimientos`
- `Operaciones_Tablaje_Mermas`
- `Operaciones_Tablaje_Costos`
- `Operaciones_Tablaje_SyncLog`
- `Operaciones_Tablaje_SyncErrores`
- `Operaciones_Tablaje_Autorizaciones`
- `Operaciones_Tablaje_Auditoria`
- `Operaciones_Tablaje_Documentos`
- `Operaciones_Tablaje_EventosContables`

### Fase 2 - Backend FastAPI (BAJO RIESGO)
Crear módulo en `/app/backend/modules/tablajeria/`:
- `schemas.py`
- `repository.py`
- `service.py`
- `routes.py`
- `sync_service.py`

### Fase 3 - Frontend React (BAJO RIESGO)
Modificar `/app/frontend/src/pages/Produccion.js` → Tablajería
Agregar submenús en Layout.js bajo "Producción"

---

## 8. HALLAZGOS CLAVE

### ✅ Positivos
1. **Servidores YA registrados**: CIENFUEGOS TABLAJERIA y MPRO TABLAJERIA existen en `Servidores_Conexiones`
2. **Página Producción vacía**: Ideal para convertir en Tablajería
3. **RBAC completo en SQL**: Se puede extender con permisos de tablajería
4. **Inventario existe**: Se puede integrar sin modificar tablas existentes

### ⚠️ Advertencias
1. **Sin tablas de tablajería**: Se deben crear TODAS desde cero
2. **MPRO puede tener múltiples sucursales**: Diseñar con UnidadNegocioID/SucursalID
3. **Servidores externos pueden estar offline**: Manejar errores de conexión

### ❌ Prohibiciones
1. NO modificar Tablero Ejecutivo
2. NO modificar Comercial
3. NO modificar Compras (solo lectura futura)
4. NO modificar Finanzas (solo eventos contables)
5. NO crear lógica en MongoDB
6. NO usar date.today() sin timezone

---

## 9. SIGUIENTE PASO RECOMENDADO

**Solicitar autorización para:**
1. Crear tablas SQL de tablajería (DDL)
2. Registrar módulo TABLAJERIA en RBAC
3. Crear backend FastAPI
4. Modificar página Produccion.js

**Requiere autorización explícita porque:**
- Crea estructura nueva en EDARSAHUB SQL
- Modifica RBAC (aunque solo agrega, no modifica existente)
- Reemplaza página placeholder de Producción

---

*Diagnóstico Fase 0 Completado*
*Sin modificaciones realizadas al sistema*

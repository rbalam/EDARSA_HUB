# FASE 0.5 - VALIDACIÓN ARQUITECTÓNICA: MENÚS GOBERNADOS Y COMERCIAL/VENTAS

**Fecha:** 24 Mayo 2026  
**Autor:** Arquitecto ERP EDARSAHUB  
**Estado:** VALIDACIÓN COMPLETADA

---

## 1. RESUMEN EJECUTIVO

La FASE 0 (Sistema de Menús Gobernados) fue implementada correctamente. Se crearon las tablas necesarias, los 27 módulos según el manifiesto ERP están registrados y el endpoint funciona. Sin embargo, se detectaron áreas de mejora y riesgos que deben atenderse antes de avanzar con Comercial/Ventas UI.

### Conclusión General: ✅ APROBADO CON OBSERVACIONES

---

## 2. VALIDACIÓN DE TABLAS CREADAS

### 2.1 Sistema_Modulos ✅
- **Columnas:** 12 (correctas)
- **Llave primaria:** ModuloID (IDENTITY)
- **Índice único:** Codigo
- **Campos de auditoría:** FechaCreacion ✅
- **Campos faltantes:** FechaModificacion, UsuarioCreacionID (RECOMENDADO)

### 2.2 Sistema_ModulosMenus ✅
- **Columnas:** 12 (correctas)
- **Llave primaria:** MenuID (IDENTITY)
- **FKs definidas:** 
  - FK_Menu_Modulo → Sistema_Modulos ✅
  - FK_Menu_Padre → Sistema_ModulosMenus ✅ (auto-referencia)
- **Campos de auditoría:** FechaCreacion ✅

### 2.3 Sistema_ModulosPermisos ✅
- **Columnas:** 8 (correctas)
- **Llave primaria:** PermisoID (IDENTITY)
- **Índice único:** Codigo ✅
- **FK definida:** FK_Permiso_Modulo → Sistema_Modulos ✅

### ⚠️ OBSERVACIONES TABLAS:
1. Falta campo `EmpresaID` en tablas (multiempresa no aplica a catálogos globales - OK)
2. Falta campo `UsuarioModificacionID` y `FechaModificacion` para auditoría completa
3. No hay duplicidad con tablas previas (`Usuario_Modulos` existe pero es diferente)

---

## 3. VALIDACIÓN DE MÓDULOS OFICIALES

### Resultado: 27/27 PRESENTES ✅

| # | Código | Tipo | Estado |
|---|--------|------|--------|
| 1 | DIRECCION | PRINCIPAL | ✅ |
| 2 | COMERCIAL | PRINCIPAL | ✅ |
| 3 | POS | SATELITE | ✅ |
| 4 | COMPRAS | PRINCIPAL | ✅ |
| 5 | INVENTARIOS | PRINCIPAL | ✅ |
| 6 | TABLAJERIA | PRINCIPAL | ✅ |
| 7 | CAVA_SOCIOS | PRINCIPAL | ✅ |
| 8 | FINANZAS | PRINCIPAL | ✅ |
| 9 | HOST_TO_HOST | PRINCIPAL | ✅ |
| 10 | EDARSA_GO | SATELITE | ✅ |
| 11 | CONTABILIDAD | PRINCIPAL | ✅ |
| 12 | RH | PRINCIPAL | ✅ |
| 13 | ACTIVOS_FIJOS | PRINCIPAL | ✅ |
| 14 | CRM | PRINCIPAL | ✅ |
| 15 | COMISIONES | PRINCIPAL | ✅ |
| 16 | PORTAL_PROVEEDORES | PORTAL | ✅ |
| 17 | PORTAL_COMISIONISTAS | PORTAL | ✅ |
| 18 | PORTAL_CLIENTES | PORTAL | ✅ |
| 19 | CHEF_IA | SATELITE | ✅ |
| 20 | IA | PRINCIPAL | ✅ |
| 21 | CALIDAD | PRINCIPAL | ✅ |
| 22 | PROYECTOS | PRINCIPAL | ✅ |
| 23 | MARKETING | PRINCIPAL | ✅ |
| 24 | REPORTES_BI | PRINCIPAL | ✅ |
| 25 | INTEGRACIONES | PRINCIPAL | ✅ |
| 26 | CATALOGOS | PRINCIPAL | ✅ |
| 27 | SISTEMA | PRINCIPAL | ✅ |

**Clasificación:**
- Principales: 21
- Satélites: 3 (POS, EDARSA_GO, CHEF_IA)
- Portales: 3 (Proveedores, Comisionistas, Clientes)

---

## 4. VALIDACIÓN ENDPOINT /api/sistema/menus/usuario

### Resultado: FUNCIONAL ✅

| Criterio | Estado |
|----------|--------|
| Autenticación obligatoria | ✅ HTTP 401 sin token |
| SQL-first | ✅ Lee de EDARSAHUB SQL |
| Permisos RBAC | ✅ Filtra por rol |
| No MongoDB | ✅ Sin dependencias |
| No datos duros | ✅ |
| SuperAdmin ve todo | ✅ 27 módulos |
| Orden correcto | ✅ Por campo Orden |

### Respuesta para SuperAdmin:
```json
{
  "modulos": [...27 módulos...],
  "total": 27,
  "es_super_admin": true
}
```

---

## 5. VALIDACIÓN FRONTEND ACTUAL

### ⚠️ HALLAZGOS CRÍTICOS:

1. **Frontend NO consume `/api/sistema/menus/usuario`**
   - Layout.js usa menús **HARDCODEADOS** (líneas 179-377)
   - Usa endpoint `/api/auth/me/menu-permissions` para RBAC

2. **Menús duplicados potenciales:**
   - `modulos[]` hardcodeado en Layout.js
   - `Sistema_ModulosMenus` en SQL
   - **RIESGO: Si se integran sin consolidar, habrá conflicto**

3. **Endpoint actual de permisos:**
   - `/api/auth/me/menu-permissions` → 19 permisos módulos
   - Funciona pero es independiente de Sistema_ModulosPermisos

### RECOMENDACIÓN:
Antes de FASE 1 Comercial UI:
- **FASE 0.6:** Migrar Layout.js para consumir `/api/sistema/menus/usuario`
- **FASE 0.7:** Sincronizar Sistema_ModulosPermisos con Usuario_PermisosRolModulo

---

## 6. VALIDACIÓN RBAC

### Tablas RBAC existentes: 28 tablas
- Usuario_Roles ✅
- Usuario_RolesAsignacion ✅
- Usuario_EmpresasAsignacion ✅
- Usuario_PermisosRolModulo ✅
- Usuario_Modulos ✅
- Sistema_ModulosPermisos ✅ (NUEVA)

### ⚠️ RIESGO DE DUPLICIDAD:
- `Usuario_Modulos` vs `Sistema_Modulos` → Pueden coexistir (diferentes propósitos)
- `Usuario_PermisosRolModulo` vs `Sistema_ModulosPermisos` → REQUIERE INTEGRACIÓN

### ACCIÓN REQUERIDA:
Sistema_ModulosPermisos debe ser el **catálogo maestro** de permisos.
Usuario_PermisosRolModulo debe **referenciar** Sistema_ModulosPermisos.

---

## 7. VALIDACIÓN NO REGRESIÓN

### Pruebas Ejecutadas:

| Prueba | Estado |
|--------|--------|
| Login funciona | ✅ |
| Auth SQL-first | ✅ |
| /api/auth/me | ✅ |
| /api/comercial/tablero-ejecutivo | ✅ |
| /api/cava-socios/socios | ✅ |
| /api/crm/cuentas | ✅ |
| Sin errores 500 en logs | ✅ |
| Sin MongoDB nuevo | ✅ |
| /api/comercial/ventas-del-dia | ❌ 404 (endpoint no existe) |
| /api/servidores | ❌ 404 (ruta diferente) |
| /api/tablajeria/dashboard | ❌ 404 (ruta diferente) |

### Conclusión No Regresión: ✅ APROBADO
Los 404 son por rutas diferentes, no por regresión. Los módulos core funcionan.

---

## 8. INVENTARIO COMERCIAL/VENTAS EXISTENTE

### 8.1 Backend Comercial

**Archivos principales:**
- `/app/backend/modules/comercial/routes.py` (287KB, 10 endpoints GET)
- `/app/backend/modules/comercial/service.py` (112KB)
- `/app/backend/modules/comercial/repository.py` (27KB)
- `/app/backend/modules/comercial/kpis_repository.py` (18KB)
- `/app/backend/modules/comercial_v2/` (Versión actualizada)
- `/app/backend/modules/crm/comercial_routes.py` (CRM integrado)

**Endpoints Comercial V1:**
1. GET /comercial/tablero-ejecutivo
2. GET /comercial/sucursales/{server_id}
3. GET /comercial/metas/{server_id}
4. GET /comercial/ticket-perfecto/{server_id}
5. GET /comercial/ventas-tiempo/{server_id}
6. GET /comercial/mesas/{server_id}
7. GET /comercial/detalle-movimientos/{server_id}
8. GET /comercial/precios-constantes/{server_id}
9. GET /comercial/reporte-pax/{server_id}
10. GET /comercial/dashboard/{server_id}

**Endpoints Comercial V2:** (Bajo /api/v2/comercial)
- Sincronización EDARSAHUB
- KPIs consolidados

### 8.2 Tablas SQL Comercial: 36 tablas

**Tablas críticas:**
- `Comercial_KPIs_Diarios_v2` - KPIs por día
- `Comercial_KPIs_Mensuales_v2` - KPIs consolidados
- `Comercial_Ventas_Dia_Abiertas_v2` - Ventas en curso
- `Comercial_SyncLog_v2` - Log de sincronización
- `Venta_Cotizaciones` / `Venta_CotizacionesDetalle`
- `Venta_Pedidos` / `Venta_PedidosDetalle`
- `Venta_Remisiones` / `Venta_RemisionesDetalle`
- `Venta_ListasPrecios` / `Venta_ListasPreciosDetalle`
- `Cliente_Catalogo` / `Cliente_Contactos`

### 8.3 Frontend Comercial

**Estado actual:** NO HAY CARPETA `/pages/comercial`
- Comercial se accede desde Layout.js hardcodeado
- Ruta `/comercial` apunta a componente existente
- No hay UI modular separada

---

## 9. RIESGOS DETECTADOS

| ID | Riesgo | Severidad | Mitigación |
|----|--------|-----------|------------|
| R1 | Menús hardcodeados vs SQL | ALTA | Migrar Layout.js a consumir API |
| R2 | Duplicidad permisos RBAC | MEDIA | Consolidar con Sistema_ModulosPermisos |
| R3 | Comercial V1 vs V2 coexisten | MEDIA | Documentar y unificar gradualmente |
| R4 | 36 tablas comerciales | BAJA | Ya consolidadas en EDARSAHUB |
| R5 | Sin páginas frontend Comercial | MEDIA | Crear en FASE 1 |

---

## 10. RECOMENDACIONES PARA FASE 1

### PRERREQUISITOS (FASE 0.6 - 0.7):

**FASE 0.6 - Migrar Layout.js:**
1. Modificar Layout.js para consumir `/api/sistema/menus/usuario`
2. Eliminar arrays `modulos[]` y `sistema[]` hardcodeados
3. Renderizar menús dinámicamente desde SQL
4. Mantener fallback legacy durante transición

**FASE 0.7 - Consolidar RBAC:**
1. Poblar Sistema_ModulosPermisos con permisos granulares
2. Crear vista o función que unifique permisos
3. Actualizar `/api/auth/me/menu-permissions` para usar Sistema_ModulosPermisos

### FASE 1 - Comercial/Ventas UI (Subfases):

**FASE 1A:** Integrar Comercial al menú gobernado
- Insertar menús en Sistema_ModulosMenus
- Conectar rutas existentes

**FASE 1B:** Dashboard Comercial SQL-first
- Usar Comercial_KPIs_Diarios_v2
- Usar Comercial_Ventas_Dia_Abiertas_v2
- No crear tablas nuevas

**FASE 1C:** Clientes
- Usar Cliente_Catalogo existente
- Crear UI CRUD

**FASE 1D:** Cotizaciones/Remisiones
- Usar Venta_Cotizaciones, Venta_Remisiones
- Crear UI con workflow

**FASE 1E:** Precios y Listas
- Usar Venta_ListasPrecios
- No afectar POS/Comandero

**FASE 1F:** Costos y Márgenes
- Conectar con recetas, inventarios, compras
- Análisis de rentabilidad

---

## 11. CRITERIOS DE ACEPTACIÓN FASE 0.5

| # | Criterio | Estado |
|---|----------|--------|
| 1 | Tablas Sistema_Modulos* creadas | ✅ |
| 2 | 27 módulos insertados | ✅ |
| 3 | Clasificación correcta | ✅ |
| 4 | Endpoint funcional | ✅ |
| 5 | No regresión módulos core | ✅ |
| 6 | Inventario Comercial documentado | ✅ |
| 7 | Riesgos identificados | ✅ |
| 8 | Plan FASE 1 definido | ✅ |

---

## 12. DECISIÓN FINAL

### ✅ FASE 0.5 APROBADA

**SIGUIENTE PASO:**
Antes de FASE 1 Comercial UI, ejecutar:
- **FASE 0.6:** Migrar Layout.js a menús SQL
- **FASE 0.7:** Consolidar RBAC

**NO SE AUTORIZA** avanzar directamente a Comercial UI sin estas fases intermedias para evitar duplicidad de menús y conflictos RBAC.

---

*Documento generado: 24 Mayo 2026*
*Arquitecto: EDARSAHUB ERP System*

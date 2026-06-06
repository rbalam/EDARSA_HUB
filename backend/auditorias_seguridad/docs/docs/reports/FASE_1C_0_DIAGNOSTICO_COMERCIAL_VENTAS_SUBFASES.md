# FASE 1C-0: Diagnóstico Comercial/Ventas para Subfases

**Fecha**: 2026-05-24  
**Hora México**: 12:30 - 13:15  
**Ejecutado por**: Agente EDARSA HUB  
**Estado**: ✅ DIAGNÓSTICO COMPLETADO

---

## 1. Rutas Revisadas

### 1.1 Rutas Frontend (App.js)

| Ruta | Estado | Destino/Componente | Clasificación |
|------|--------|-------------------|---------------|
| `/comercial` | ✓ Existe | `Comercial.js` (Dashboard) | Principal |
| `/comercial/clientes` | ⚠ Redirige | → `/crm/cuentas` | Alias CRM |
| `/comercial/costos-margenes` | ⚠ Redirige | → `/comercial` | Stub (sin implementar) |
| `/comercial/ventas` | ✗ No existe | - | Pendiente |
| `/comercial/precios` | ✗ No existe | - | Pendiente |
| `/comercial/listas-precios` | ✗ No existe | - | Pendiente |
| `/comercial/devoluciones` | ✗ No existe | - | Pendiente |
| `/comercial/bonificaciones` | ✗ No existe | - | Pendiente |
| `/comercial/reservaciones` | ✗ No existe | - | Pendiente |
| `/crm/dashboard` | ✓ Existe | `CRMDashboard.jsx` | CRM |
| `/crm/cuentas` | ✓ Existe | `CuentasPage.jsx` | CRM |
| `/crm/solicitudes-alta` | ✓ Existe | `SolicitudesAltaPage.jsx` | CRM |
| `/crm/leads` | ✓ Existe | `LeadsPage.jsx` | CRM |
| `/crm/oportunidades` | ✓ Existe | `OportunidadesPage.jsx` | CRM |
| `/crm/pipeline` | ✓ Existe | `PipelinePage.jsx` | CRM |
| `/crm/cotizaciones` | ✓ Existe | `CotizacionesPage.jsx` | CRM |
| `/crm/pedidos` | ✓ Existe | `PedidosPage.jsx` | CRM |
| `/crm/remisiones` | ✓ Existe | `RemisionesPage.jsx` | CRM |

### 1.2 Menú SQL (Sistema_ModulosMenus)

**Módulo COMERCIAL (ModuloID=2):**

| MenuID | Código | Nombre | Ruta | Permiso |
|--------|--------|--------|------|---------|
| 25 | comercial.dashboard | Dashboard Comercial | /comercial | comercial |
| 26 | comercial.clientes | Clientes | /comercial/clientes | comercial.clientes |
| 27 | comercial.cotizaciones | Cotizaciones | /crm/cotizaciones | comercial.cotizaciones |
| 28 | comercial.pedidos | Pedidos | /crm/pedidos | comercial.pedidos |
| 29 | comercial.remisiones | Remisiones | /crm/remisiones | comercial.remisiones |
| 30 | comercial.costos | Costos y Márgenes | /comercial/costos-margenes | comercial.costos |

**Módulo CRM (ModuloID=14):**

| MenuID | Código | Nombre | Ruta | Permiso |
|--------|--------|--------|------|---------|
| 31 | crm.dashboard | Dashboard CRM | /crm/dashboard | crm |
| 32 | crm.cuentas | Cuentas | /crm/cuentas | crm |
| 33 | crm.solicitudes | Solicitudes Alta | /crm/solicitudes-alta | crm |
| 34 | crm.leads | Leads | /crm/leads | crm |
| 35 | crm.oportunidades | Oportunidades | /crm/oportunidades | crm |
| 36 | crm.pipeline | Pipeline | /crm/pipeline | crm |

---

## 2. Clasificación de Rutas

| Ruta | Clasificación |
|------|---------------|
| `/comercial` | ✓ Funcional - Dashboard NO-LIVE |
| `/comercial/clientes` | ⚠ Redirige a CRM - Decisión pendiente |
| `/comercial/costos-margenes` | ✗ Stub - Necesita implementación |
| `/crm/cotizaciones` | ✓ Funcional - Pertenece a CRM, accesible desde Comercial |
| `/crm/pedidos` | ✓ Funcional - Pertenece a CRM, accesible desde Comercial |
| `/crm/remisiones` | ✓ Funcional - Pertenece a CRM, accesible desde Comercial |

### Decisiones de Arquitectura Requeridas:

1. **Clientes**: ¿Mantener en CRM (`/crm/cuentas`) o crear `/comercial/clientes` separado?
   - Actualmente: `/comercial/clientes` → redirige a `/crm/cuentas`
   - Recomendación: Mantener alias, no duplicar

2. **Cotizaciones/Pedidos/Remisiones**: Ya apuntan a CRM desde el menú Comercial
   - Recomendación: Mantener integración actual sin duplicar

---

## 3. Endpoints Backend Encontrados

### 3.1 Módulo Comercial (`/api/comercial/`)

| Endpoint | Método | Estado |
|----------|--------|--------|
| `/comercial/tablero-ejecutivo` | GET | ✓ Implementado |
| `/comercial/dashboard/{server_id}` | GET | ✓ Implementado (EDARSAHUB SQL) |
| `/comercial/ventas-tiempo/{server_id}` | GET | ✓ Implementado (EDARSAHUB SQL) |
| `/comercial/sucursales/{server_id}` | GET | ✓ Implementado |
| `/comercial/metas/{server_id}` | GET | ✓ Implementado |
| `/comercial/ticket-perfecto/{server_id}` | GET | ✓ Implementado |
| `/comercial/mesas/{server_id}` | GET | ✓ Implementado |
| `/comercial/detalle-movimientos/{server_id}` | GET | ✓ Implementado |
| `/comercial/precios-constantes/{server_id}` | GET | ✓ Implementado |
| `/comercial/reporte-pax/{server_id}` | GET | ✓ Implementado |

### 3.2 Módulo CRM (`/api/crm/`)

| Endpoint | Método | Estado |
|----------|--------|--------|
| `/crm/cuentas` | GET/POST | ✓ Implementado |
| `/crm/cuentas/{id}` | GET | ✓ Implementado |
| `/crm/cuentas/{id}/ligar-cliente` | POST | ✓ Implementado |
| `/crm/clientes` | GET | ✓ Implementado |
| `/crm/clientes/solicitudes` | GET/POST | ✓ Implementado |
| `/crm/clientes/solicitudes/{id}/enviar` | POST | ✓ Implementado |
| `/crm/clientes/solicitudes/{id}/autorizar` | POST | ✓ Implementado |
| `/crm/clientes/solicitudes/{id}/rechazar` | POST | ✓ Implementado |
| `/crm/cotizaciones` | GET/POST | ✓ Implementado |
| `/crm/cotizaciones/{id}` | GET | ✓ Implementado |
| `/crm/cotizaciones/{id}/enviar` | POST | ✓ Implementado |
| `/crm/cotizaciones/{id}/aprobar` | POST | ✓ Implementado |
| `/crm/pedidos-venta` | GET/POST | ✓ Implementado |
| `/crm/pedidos-venta/{id}` | GET | ✓ Implementado |
| `/crm/pedidos-venta/{id}/confirmar` | POST | ✓ Implementado |
| `/crm/remisiones-venta` | GET/POST | ✓ Implementado |
| `/crm/remisiones-venta/{id}` | GET | ✓ Implementado |
| `/crm/actividades` | GET/POST | ✓ Implementado |
| `/crm/actividades/{id}/cerrar` | POST | ✓ Implementado |
| `/crm/leads` | (implícito) | ✓ Implementado |
| `/crm/oportunidades` | (implícito) | ✓ Implementado |

### 3.3 Endpoints FALTANTES

| Endpoint Necesario | Módulo Sugerido |
|--------------------|-----------------|
| `/comercial/costos-margenes` | Comercial |
| `/comercial/recetas/{producto_id}` | Comercial |
| `/comercial/precios-listas` | Comercial |
| `/comercial/devoluciones` | Comercial |
| `/comercial/bonificaciones` | Comercial |
| `/comercial/reservaciones` | Comercial/Eventos |

---

## 4. Tablas EDARSAHUB SQL Existentes por Submódulo

### 4.1 Clientes

| Tabla | Estado | Uso |
|-------|--------|-----|
| `Cliente_Catalogo` | ✓ Existe | Catálogo maestro de clientes |
| `Cliente_Contactos` | ✓ Existe | Contactos por cliente |
| `Cliente_Direcciones` | ✓ Existe | Direcciones por cliente |
| `Cliente_Grupos` | ✓ Existe | Categorías de clientes |
| `Cliente_UsuariosPortal` | ✓ Existe | Usuarios Portal Clientes |
| `Cliente_RolUsuarioPortal` | ✓ Existe | Roles Portal Clientes |

### 4.2 Ventas

| Tabla | Estado | Uso |
|-------|--------|-----|
| `Comercial_KPIs_Diarios_v2` | ✓ Existe | KPIs diarios consolidados |
| `Comercial_KPIs_Mensuales_v2` | ✓ Existe | KPIs mensuales |
| `Comercial_KPIs_Historico` | ✓ Existe | Histórico de KPIs |
| `Comercial_Ventas_Dia_Abiertas_v2` | ✓ Existe | Ventas del día actual |
| `Sync_Ventas_Historicas` | ✓ Existe | Ventas históricas sincronizadas |
| `Sync_Ventas_PorHora` | ✓ Existe | Ventas por hora sincronizadas |
| `Sync_Ventas_PorDiaSemana` | ✓ Existe | Ventas por día de semana |
| `Venta_Encabezado` | ✓ Existe | Encabezados de venta |
| `Venta_Detalle` | ✓ Existe | Detalle de ventas |
| `Venta_Estatus` | ✓ Existe | Catálogo de estatus |
| `Venta_FormaPago` | ✓ Existe | Formas de pago |
| `Venta_Pagos` | ✓ Existe | Pagos registrados |
| `Venta_CondicionesPago` | ✓ Existe | Condiciones de pago |

### 4.3 Cotizaciones/Pedidos/Remisiones

| Tabla | Estado | Uso |
|-------|--------|-----|
| `Venta_Cotizaciones` | ✓ Existe | Cotizaciones de venta |
| `Venta_CotizacionesDetalle` | ✓ Existe | Detalle de cotizaciones |
| `Venta_CotizacionesEstatus` | ✓ Existe | Estados de cotizaciones |
| `Venta_Pedidos` | ✓ Existe | Pedidos de venta |
| `Venta_PedidosDetalle` | ✓ Existe | Detalle de pedidos |
| `Venta_PedidosEstatus` | ✓ Existe | Estados de pedidos |
| `Venta_Remisiones` | ✓ Existe | Remisiones |
| `Venta_RemisionesDetalle` | ✓ Existe | Detalle de remisiones |
| `Venta_RemisionesHistorial` | ✓ Existe | Historial de remisiones |
| `Venta_Cat_EstatusRemision` | ✓ Existe | Catálogo estatus remisión |

### 4.4 Precios y Listas de Precios

| Tabla | Estado | Uso |
|-------|--------|-----|
| `Venta_ListasPrecios` | ✓ Existe | Listas de precios |
| `Venta_ListasPreciosDetalle` | ✓ Existe | Productos por lista |

### 4.5 Productos y Costos

| Tabla | Estado | Uso |
|-------|--------|-----|
| `Producto_Catalogo` | ✓ Existe | Catálogo de productos |
| `Producto_Familias` | ✓ Existe | Familias de productos |
| `Producto_SubFamilias` | ✓ Existe | Subfamilias |
| `Producto_Lineas` | ✓ Existe | Líneas de productos |
| `Producto_Marcas` | ✓ Existe | Marcas |
| `Producto_Presentaciones` | ✓ Existe | Presentaciones |
| `Producto_Sustitutos` | ✓ Existe | Productos sustitutos |
| `Producto_Equivalentes` | ✓ Existe | Equivalencias |
| `Tablajeria_CosteoProduccion` | ✓ Existe | Costeo de producción |
| `Operaciones_Tablaje_Rendimientos` | ✓ Existe | Rendimientos |
| `Operaciones_Tablaje_Costos` | ✓ Existe | Costos de tablaje |

### 4.6 CRM

| Tabla | Estado | Uso |
|-------|--------|-----|
| `CRM_Cuentas` | ✓ Existe | Cuentas comerciales |
| `CRM_Leads` | ✓ Existe | Leads/Prospectos |
| `CRM_Oportunidades` | ✓ Existe | Oportunidades de venta |
| `CRM_Actividades` | ✓ Existe | Actividades/Tareas |
| `CRM_Contratos` | ✓ Existe | Contratos |
| `CRM_Propuestas` | ✓ Existe | Propuestas |
| `CRM_ClientesSolicitudesAlta` | ✓ Existe | Solicitudes de alta |
| `CRM_Config_Pipelines` | ✓ Existe | Configuración de pipelines |
| `CRM_Config_PipelineEtapas` | ✓ Existe | Etapas de pipeline |
| `CRM_Cat_*` | ✓ Varios | Catálogos CRM |

### 4.7 Tablas FALTANTES en EDARSAHUB

| Tabla Necesaria | Submódulo | Prioridad |
|-----------------|-----------|-----------|
| `Comercial_Recetas` | Costos/Márgenes | P0 - Sincronizar de fuentes |
| `Comercial_Recetas_Insumos` | Costos/Márgenes | P0 - Sincronizar de fuentes |
| `Comercial_Insumos_Costos` | Costos/Márgenes | P0 - Sincronizar de fuentes |
| `Comercial_Devoluciones` | Devoluciones | P1 |
| `Comercial_Bonificaciones` | Bonificaciones | P1 |
| `Comercial_Reservaciones` | Reservaciones | P2 |

---

## 5. Fuentes de Datos para Costos/Márgenes

### 5.1 Estructura en SoftRestaurant

| Tabla | Contenido | Columnas Clave |
|-------|-----------|----------------|
| `productos` | Catálogo de platillos | idproducto, descripcion, idgrupo |
| `productosdetalle` | Precios por empresa | idproducto, precio, preciosinimpuestos |
| `grupos` | Grupos/Categorías | idgrupo, descripcion |
| `insumos` | Ingredientes | idinsumo, descripcion, unidad |
| `insumosdetalle` | Costos por empresa | idinsumo, costo, costopromedio, costoestandar |
| `explosioninsumosdetalle` | Recetas (producto→insumos) | idproducto, idinsumo, cantidad, costo |

### 5.2 Estructura en MPRO

| Tabla | Contenido | Columnas Clave |
|-------|-----------|----------------|
| `Producto` | Catálogo de productos | (por investigar) |
| `Producto_Precio` | Precios por lista | (por investigar) |
| `Formula_Produccion` | Fórmulas/Recetas | (por investigar) |
| `Formula_Produccion_Detalle` | Componentes de receta | (por investigar) |
| `Producto_Componente` | Componentes/Insumos | (por investigar) |

### 5.3 Ejemplo de Datos Reales (LA ESTELAR)

**Productos con precios:**
```
[A085003] A ARANDANOS C/CHILE | Grupo: A BOTANAS | Precio: $45.00
[A050004] A CHILPALCHOLE DE CAMARON | Grupo: A CALIENTES | Precio: $280.00
[A030005] ZZZA PESCA DEL DIA | Grupo: A CARNE/DEL MAR | Precio: $320.00
```

**Insumos con costos:**
```
A400001 | A AGUACATE HASS GR | GR | Costo: $0.048 | CostoProm: $0.056
A400005 | A ALBAHACA GR | GR | Costo: $0.168 | CostoProm: $0.248
A400094 | A LIMON PERSA GR | GR | Costo: $0.023 | CostoProm: $0.016
```

---

## 6. Duplicidades Detectadas

| Elemento | Ubicación 1 | Ubicación 2 | Recomendación |
|----------|-------------|-------------|---------------|
| Clientes | `/comercial/clientes` | `/crm/cuentas` | Mantener alias, no duplicar |
| Cotizaciones | menú Comercial | `/crm/cotizaciones` | Mantener integración actual |
| Pedidos | menú Comercial | `/crm/pedidos` | Mantener integración actual |
| Remisiones | menú Comercial | `/crm/remisiones` | Mantener integración actual |

**Nota**: No hay duplicidades de datos, solo de navegación. El diseño actual es correcto.

---

## 7. Dependencias MongoDB Detectadas

**NINGUNA** para los módulos Comercial/Ventas analizados.

✓ Todos los endpoints de `/comercial/` consultan EDARSAHUB SQL.
✓ Todos los endpoints de `/crm/` consultan EDARSAHUB SQL.
✓ No hay referencias a MongoDB en `comercial/routes.py` ni `crm/comercial_routes.py`.

---

## 8. Dependencias Live Detectadas

| Módulo | Estado |
|--------|--------|
| Dashboard Comercial | ✓ NO-LIVE (FASE 1B-R1) |
| Ventas por Hora | ✓ NO-LIVE (FASE 1B-R2) |
| CRM | ✓ NO-LIVE |

**Costos/Márgenes**: Requerirá sincronización de fuentes remotas a EDARSAHUB (similar a `Sync_Ventas_PorHora`).

---

## 9. Permisos RBAC Existentes

| Permiso | Módulo | Estado |
|---------|--------|--------|
| `comercial` | Dashboard | ✓ Definido en menú |
| `comercial.clientes` | Clientes | ✓ Definido en menú |
| `comercial.cotizaciones` | Cotizaciones | ✓ Definido en menú |
| `comercial.pedidos` | Pedidos | ✓ Definido en menú |
| `comercial.remisiones` | Remisiones | ✓ Definido en menú |
| `comercial.costos` | Costos y Márgenes | ✓ Definido en menú |
| `crm` | Dashboard CRM | ✓ Definido en menú |

### 9.1 Permisos RBAC Faltantes

| Permiso Sugerido | Módulo |
|------------------|--------|
| `comercial.clientes.ver` | Clientes (lectura) |
| `comercial.clientes.crear` | Clientes (alta) |
| `comercial.clientes.editar` | Clientes (modificación) |
| `comercial.ventas.ver` | Ventas (lectura) |
| `comercial.precios.ver` | Precios (lectura) |
| `comercial.precios.editar` | Precios (modificación) |
| `comercial.listas_precios.ver` | Listas de precios |
| `comercial.listas_precios.editar` | Listas de precios |
| `comercial.costos_margenes.ver` | Costos y márgenes |
| `comercial.costos_margenes.exportar` | Exportación de reportes |
| `comercial.costos_margenes.simular_precio` | Simulador de precios |
| `comercial.devoluciones.ver` | Devoluciones |
| `comercial.bonificaciones.ver` | Bonificaciones |
| `comercial.reservaciones.ver` | Reservaciones |

---

## 10. Relación con CRM

### Arquitectura Actual

```
COMERCIAL/VENTAS                           CRM
├── Dashboard (/comercial)                 ├── Dashboard (/crm/dashboard)
├── Clientes → redirige ─────────────────► Cuentas (/crm/cuentas)
├── Cotizaciones → apunta ────────────────► Cotizaciones (/crm/cotizaciones)
├── Pedidos → apunta ─────────────────────► Pedidos (/crm/pedidos)
├── Remisiones → apunta ──────────────────► Remisiones (/crm/remisiones)
└── Costos y Márgenes (pendiente)          ├── Solicitudes Alta
                                           ├── Leads
                                           ├── Oportunidades
                                           └── Pipeline
```

### Recomendación

**Mantener integración actual**:
- Comercial = Análisis y administración de ventas
- CRM = Gestión de relaciones y flujos comerciales
- Cotizaciones/Pedidos/Remisiones son compartidos pero viven en CRM

---

## 11. Relación con Satélites

### 11.1 POS Genérico

| Aspecto | Estado |
|---------|--------|
| Menú separado | ✓ Módulo 28 (POS_GENERICO) |
| Rutas separadas | ✓ No hay conflicto |
| Datos | Lee de EDARSAHUB SQL |
| **Impacto de Costos/Márgenes** | Ninguno directo - POS opera, Comercial analiza |

### 11.2 Comandero Restaurantero

| Aspecto | Estado |
|---------|--------|
| Menú separado | ✓ Módulo 3 (COMANDERO_RESTAURANTERO) |
| Rutas separadas | ✓ No hay conflicto |
| **Impacto de Costos/Márgenes** | Podría beneficiarse del catálogo de recetas para alertas de ingredientes |

### 11.3 Portal de Clientes

| Aspecto | Estado |
|---------|--------|
| Menú separado | ✓ Módulo 18 (PORTAL_CLIENTES) |
| Tablas relacionadas | `Cliente_UsuariosPortal`, `Cliente_RolUsuarioPortal` |
| **Impacto de Costos/Márgenes** | Ninguno - Portal Clientes no ve costos |
| **Impacto de Precios** | Podría mostrar listas de precios públicas |

### 11.4 EDARSA GO

| Aspecto | Estado |
|---------|--------|
| Menú separado | ✓ Módulo 10 (EDARSA_GO) |
| **Impacto de Costos/Márgenes** | Ninguno - EDARSA GO cobra, no analiza costos |

---

## 12. Relación con Módulos Relacionados

### 12.1 Inventarios

| Relación | Tipo | Impacto |
|----------|------|---------|
| Existencias | Lectura | Costos/Márgenes puede mostrar existencia de insumos |
| Movimientos | Lectura | Trazabilidad de consumo |
| **Riesgo** | Bajo | Solo lectura de EDARSAHUB |

### 12.2 Compras

| Relación | Tipo | Impacto |
|----------|------|---------|
| Costos de insumos | Lectura | Costos/Márgenes necesita costos actualizados de compras |
| Proveedores | Lectura | Referencia de proveedor por insumo |
| **Riesgo** | Bajo | Solo lectura |

### 12.3 Tablajería/Producción

| Relación | Tipo | Impacto |
|----------|------|---------|
| Recetas | Lectura | Ya existe `Tablajeria_CosteoProduccion` |
| Rendimientos | Lectura | `Operaciones_Tablaje_Rendimientos` |
| **Riesgo** | Medio | Posible duplicidad con nuevo módulo de recetas |

### 12.4 Tablero Ejecutivo

| Relación | Tipo | Impacto |
|----------|------|---------|
| KPIs | Lectura | Comparte `Comercial_KPIs_Diarios_v2` |
| **Riesgo** | Bajo | Solo lectura, tablas compartidas |

---

## 13. Riesgos Identificados

| Riesgo | Severidad | Mitigación |
|--------|-----------|------------|
| Duplicidad de recetas entre Tablajería y nuevo módulo | Media | Usar tablas existentes de Tablajería si aplican |
| Sincronización de costos desde fuentes remotas | Media | Crear job similar a `Sync_Ventas_PorHora` |
| Precios inconsistentes entre fuentes | Alta | Definir fuente autoritativa por unidad |
| Permisos RBAC incompletos | Baja | Crear permisos antes de pantallas |

---

## 14. Propuesta de Subfases 1C-1 a 1C-6

### FASE 1C-1: Clientes
**Alcance**: Pantalla `/comercial/clientes` con lectura desde EDARSAHUB SQL.
**Decisión**: ¿Crear pantalla propia o mantener alias a CRM?
**Tablas**: `Cliente_Catalogo`, `Cliente_Contactos`, `Cliente_Direcciones`, `Cliente_Grupos`
**Prioridad**: P1
**Riesgo**: Bajo

### FASE 1C-2: Precios y Listas de Precios
**Alcance**: Pantalla `/comercial/precios` y `/comercial/listas-precios`.
**Tablas**: `Venta_ListasPrecios`, `Venta_ListasPreciosDetalle`, `Producto_Catalogo`
**Endpoint nuevo**: `/api/comercial/precios-listas`
**Prioridad**: P1
**Riesgo**: Bajo

### FASE 1C-3: Costos y Márgenes ⭐
**Alcance**: Pantalla `/comercial/costos-margenes` con:
- Vista jerárquica (Grupo → Familia → Producto → Receta → Insumos)
- Columnas: Grupo, Familia, Precio Venta, Nombre, Receta, Cantidad, Unidad Med, Costo, Total, Utilidad, Margen
- Colapsar/expandir recetas
- Ordenamiento por nombre, precio, margen
- Doble clic en producto compuesto → Ver subrecetas
**Tablas nuevas**: `Sync_Recetas_Productos`, `Sync_Recetas_Insumos`, `Sync_Insumos_Costos`
**Job de sync**: Crear `sync_recetas.py` similar a `sync_ventas.py`
**Fuentes**: SoftRestaurant (`productos`, `insumos`, `insumosdetalle`, `explosioninsumosdetalle`)
**Prioridad**: P0 (SOLICITADO POR USUARIO)
**Riesgo**: Medio - Requiere sincronización de fuentes remotas

### FASE 1C-4: Devoluciones y Bonificaciones
**Alcance**: Pantallas `/comercial/devoluciones` y `/comercial/bonificaciones`.
**Tablas**: Requiere investigación de fuentes
**Prioridad**: P2
**Riesgo**: Medio

### FASE 1C-5: Reservaciones/Eventos
**Alcance**: Pantalla `/comercial/reservaciones`.
**Tablas**: Requiere investigación de fuentes
**Prioridad**: P3
**Riesgo**: Bajo

### FASE 1C-6: Integración CRM (Cotizaciones/Pedidos/Remisiones)
**Alcance**: Definir si se crean pantallas en Comercial o se mantienen alias a CRM.
**Decisión arquitectónica**: Mantener actual o migrar.
**Prioridad**: P2
**Riesgo**: Bajo si se mantiene actual

---

## 15. Requerimientos UI Costos y Márgenes (Según Imagen Usuario)

### Estructura de Tabla

| Columna | Tipo | Ordenable |
|---------|------|-----------|
| GRUPO | Texto | Sí |
| FAMILIA | Texto | Sí |
| PRECIO VENTA | Moneda | Sí |
| NOMBRE | Texto | Sí |
| RECETA | Texto/Expansión | No |
| CANTIDAD | Número | No |
| UNIDAD MED | Texto | No |
| COSTO | Moneda | No |
| TOTAL | Moneda | Sí |
| UTILIDAD | Moneda | Sí |
| MARGEN | Porcentaje | Sí |

### Funcionalidades Requeridas

1. **Contraer/Expandir**: 
   - Por defecto mostrar solo: Nombre, Precio Venta, Costo Total, Utilidad, Margen
   - Al expandir: Mostrar detalle de receta con insumos

2. **Ordenamiento**:
   - Por Nombre (A-Z, Z-A)
   - Por Precio Venta (Mayor-Menor, Menor-Mayor)
   - Por Margen (Mayor-Menor, Menor-Mayor)

3. **Subrecetas**:
   - Si producto tiene "PRODUCCION" o "SUB-RECETAS" en su tipo
   - Doble clic → Modal/Panel con receta expandida
   - Mostrar: Insumos, Cantidades, Costos unitarios, Rendimientos

4. **Cálculos**:
   - `TOTAL = COSTO_UNITARIO × CANTIDAD`
   - `UTILIDAD = PRECIO_VENTA - TOTAL_COSTO`
   - `MARGEN = (UTILIDAD / PRECIO_VENTA) × 100`

---

## 16. Recomendación de Implementación

### Primera Subfase: FASE 1C-3 (Costos y Márgenes)

**Justificación**:
1. Explícitamente solicitado por el usuario con mockup visual
2. Mayor valor de negocio (análisis de rentabilidad)
3. Sirve de base para decisiones de precios (FASE 1C-2)
4. No depende de Clientes ni CRM

**Prerequisitos**:
1. Crear job de sincronización `sync_recetas.py`
2. Crear tablas en EDARSAHUB: `Sync_Recetas_Productos`, `Sync_Recetas_Insumos`
3. Definir endpoint `/api/comercial/costos-margenes/{server_id}`
4. Implementar pantalla con características solicitadas

**Estimación**: 
- Job de sync: Similar a `sync_ventas.py` (2-3 endpoints de lectura remota)
- Endpoint: Lectura jerárquica de EDARSAHUB
- Frontend: Componente React con tabla expandible

---

## 17. Validaciones Confirmadas

| # | Validación | Estado |
|---|------------|--------|
| 1 | Login funciona | ✓ |
| 2 | Auth SQL-first funciona | ✓ |
| 3 | Menú SQL carga | ✓ |
| 4 | Comercial/Ventas carga | ✓ |
| 5 | Dashboard Comercial sigue funcionando | ✓ |
| 6 | Ventas por Hora sigue EDARSAHUB SQL | ✓ |
| 7 | Tablero Ejecutivo sigue funcionando | No probado (fuera de alcance) |
| 8-13 | Otros módulos | No probado (fuera de alcance) |
| 14 | No se agregan dependencias MongoDB | ✓ |
| 15 | No se agregan conexiones live | ✓ |
| 16 | No se crean tablas duplicadas | ✓ |
| 17-19 | Seguridad | ✓ |

---

## 18. Conclusión

El diagnóstico FASE 1C-0 está completo. El sistema tiene una arquitectura sólida con:

- ✓ Módulos Comercial y CRM bien separados
- ✓ Arquitectura NO-LIVE validada
- ✓ Tablas de soporte existentes para la mayoría de submódulos
- ✓ Integración CRM → Comercial funcional

**Gap principal**: Falta módulo de Costos/Márgenes con sincronización de recetas desde fuentes remotas.

**Recomendación**: Proceder con FASE 1C-3 (Costos y Márgenes) como primera implementación.

---

**Documento generado por**: Agente EDARSA HUB  
**Fecha de generación**: 2026-05-24 13:15 (hora México)

# Edarsa Hub - PRD

## Última Actualización: Marzo 2026

### Bug Fixes y Mejoras Recientes (29 Mar 2026 - Sesión 2)
- **Corregido:** Bug rutas - "Tablero de Dirección" ya no abre "Dashboard de Inventarios" 
  - Menú reorganizado: "Tablero Ejecutivo" primero, "Dashboard Inventarios" debajo de "Inventarios"
  - Redirect por defecto ahora va a `/tablero-ejecutivo`
- **Nuevo:** Badges en multi-selectores de Inventarios
  - Almacenes seleccionados muestran badges azules con "×" para eliminar
  - Inventarios iniciales seleccionados muestran badges verdes
  - Inventarios finales seleccionados muestran badges naranjas
- **Corregido:** Inventarios no cargaban para SoftRestaurant ("No hay inventarios disponibles")
  - El endpoint esperaba `sucursal` y `almacen` (nombres), pero frontend enviaba `sucursal_id` y `almacen_id`
  - Ahora pasa `sucursal: 'SoftRestaurant'` para servidores SoftRestaurant
  - Parsing de respuesta corregido (acepta array directo o `{inventarios: [...]}`)
- **Nuevo:** Catálogo de Roles completo
  - Ubicado en Sistema > Usuarios > Tab "Roles"
  - CRUD completo: Crear, Editar, Eliminar roles
  - 14 módulos disponibles para asignar permisos
  - 3 roles predeterminados (Sistema): Administrador, Supervisor, Usuario
  - Los roles de sistema no se pueden eliminar pero sí editar sus permisos
  - Colección MongoDB `roles` creada

### Bug Fixes y Mejoras Anteriores (29 Mar 2026)
- **Corregido:** Etiqueta "Tipo" en movimientos usa el campo `C.tipo` de la BD (no el signo de cantidad)
- **Renombrado:** "Ticket Promedio" → "Cheque Promedio" y "Consumo por Persona" → "Pax Promedio"
- **Renombrado:** "Cienfuegos SoftRestaurant" → "CIENFUEGOS" (en MongoDB)
- **Nuevo:** Comparativa de PAX vs mes/año anterior en Dashboard Comercial
- **Nuevo:** PAX agregado al Comparativo del Tablero Ejecutivo (Mes Actual/Anterior/Año Anterior)
- **Nuevo:** Reporte de PAX con drill-up/down por vendedor o ticket
- **Mejorado:** Exportación Excel de Análisis de Inventario ahora ordena por Diferencia_Costo (negativo a positivo)
- **Mejorado:** Detalle del Tablero Ejecutivo ahora pasa parámetro `sucursal` para mostrar gráficas por hora/día correctamente
- **Reorganizado (29 Mar 2026):** KPIs del Dashboard Comercial - Nueva estructura:
  - **Fila 1:** Ventas del Período, Pax Promedio (Ventas ÷ PAX), Cheque Promedio (Ventas ÷ Cheques)
  - **Fila 2:** PAX Total, Cheques Total, Rotación Mesas
- **Nuevo (29 Mar 2026):** Multi-selección de Inventarios en Reportes
  - Inventario Inicial y Final ahora soportan selección múltiple
  - Incluye buscador dentro del dropdown
  - Backend actualizado para combinar múltiples folios en el análisis
- **Corregido (29 Mar 2026):** Bug de MPRO en Tablero Ejecutivo
  - Las unidades MPRO no aparecían por error SQL `Invalid column name 'Vn_Cancelacion'`
  - Corregido usando formato de fecha YYYYMMDD en todas las queries MPRO
- **Nuevo (29 Mar 2026):** CRUD de Consultas Personalizadas en Catálogo SQL
  - Botón "+ Nueva" para agregar consultas personalizadas
  - Modal con campos: Nombre, Sistema, Categoría, Parámetros, Descripción, SQL
  - Consultas almacenadas en MongoDB (colección `consultas_custom`)
  - Botón de eliminar para consultas personalizadas
  - Las consultas custom se mezclan con las predefinidas y muestran etiqueta "Custom"
- **Corregido (29 Mar 2026):** Error `Invalid object name 'invfisicomov'` en Auditoría Operativa
  - Nombre de tabla corregido a `invfisicomovtos` y columna `fisicoalmacen1`
- **Nuevo (29 Mar 2026):** Menú ERP Completo con módulos placeholder
  - Finanzas (Próximamente) - Libro Mayor, Cuentas, Conciliación
  - Producción MRP (Próximamente) - Órdenes, BOM, Tiempos
  - Recursos Humanos (Próximamente) - Nómina, Asistencias, Vacaciones
  - Reportes BI (Próximamente) - Análisis Predictivo, KPIs

### Sistema Standalone (Pendiente - Solo cuando haya cliente)
Cuando un cliente requiera usar el sistema SIN BD externa:
- Crear colecciones MongoDB: productos, inventarios, ventas, compras, etc.
- Estimación: ~2,000-2,800 créditos

## CHECKPOINT ESTABLE - 29 Marzo 2026
> **Aplicación renombrada a "Edarsa Hub"**
> **Módulo de Compras con TABS: Dashboard, Autorización, Análisis**
> **Módulo Comercial (Ventas) con DATOS REALES - ✅ COMPLETADO**
> **TABLERO EJECUTIVO con MPRO dividido por sucursal - ✅ COMPLETADO (27 Mar 2026)**
> **Drill-down en KPIs (doble click para ver movimientos) - ✅ COMPLETADO (27 Mar 2026)**
> **REPORTE DE PAX con drill-down vendedor/ticket - ✅ COMPLETADO (29 Mar 2026)**
> **Análisis de compras por proveedor con drill-down hasta nivel factura/productos**
> **Reportes de Análisis de Inventarios funcionando para SoftRestaurant y MPRO.**

---

## Resumen del Producto
**Edarsa Hub** - Aplicación web (Mini-ERP) para analizar inventarios de múltiples sucursales y autorizar compras. Los datos se obtienen de servidores SQL Server con diferentes estructuras (ManagmentPro y SoftRestaurant).

## Arquitectura Técnica

### Stack
- **Frontend**: React, TailwindCSS, Shadcn UI
- **Backend**: FastAPI, Python
- **Base de Datos**: MongoDB (configuración), SQL Server (datos de inventario)
- **Bibliotecas SQL**: pytds (principal), pymssql (fallback)

### URLs
- **Preview**: https://stock-tracker-990.preview.emergentagent.com
- **API**: https://stock-tracker-990.preview.emergentagent.com/api

### Credenciales de Prueba
- **Admin**: admin@inventario.com / admin123

---

## TABLERO EJECUTIVO - IMPLEMENTADO ✅ (27 Mar 2026)

### Funcionalidades:
1. **Consolidación Multi-Servidor** - Ventas de todos los servidores (SoftRestaurant + MPRO)
2. **MPRO dividido por sucursal** - 130° QUERETARO, ORIGEN, EDARSA (como en Inventarios)
3. **KPIs consolidados** - Ventas, PAX, Cheques, Proyección, Ticket Promedio
4. **Comparativos** - vs Mes Anterior, vs Año Anterior
5. **Drill-down por unidad** - Click para ver detalle de cada sucursal

### Datos Verificados (Marzo 2026):
- Ventas Consolidadas: $10.92M
- Unidades: 5 (130° QUERETARO, ORIGEN, EDARSA, Cienfuegos, LA ESTELAR)
- Variación vs Mes: -17.2%
- Variación vs Año: +14.9%

---

## MÓDULO COMERCIAL (VENTAS) - IMPLEMENTADO ✅ (27 Mar 2026)

### Estructura con TABS:
1. **Dashboard** - KPIs de ventas, ticket promedio, PAX, comparativos
2. **Ticket Perfecto** - Análisis de tickets completos, rentabilidad por producto
3. **Metas** - Metas por producto y vendedor (calculadas dinámicamente)
4. **Por Hora/Día** - Ventas por hora pico y día de semana
5. **Mesas** - Rotación de mesas/hora, comensales, capacidad

### Funcionalidades Implementadas:
- KPIs reales desde SQL Server (SoftRestaurant)
- Ventas del período, ticket promedio, PAX total
- Comparativo vs período anterior (%)
- Top productos por rentabilidad (margen %)
- Ventas por hora (horarios pico)
- Ventas por día de la semana
- Análisis de rotación por hora
- **DRILL-DOWN en KPIs (doble click para ver detalle de movimientos)** ✅ NUEVO

### Endpoints Nuevos (27 Mar 2026):
- `GET /api/comercial/dashboard/{server_id}` - KPIs y comparativos
- `GET /api/comercial/ticket-perfecto/{server_id}` - Ticket perfecto y rentabilidad
- `GET /api/comercial/metas/{server_id}` - Metas por producto y vendedor
- `GET /api/comercial/ventas-tiempo/{server_id}` - Ventas por hora y día
- `GET /api/comercial/mesas/{server_id}` - Rotación y comensales
- `GET /api/comercial/detalle-movimientos/{server_id}` - **NUEVO** Drill-down de cheques

### Datos Verificados (LA ESTELAR - Marzo 2026):
- Ventas del Mes: $2,191,051.00
- Ticket Promedio: $1,619.40
- Cheques: 1,353
- PAX Total: 4,007
- Comparativo: -25.2% vs período anterior

---

## MÓDULO DE COMPRAS - IMPLEMENTADO ✅ (27 Mar 2026)

### Estructura con TABS (menos clicks):
1. **Dashboard** - KPIs de compras, alertas, top proveedores
2. **Autorización** - Cálculo de pedido sugerido (existente)
3. **Análisis** - Compras por proveedor con drill-down

### Funcionalidades Implementadas:
- Tabla pivote: Proveedor × Mes con totales
- Drill-down 3 niveles: Proveedor → Facturas → Productos
- Visor de documentos (PDF/XML) - estructura lista
- Alertas de desviación Compras vs Consumos
- Validaciones fiscales (RFC emisor/receptor) - estructura lista

### Endpoints Nuevos:
- `GET /api/compras/dashboard/{server_id}` - KPIs y alertas
- `POST /api/compras/analisis` - Análisis por proveedor/mes
- `GET /api/compras/facturas-proveedor/{server_id}` - Facturas de un proveedor
- `GET /api/compras/detalle-factura/{server_id}/{folio}` - Detalle de factura

---

## FUNCIONALIDADES VERIFICADAS

### 1. Reporte Análisis de Inventarios - SoftRestaurant ✅ (23 Mar 2026)

#### Almacén BODEGA (Presentaciones) - FUNCIONANDO
- Catálogo de productos (INSUMOS + PRESENTACIONES inventariables)
- Inventario inicial y final por folio
- Movimientos entre inventarios
- Códigos de producto SIN doble prefijo (B130009, no BB130009)

#### Almacén CONSUMO (200 BARRA) - FUNCIONANDO
- Catálogo de INSUMOS inventariables
- Inventarios físicos
- Movimientos
- **Ventas calculadas correctamente**:
  - Filtro por fecha de APERTURA del turno
  - Rango: Día del inventario inicial (00:00:00) hasta día ANTERIOR al inventario final (23:59:59)
  - Incluye todos los turnos del período (ej: turno del 15 que abre a las 13:27)
  - Intenta incluir tablas temporales (temcheques/temcheqdet) si existen

#### Datos Verificados:
- B130004 (RON CAPITAN MORGAN): Ventas = 1,035.00 ✓
- B130009 (RON BACARDI BLANCO): Ventas = 18,802.50 ✓

### 2. Reporte Análisis de Inventarios - MPRO ✅ (24 Mar 2026)

#### Lógica Implementada:
El reporte muestra productos según la siguiente lógica:
1. **INSUMOS (Dp_Cve_Departamento = '0007')** que tienen **PRESENTACIONES** asociadas en `Producto_Presentacion`
2. **COMPRAS** que NO están registradas como presentación de ningún insumo

#### Tablas MPRO utilizadas:
- `Producto` - Catálogo de productos con departamento
- `Producto_Presentacion` - Relaciona INSUMOS con sus presentaciones de compra
  - `Pr_Cve_Producto` = Código del INSUMO
  - `Pp_Producto` = Código de la PRESENTACIÓN (unidad de compra)
  - `Pp_Cantidad` = Rendimiento
- `Producto_Kit` - Recetas (relaciona producto vendido con componentes)
  - `Pr_Cve_Producto` = Producto vendido
  - `Pk_Producto` = Insumo usado en la receta
  - `Pk_Cantidad` = Cantidad del insumo por unidad vendida

#### Cálculo de Ventas:
Las ventas se calculan usando `Producto_Kit`. Cuando se vende un producto, se consume el insumo según la receta.

#### Detección de Errores de Captura:
El sistema detecta cuando una PRESENTACIÓN fue capturada en inventario físico, pero debería haberse capturado el INSUMO. Esto se muestra como alerta en el frontend.

#### Ejemplo - Ron Bacardí:
- **INSUMO `0000000185`** (Ron Bacardí Blanco ml*) → **SÍ APARECE** en el reporte
- **PRESENTACIONES `0000007586` y `0000009049`** (botellas 750ml y 700ml) → **NO APARECEN** (son presentaciones del insumo)
- Las ventas se calculan sumando: (cantidad_vendida × cantidad_receta) para cada producto que usa el insumo

### 3. Modal Detalle de Movimientos - FUNCIONANDO
- Muestra detalle por producto al hacer doble clic
- Incluye: folio, fecha, cantidad, tipo, descripción

### 4. Modal Detalle de Ventas - FUNCIONANDO  
- Muestra detalle de ventas por producto
- Incluye: folio, fecha, cantidad, producto vendido

### 5. Filtros - FUNCIONANDO
- Por Categoría (Clasificación)
- Por Familia (Grupo)
- Por SubFamilia (SubGrupo)

---

## Consultas SQL Clave

### Ventas para Almacenes de Consumo (SoftRestaurant)
```sql
SELECT 
    RTRIM(LTRIM(receta.idinsumo)) as CODIGO,
    SUM(venta.cantidad * COSTOS.cantidad) as CONSUMIDO
FROM cheqdet venta
INNER JOIN cheques ON venta.foliodet = cheques.folio 
INNER JOIN costos ON costos.idproducto = venta.idproducto
INNER JOIN recetasalmacenes RC ON RC.idproducto = venta.idproducto 
    AND RC.idinsumo = COSTOS.idinsumo 
    AND cheques.idarearestaurant = RC.idarearestaurant 
    AND cheques.idempresa = RC.idempresa
INNER JOIN almacen AL ON AL.idalmacen = RC.idalmacen
INNER JOIN insumos receta ON receta.idinsumo = costos.idinsumo
INNER JOIN turnos ON turnos.idturno = cheques.idturno
WHERE turnos.APERTURA BETWEEN 
    CONVERT(datetime, CONVERT(nvarchar(30),'DD/MM/YYYY 00:00:00',103),103) 
    AND CONVERT(datetime, CONVERT(nvarchar(30),'DD/MM/YYYY 23:59:59',103),103)
  AND cheques.cancelado = 0
  AND AL.nombre LIKE '%ALMACEN%'
GROUP BY RTRIM(LTRIM(receta.idinsumo))
```

**Nota importante sobre fechas de ventas:**
- fecha_ini: Día del inventario INICIAL a las 00:00:00
- fecha_fin: Día ANTERIOR al inventario FINAL a las 23:59:59
- Esto asegura incluir todos los turnos del período correcto

---

## Archivos Principales

### Backend
- `/app/backend/server.py` - API principal (~3400 líneas)
  - Líneas 1908-1965: Consulta catálogo productos
  - Líneas 1975-2010: Consulta inventarios
  - Líneas 2060-2095: Consulta movimientos
  - Líneas 2115-2170: Consulta ventas (con lógica de fechas corregida)

### Frontend
- `/app/frontend/src/pages/Reportes.js` - UI de reportes (~1400 líneas)
  - Manejo de sessionStorage para persistencia
  - Modales de detalle de movimientos y ventas
  - Exportación a Excel/PDF

---

## Servidores Configurados

| Nombre | Tipo | Host | Base de Datos |
|--------|------|------|---------------|
| ManagmentPro | MPRO | 54.39.104.176:1433 | CENTRAL2020 |
| Cienfuegos | SoftRestaurant | (configurado) | softrestaurant12 |
| LA ESTELAR | SoftRestaurant | serverestelar.ddns.net:6669 | softrestaurant12 |

---

## Tablas SoftRestaurant (Referencia)

### Catálogo
- `insumos` + `insumosdetalle` (inventariable=1)
- `insumospresentaciones` + `insumospresentacionesdetalle`
- `gruposi` / `gruposiclasificacion`

### Inventario Físico
- `invfisico` - Cabecera
- `invfisicomovtos` - Detalle (idinsumo o idpresentacion)

### Movimientos
- `movsinv` - Movimientos de INSUMOS
- `movtosalmacen` - Movimientos de PRESENTACIONES

### Ventas
- `cheques` / `cheqdet` - Ventas cerradas
- `temcheques` / `temcheqdet` - Ventas temporales (puede no existir)
- `costos` - Recetas
- `recetasalmacenes` - Relación producto-insumo-almacén
- `turnos` - Para filtrar por fecha de apertura

---

## Pendientes / Backlog

### P0 - COMPLETADOS (27 Mar 2026)
1. ~~**MPRO dividido por sucursal**~~ ✅ - Tablero Ejecutivo ahora muestra cada sucursal por separado
2. ~~**Drill-down en KPIs**~~ ✅ - Doble click para ver detalle de movimientos

### P1 - Próximos
1. **Bug routing `/explorador-bd`** - Redirige al Dashboard (pendiente arreglar)
2. **Presupuestos** - Comparativa vs presupuesto (existe en análisis e inventarios)
3. **Ventas sin inflación** - Parametrizable el % de inflación (precios constantes)
4. **Filtros por grupo, zona, permisos** - Especialmente para MPRO y relación usuarios

5. **Módulo Compras - Fases 2-6** - Continuar desarrollo del Mini-ERP de compras
   - Fase 2: Inventario final inteligente
   - Fase 3: Captura y comparación de pedidos
   - Fase 4: Autorización con cobro de diferencias
   - Fase 5: Alertas y días de proveedor
   - Fase 6: Lógica de compra por período

6. **Reporte "Insumos Pendientes por Descargar"** - Nuevo reporte solicitado
   - Insumos consumidos según ventas vs existencias
   - Solo para almacenes de consumo

### P2 - Mejoras
7. Exportación a PDF (verificar funcionamiento - reportada rota)
8. Envío de reportes por correo electrónico
9. Productos con movimientos pero sin inventario físico
10. Filtro por comentarios de captura física e Inventario Selectivo

### P3 - Futuros
11. Módulo Rentabilidad - OpenTable, conciliación PAX
12. Módulo CRM (Leads, estado de cuenta)
13. Módulo Comisionistas, Bonificaciones, Convenios
14. Integración con WhatsApp para notificaciones
15. Migrar Portal de Proveedores
16. Migrar Bitácora de Activos

---

## Historial de Cambios

### 27 Mar 2026 - TABLERO EJECUTIVO + DRILL-DOWN ✅
- ✅ **MPRO dividido por sucursal**: Tablero Ejecutivo muestra 130° QUERETARO, ORIGEN, EDARSA separados
- ✅ **Nueva función `get_kpis_mpro_por_sucursal`**: GROUP BY Sc_Cve_Sucursal para dividir datos
- ✅ **Drill-down en KPIs**: Doble click en tarjetas de Comercial muestra detalle de movimientos
- ✅ **Endpoint `/api/comercial/detalle-movimientos/{server_id}`**: Paginación de cheques/facturas
- ✅ **5 unidades en Tablero**: 130° QUERETARO, ORIGEN, EDARSA (MPRO) + Cienfuegos, LA ESTELAR (Soft)

### 27 Mar 2026 - EDARSA HUB + BUGFIXES ✅
- ✅ **Renombre del sistema**: "Sistema Inventarios" → "Edarsa Hub"
- ✅ **Fix Bug Consumos en Ceros**: Ahora `es_bodega` solo es TRUE si TODOS los almacenes son bodegas (antes cualquier bodega lo marcaba como TRUE)
- ✅ **Lista de Requisiciones**: Cambiado de `Pedido`/`Orden_Compra` a `REQUISICION_COMPRA` con estado `PXA` (Por Autorizar)
- ✅ **Soporte SoftRestaurant**: Agregada consulta de pedidos sin autorizar para Soft
- ✅ **Comparación 1:1**: Cuando se compara con un folio de requisición, SOLO muestra los productos de ese folio específico
- ✅ **UI mejorada**: Dropdown de requisiciones muestra comentario del pedido

### 27 Mar 2026 - MÓDULO AUTORIZACIÓN DE COMPRAS - FASE 1 ✅
- ✅ Nuevo módulo "Autorización de Compras" agregado al menú lateral
- ✅ Ruta `/compras` enlazada en App.js y Layout.js
- ✅ Endpoint `/api/compras/calculo-pedido` implementado para MPRO
- ✅ Lógica de cálculo: Inv. Físico + Compras - Consumos = Inv. Teórico
- ✅ Obtención de compras desde tabla `Movimiento` (filtro tipos de entrada)
- ✅ Para bodegas: salidas por traspaso como "consumo"
- ✅ Para almacenes de consumo: ventas calculadas por recetas (Producto_Kit)
- ✅ Detección de productos sin inventario físico (flag `Sin_Inventario_Fisico`)
- ✅ UI permite ingreso manual de existencias cuando no hay inv. físico
- ✅ KPIs: Total productos, A pedir, Costo total, Stock bajo, Sin inv. físico
- ✅ Información del folio de inventario físico y fecha
- ✅ Tabla con todas las columnas del cálculo de pedido

### 24 Mar 2026 - REPORTE MPRO IMPLEMENTADO
- ✅ Implementada lógica de INSUMOS vs PRESENTACIONES para MPRO
- ✅ El reporte muestra INSUMOS (depto 0007) que tienen presentaciones
- ✅ El reporte muestra COMPRAS que no son presentación de ningún insumo
- ✅ Ventas calculadas usando `Producto_Kit` (recetas)
- ✅ Detección de errores de captura (presentaciones capturadas incorrectamente)
- ✅ Frontend actualizado para mostrar errores de captura

### 23 Mar 2026 - CHECKPOINT ESTABLE SOFTRESTAURANT
- ✅ Corregido doble prefijo en códigos (BB130009 → B130009)
- ✅ Corregido cálculo de ventas para almacenes de consumo
- ✅ Corregido filtro de fechas de ventas (incluye todos los turnos del período)
- ✅ Modal detalle de movimientos funcionando
- ✅ Modal detalle de ventas funcionando
- ✅ Manejo robusto de sessionStorage en frontend

### Correcciones Técnicas Aplicadas:
1. Códigos de producto: Usar código natural de BD (ya incluye prefijo)
2. Fechas de ventas: 
   - Inicio: día inventario inicial 00:00:00
   - Fin: día ANTERIOR a inventario final 23:59:59
3. Tablas temporales: Manejo graceful si no existen
4. SessionStorage: Validación y limpieza de datos corruptos

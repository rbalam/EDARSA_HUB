# Sistema de Análisis de Inventarios - PRD

## Resumen del Producto
Aplicación web para analizar inventarios de múltiples sucursales. Los datos se obtienen de diferentes servidores SQL Server con distintas estructuras de bases de datos (ManagmentPro y SoftRestaurant).

## Arquitectura Técnica

### Stack
- **Frontend**: React, TailwindCSS, Shadcn UI, Recharts
- **Backend**: FastAPI, Python
- **Base de Datos**: MongoDB (configuración), SQL Server (datos de inventario)
- **Bibliotecas SQL**: pytds (principal), pymssql (fallback)

### Endpoints Principales
- `POST /api/auth/login` - Autenticación
- `GET/POST /api/servers` - CRUD de servidores
- `GET /api/servers/{id}/almacenes-softrestaurant` - Lista de almacenes para SoftRestaurant
- `GET /api/servers/{id}/inventarios` - Lista de inventarios físicos
- `GET /api/servers/{id}/report-filters` - Obtiene filtros (categorías, familias, subfamilias)
- `POST /api/reports/inventory-analysis` - Análisis de inventario principal
- `POST /api/reports/movement-details` - Detalle de movimientos por producto
- `POST /api/reports/sales-details` - Detalle de ventas por producto
- `POST /api/reports/export/excel` - Exportar Excel

## Lo Implementado

### 2026-03-14 - Soporte Completo para SoftRestaurant (Almacenes de Bodega y Consumo)
**CORRECCIÓN CRÍTICA**: El reporte ahora funciona para AMBOS tipos de almacén en SoftRestaurant:

#### Almacén Tipo 1 (CONSUMO - ej. "100 PRODUCCION"):
- Usa `idinsumo` directamente en `invfisicomovtos`
- Movimientos desde tabla `movsinv`
- Ventas calculadas desde `explosioninsumosdetalle` (si hay recetas configuradas)

#### Almacén Tipo 2 (BODEGA/PRESENTACIONES - ej. "001 BODEGA"):
- Usa `idpresentacion` en `invfisicomovtos` → se relaciona con `insumospresentaciones` → `insumos`
- Movimientos desde tabla `movtosalmacen`
- NO tiene ventas (es almacén de almacenamiento, no consumo)

**Resultados Verificados:**
- **001 BODEGA (folio 141 vs 149)**: 10,156 productos, 8,591 con costo, 3,794 con movimientos
- **100 PRODUCCION (folio 143 vs 150)**: 124 productos, 32 con costo, 23 con movimientos

### 2026-03-14 - Correcciones SQL Previas
- Columnas inexistentes eliminadas: `unidaddecompra`, `costounitario`
- Tabla de movimientos corregida: `movimientosinventario` → `movsinv` (para consumo)
- Problema de espacios en `idalmacen`: Agregado `RTRIM()` para comparaciones
- Fechas auto-calculadas desde los folios de inventario seleccionados

### Sesiones Anteriores
- Dashboard sin carga automática (resuelve timeout en login)
- Filtros multiselección (Clasificación, Grupos, SubGrupos para SoftRestaurant)
- Modal de detalle con doble clic en Movimientos/Ventas
- Sistema de permisos granular
- Excel con formato profesional

## Tablas de SoftRestaurant

### Catálogo
- `insumos` - Catálogo de insumos (idinsumo, descripcion, unidad)
- `insumospresentaciones` - Presentaciones de insumos (idinsumospresentaciones, idinsumo)
- `insumosdetalle` - Detalle con costos (idinsumo, costo)
- `gruposi` - Grupos de insumos (subfamilia)
- `gruposiclasificacion` - Clasificación de grupos (familia)

### Inventario Físico
- `invfisico` - Cabecera de inventarios (folio, fecha, idalmacen1)
- `invfisicomovtos` - Detalle:
  - Para consumo: usa `idinsumo`
  - Para bodega: usa `idpresentacion` → `insumospresentaciones`

### Movimientos
- `movsinv` - Para almacenes de CONSUMO (tipo=1) con `idinsumo`
- `movtosalmacen` - Para almacenes de BODEGA (tipo=2) con `idinsumospresentaciones`

### Almacenes
- `almacen` - Catálogo con campo `tipo`:
  - 1 = Consumo (tiene ventas)
  - 2 = Presentaciones/Bodega (sin ventas)

### Ventas (para almacenes de consumo)
- `cheques` / `cheqdet` - Ventas de productos
- `explosioninsumosdetalle` - Recetas (relaciona productos vendidos con insumos consumidos)

## Pendiente / Backlog

### P1 - Alta Prioridad
- [ ] Corregir exportación a Excel/PDF (el archivo no se descarga)

### P2 - Media Prioridad
- [ ] Paginación del reporte de inventario (10,000+ registros)

### P3 - Baja Prioridad / Futuro
- [ ] Envío de reportes por correo electrónico
- [ ] Modularización del backend (server.py tiene >3000 líneas)
- [ ] Limpieza de endpoints de debug

## Credenciales de Prueba

### Aplicación
- **Admin**: `admin@inventario.com` / `admin123`

### Servidores SQL
- **ManagmentPro**: `54.39.104.176:1433`, DB: `CENTRAL2020`
- **LA ESTELAR**: `serverestelar.ddns.net,6669`, DB: `softrestaurant12`, User: `STLectura`

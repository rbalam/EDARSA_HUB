# Sistema de Análisis de Inventarios - PRD

## Resumen del Producto
Aplicación web para analizar inventarios de múltiples sucursales. Los datos se obtienen de diferentes servidores SQL Server con distintas estructuras de bases de datos (ManagmentPro y SoftRestaurant).

## Arquitectura Técnica

### Stack
- **Frontend**: React, TailwindCSS, Shadcn UI, Recharts
- **Backend**: FastAPI, Python
- **Base de Datos**: MongoDB (configuración), SQL Server (datos de inventario)
- **Bibliotecas SQL**: pytds (principal)

### Endpoints Principales
- `POST /api/auth/login` - Autenticación
- `POST /api/reports/inventory-analysis` - Análisis de inventario principal
- `GET /api/servers/{id}/almacenes-softrestaurant` - Lista de almacenes
- `GET /api/servers/{id}/inventarios` - Lista de inventarios físicos

## Lo Implementado

### 2026-03-14 - Reporte SoftRestaurant Corregido (Basado en consultas Power BI)

#### Lógica Correcta Implementada:

**1. PRODUCTOS (Catálogo)**
- UNION de INSUMOS inventariables (`insumosdetalle.inventariable = 1`) + PRESENTACIONES
- Código con prefijo: `LEFT(clasificacion.descripcion,1) + RTRIM(LTRIM(id))`
- Ejemplo: clasificación "ALIMENTOS" + idinsumo "100043" = **"A100043"**

**2. INVENTARIOS (invfisicomovtos)**
- Una sola consulta que maneja AMBOS tipos:
  - Si `idinsumo = ''` → Es PRESENTACIÓN, usa `idpresentacion`
  - Si `idinsumo <> ''` → Es INSUMO, usa `idinsumo`
- El código usa el mismo formato con prefijo de clasificación

**3. MOVIMIENTOS**
- UNION de dos tablas:
  - `movsinv` → Para INSUMOS
  - `movtosalmacen` → Para PRESENTACIONES
- Ambas se consultan para TODOS los almacenes

**4. VENTAS (Solo almacenes de consumo tipo=1)**
- Usa `cheqdet` + `cheques` + `costos` + `recetasalmacenes`
- Calcula consumos de insumos basado en recetas

**5. ALMACENES**
- `tipo = 1` → INSUMO (almacén de consumo, tiene ventas)
- `tipo != 1` → PRESENTACIÓN (almacén de bodega, sin ventas)

#### Resultados Verificados:
- **001 BODEGA** (folio 141 vs 149): 1,524 productos únicos, 1,273 con costo, 333 con movimientos
- **100 PRODUCCION** (folio 143 vs 150): 124 productos únicos, 46 con costo, 53 con movimientos

## Tablas de SoftRestaurant

### Catálogo
- `insumos` + `insumosdetalle` (filtrar `inventariable = 1`)
- `insumospresentaciones` + `insumospresentacionesdetalle`
- `gruposi` - Grupos de insumos
- `gruposiclasificacion` - Clasificación de grupos (para prefijo del código)

### Inventario Físico
- `invfisico` - Cabecera de inventarios
- `invfisicomovtos` - Detalle (usa `idinsumo` o `idpresentacion` según el tipo)

### Movimientos
- `movsinv` - Para INSUMOS
- `movtosalmacen` - Para PRESENTACIONES

### Ventas
- `cheques` / `cheqdet` - Ventas de productos
- `costos` - Costos de recetas
- `recetasalmacenes` - Relación producto-insumo-almacén

## Pendiente / Backlog

### P1 - Alta Prioridad
- [ ] Corregir exportación a Excel/PDF (el archivo no se descarga)

### P2 - Media Prioridad
- [ ] Paginación del reporte de inventario (1,500+ registros)

### P3 - Baja Prioridad / Futuro
- [ ] Envío de reportes por correo electrónico
- [ ] Modularización del backend

## Credenciales de Prueba

### Aplicación
- **Admin**: `admin@inventario.com` / `admin123`

### Servidores SQL
- **LA ESTELAR**: `serverestelar.ddns.net,6669`, DB: `softrestaurant12`, User: `STLectura`

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
- `POST /api/reports/movement-details` - Detalle de movimientos (PENDIENTE CORREGIR)
- `POST /api/reports/sales-details` - Detalle de ventas (PENDIENTE CORREGIR)
- `GET /api/servers/{id}/almacenes-softrestaurant` - Lista de almacenes
- `GET /api/servers/{id}/inventarios` - Lista de inventarios físicos

## Lo Implementado (2026-03-14)

### Reporte SoftRestaurant - FUNCIONANDO ✅
Basado en las consultas de Power BI del usuario:

**1. PRODUCTOS (Catálogo)**
- UNION de INSUMOS inventariables (`insumosdetalle.inventariable = 1`) + PRESENTACIONES de insumos inventariables
- Código con prefijo: `LEFT(clasificacion.descripcion,1) + RTRIM(LTRIM(id))`
- Ejemplo: clasificación "ALIMENTOS" + idinsumo "100043" = **"A100043"**

**2. INVENTARIOS (invfisicomovtos)**
- Una sola consulta que maneja AMBOS tipos:
  - Si `idinsumo = ''` → Es PRESENTACIÓN, usa `idpresentacion`
  - Si `idinsumo <> ''` → Es INSUMO, usa `idinsumo`
- **FILTRO**: Solo productos con `existencia != 0` en al menos un inventario

**3. MOVIMIENTOS**
- UNION de dos tablas:
  - `movsinv` → Para INSUMOS
  - `movtosalmacen` → Para PRESENTACIONES
- Ambas se consultan para TODOS los almacenes

**4. VENTAS (Solo almacenes de consumo tipo=1)**
- Usa `cheqdet` + `cheques` + `costos` + `recetasalmacenes`

**5. ALMACENES**
- `tipo = 1` → INSUMO (almacén de consumo, tiene ventas)
- `tipo != 1` → PRESENTACIÓN (almacén de bodega, sin ventas)

### Resultados Verificados:
- **001 BODEGA** (folio 141 vs 149): 346 productos únicos ✅
- **100 PRODUCCION** (folio 143 vs 150): 21 productos únicos ✅

---

## 🔴 PENDIENTES PARA SIGUIENTE SESIÓN

### P0 - CRÍTICOS (Funcionalidades rotas)

#### 1. Detalle de Ventas NO funciona (SoftRestaurant y MPRO)
- **Síntoma**: Al hacer doble clic en columna "Ventas" no abre el modal de detalle
- **Endpoint**: `POST /api/reports/sales-details`
- **Archivos**: `/app/backend/server.py`, `/app/frontend/src/pages/Reportes.js`
- **Acción**: Revisar endpoint y frontend para ambos sistemas

#### 2. Detalle de Movimientos INCORRECTO en MPRO
- **Síntoma**: La información sale duplicada/triplicada/cuadruplicada
- **Causa probable**: Falta filtrar por el rango de fechas o hay JOINs incorrectos que multiplican registros
- **Endpoint**: `POST /api/reports/movement-details`
- **Acción**: Revisar consulta SQL para MPRO, agregar filtros de fecha y verificar JOINs

#### 3. Detalle de Movimientos NO funciona en SoftRestaurant
- **Síntoma**: No abre el modal al hacer doble clic
- **Endpoint**: `POST /api/reports/movement-details`
- **Acción**: Revisar endpoint y frontend para SoftRestaurant

### P1 - IMPORTANTES

#### 4. Dashboard MPRO no muestra información
- **Síntoma**: El dashboard no carga datos para servidores MPRO
- **Archivo**: `/app/backend/server.py` (endpoints de dashboard)
- **Acción**: Revisar consultas SQL del dashboard para MPRO

#### 5. Dashboard muestra productos NO inventariables
- **Síntoma**: Aparecen productos de tipo "servicio" en lugar de solo inventariables
- **Aplica a**: SoftRestaurant Y MPRO
- **Acción**: 
  - SoftRestaurant: Agregar filtro `insumosdetalle.inventariable = 1`
  - MPRO: Agregar filtro equivalente (probablemente en tabla de productos)

### P2 - PENDIENTES ANTERIORES

#### 6. Exportación a Excel/PDF no descarga archivo
- **Síntoma**: Mensaje de éxito pero el archivo no se descarga
- **Endpoint**: `POST /api/reports/export/excel`
- **Acción**: Revisar headers `Content-Disposition` y manejo de blob en frontend

---

## Tablas de SoftRestaurant (Referencia)

### Catálogo
- `insumos` + `insumosdetalle` (filtrar `inventariable = 1`)
- `insumospresentaciones` + `insumospresentacionesdetalle`
- `gruposi` - Grupos de insumos
- `gruposiclasificacion` - Clasificación de grupos

### Inventario Físico
- `invfisico` - Cabecera de inventarios
- `invfisicomovtos` - Detalle (usa `idinsumo` o `idpresentacion`)

### Movimientos
- `movsinv` - Para INSUMOS
- `movtosalmacen` - Para PRESENTACIONES

### Ventas
- `cheques` / `cheqdet` - Ventas de productos
- `costos` - Costos de recetas
- `recetasalmacenes` - Relación producto-insumo-almacén

---

## Credenciales de Prueba

### Aplicación
- **Admin**: `admin@inventario.com` / `admin123`

### Servidores SQL
- **ManagmentPro**: `54.39.104.176:1433`, DB: `CENTRAL2020`, User: `HRLectura`
- **LA ESTELAR** (SoftRestaurant): `serverestelar.ddns.net,6669`, DB: `softrestaurant12`, User: `STLectura`

---

## Archivos Clave

- `/app/backend/server.py` - Backend principal (>3000 líneas)
- `/app/frontend/src/pages/Reportes.js` - UI de reportes
- `/app/frontend/src/pages/Dashboard.js` - UI de dashboard

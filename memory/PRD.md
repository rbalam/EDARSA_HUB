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
- `POST /api/reports/movement-details` - Detalle de movimientos
- `POST /api/reports/sales-details` - Detalle de ventas
- `GET /api/servers/{id}/almacenes-softrestaurant` - Lista de almacenes
- `GET /api/servers/{id}/inventarios` - Lista de inventarios físicos

---

## ✅ RESUELTO (2026-03-23)

### Bug Crítico: Doble Prefijo en Códigos de Producto (SoftRestaurant)
- **Problema**: Los códigos de productos INSUMOS se mostraban con prefijo duplicado (ej: "BB130009" en lugar de "B130009")
- **Causa Raíz**: La tabla `insumos` ya almacena los códigos CON el prefijo incluido (A100043, B130009, etc.), pero las consultas SQL agregaban otro prefijo con `LEFT(clasificacion.descripcion,1) + idinsumo`
- **Solución**: Se eliminó la concatenación de prefijo en las consultas de:
  - Catálogo de productos (línea ~1901)
  - Inventarios (línea ~1965)
  - Movimientos (línea ~2053)
  - Ventas (línea ~2105)
- **Verificación**: 
  - Backend: 9/9 tests pasaron
  - Frontend: E2E testing verificado
  - Producto B130009 (RON BACARDI BLANCO 700 ML) muestra código correcto

---

## Funcionalidades Implementadas

### Reporte SoftRestaurant - FUNCIONANDO ✅
**1. PRODUCTOS (Catálogo)**
- UNION de INSUMOS inventariables + PRESENTACIONES de insumos inventariables
- Código natural desde la BD (ya incluye prefijo): `RTRIM(LTRIM(idinsumo))` o `RTRIM(LTRIM(idinsumospresentaciones))`

**2. INVENTARIOS (invfisicomovtos)**
- Maneja AMBOS tipos:
  - Si `idinsumo = ''` → Es PRESENTACIÓN, usa `idpresentacion`
  - Si `idinsumo <> ''` → Es INSUMO, usa `idinsumo`
- Filtro: Solo productos con `existencia != 0`

**3. MOVIMIENTOS**
- UNION de `movsinv` (INSUMOS) + `movtosalmacen` (PRESENTACIONES)
- Filtrado por `tipos_movimiento` del servidor (idconcepto)

**4. VENTAS (Solo almacenes de consumo tipo=1)**
- Usa `cheqdet` + `cheques` + `costos` + `recetasalmacenes`

**5. Modal Detalle de Movimientos** ✅
- Funciona al hacer doble clic en columna "Movimientos"
- Muestra: folio, fecha, cantidad, tipo, descripción, almacén

---

## 🔴 PENDIENTES

### P1 - IMPORTANTES

#### 1. Detalle de Ventas NO funciona
- **Síntoma**: Modal no se abre o error al hacer doble clic en columna "Ventas"
- **Endpoint**: `POST /api/reports/sales-details`
- **Error conocido**: "Invalid column name 'idinsumospresentaciones'" en tabla recetasalmacenes

#### 2. Verificar cálculo de Movimientos para almacenes de consumo
- **Almacén**: 200 BARRA
- **Requisito**: Los movimientos deben filtrar por `idconcepto` configurados en el servidor

#### 3. Ventas para almacenes de consumo
- **Verificar**: La consulta de ventas implementada funciona correctamente

### P2 - PENDIENTES

#### 4. Dashboard MPRO vacío
- El dashboard no carga datos para servidores ManagmentPro

#### 5. Detalle de Movimientos INCORRECTO en MPRO
- Información duplicada/triplicada

#### 6. Exportación a Excel/PDF
- Mensaje de éxito pero archivo no se descarga

### P3 - FUTUROS

#### 7. Dashboard muestra productos NO inventariables
- Filtrar por `inventariable = 1`

#### 8. Envío de reportes por correo electrónico

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
- `/app/backend/tests/test_softrestaurant_inventory.py` - Tests automatizados

---

## Test Reports
- `/app/test_reports/iteration_8.json` - Último reporte de testing (2026-03-23)

# Sistema de Análisis de Inventarios - PRD

## CHECKPOINT ESTABLE - 23 Marzo 2026
> **Todo el reporte de Análisis de Inventarios está funcionando correctamente.**
> Este es el punto de referencia para rollback si algo falla en futuras actualizaciones.

---

## Resumen del Producto
Aplicación web para analizar inventarios de múltiples sucursales. Los datos se obtienen de servidores SQL Server con diferentes estructuras (ManagmentPro y SoftRestaurant).

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

## FUNCIONALIDADES VERIFICADAS (23 Mar 2026)

### 1. Reporte Análisis de Inventarios - SoftRestaurant

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

### 2. Modal Detalle de Movimientos - FUNCIONANDO
- Muestra detalle por producto al hacer doble clic
- Incluye: folio, fecha, cantidad, tipo, descripción

### 3. Modal Detalle de Ventas - FUNCIONANDO  
- Muestra detalle de ventas por producto
- Incluye: folio, fecha, cantidad, producto vendido

### 4. Filtros - FUNCIONANDO
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

### P1 - Próximos
1. **Reporte "Insumos Pendientes por Descargar"** - Nuevo reporte solicitado
   - Insumos consumidos según ventas vs existencias
   - Solo para almacenes de consumo
   - Posible envío automático cuando informan que "traspasos están listos"

### P2 - Mejoras
2. Dashboard MPRO vacío (timeout en consultas largas)
3. Exportación a Excel/PDF (verificar funcionamiento)

### P3 - Futuros
4. Envío de reportes por correo electrónico
5. Filtrar productos no inventariables en dashboards
6. Integración con WhatsApp para notificaciones

---

## Historial de Cambios

### 23 Mar 2026 - CHECKPOINT ESTABLE
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

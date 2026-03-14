# Sistema de Análisis de Inventarios - PRD

## Resumen del Producto
Aplicación web para analizar inventarios de múltiples sucursales, cada una con sus propios almacenes. Los datos se obtienen de diferentes servidores SQL Server con distintas estructuras de bases de datos (ManagmentPro y SoftRestaurant).

## Requisitos del Producto

### Usuarios y Roles
- **Administrador**: Acceso completo, gestión de usuarios, servidores y configuraciones
- **Supervisor**: Acceso a reportes y visualización de datos
- **Usuario**: Acceso limitado a reportes asignados

### Funcionalidades Core
1. **Gestión de Servidores SQL**: Agregar, editar, eliminar conexiones a bases de datos
2. **Análisis de Inventario**: Cálculo de diferencias usando la fórmula:
   - `Inventario teórico = Inventario inicial + Movimientos - Ventas`
   - `Diferencias = Inventario teórico - Inventario final`
3. **Filtros Configurables**: Por tipos de movimiento, categorías y departamentos
4. **Exportación**: Excel (con formato profesional) y PDF
5. **Catálogo de Consultas**: Consultas SQL centralizadas y reutilizables
6. **Configuración Flexible de Consultas SQL**: Asistente para configurar consultas personalizadas por servidor
7. **Sistema de Permisos Granular**: Asignación de acceso a servidores, sucursales y almacenes por usuario

### Sistemas Soportados
- ManagmentPro (MPRO)
- SoftRestaurant
- Otros sistemas (configurables mediante consultas personalizadas)

## Arquitectura Técnica

### Stack
- **Frontend**: React, TailwindCSS, Shadcn UI, Recharts
- **Backend**: FastAPI, Python
- **Base de Datos**: MongoDB (configuración), SQL Server (datos de inventario)
- **Bibliotecas SQL**: pytds (principal), pymssql (fallback)
- **Excel**: openpyxl con estilos profesionales

### Endpoints Principales
- `POST /api/auth/login` - Autenticación
- `GET/POST /api/servers` - CRUD de servidores (filtrado por permisos)
- `GET /api/servers/{id}/sucursales` - Lista de sucursales (filtrada por permisos)
- `GET /api/servers/{id}/almacenes-softrestaurant` - Lista de almacenes para SoftRestaurant
- `GET /api/servers/{id}/inventarios` - Lista de inventarios físicos
- `GET /api/servers/{id}/report-filters` - Obtiene categorías, familias, subfamilias para filtros
- `POST /api/reports/inventory-analysis` - Análisis de inventario (acepta filtros)
- `POST /api/reports/movement-details` - Detalle de movimientos por producto
- `POST /api/reports/sales-details` - Detalle de ventas por producto
- `POST /api/reports/export/excel` - Exportar Excel con formato
- `GET /api/servers/{id}/queries` - Estado de consultas configuradas
- `PUT /api/users/{id}/permissions` - Actualizar permisos de usuario
- `GET /api/company-groups` - Obtener grupos de empresas

### Modelo de Permisos
```
User {
  company_group: string          // Grupo de empresa (ej: "Grupo Norte")
  allowed_servers: string[]      // IDs de servidores permitidos
  allowed_sucursales: {          // Sucursales específicas por servidor
    [server_id]: string[]
  }
  allowed_warehouses: {          // Almacenes específicos por servidor
    [server_id]: string[]
  }
}
```

## Lo Implementado

### 2026-03-14 - Corrección Completa de SoftRestaurant
- **Backend - Consultas SQL Corregidas**:
  - Tabla `movsinv` identificada y usada correctamente para movimientos de insumos
  - Tabla `insumosdetalle` usada para obtener costos de insumos
  - Columna `idalmacen` tiene espacios - se usa `RTRIM()` para comparaciones
  - Fechas se calculan automáticamente desde los folios de inventario
  - Ventas de insumos requieren recetas en `explosioninsumosdetalle` (si no hay, ventas = 0)
- **Resultado**: Reporte genera correctamente 124 productos con:
  - 32 productos con costo > 0
  - 23 productos con movimientos
  - 31 productos con diferencias

### 2026-03-14 - Filtros y Análisis Completo para SoftRestaurant
- **Backend - Filtros para SoftRestaurant**:
  - Clasificación (clasificacionventa): 1=ALIMENTOS, 2=BEBIDAS, 3=OTROS (equivale a Categoría)
  - Grupos (gruposiclasificacion): Grupos disponibles (equivale a Familia)
  - SubGrupos (gruposi): SubFamilias disponibles
- **Backend - Análisis de Inventario con Filtros**:
  - Los filtros se aplican a la consulta SQL correctamente
  - Resultado incluye: Categoría, Familia, SubFamilia, Código, Producto, etc.
- **Frontend - UI de Filtros para SoftRestaurant**:
  - Etiquetas adaptadas: Clasificación, Grupos, SubGrupos
  - Filtros visibles al seleccionar servidor SoftRestaurant

### 2026-03-13 - Correcciones Finales
- **Backend - Corregido error SQL en detalle de movimientos**: Removida columna `Mv_Observaciones` que no existe en MPRO
- **Backend - Corregido error SQL en Dashboard SoftRestaurant**: Removido filtro por columna `esinventariable` que no existe
- **Frontend - Restaurados filtros multiselección**: Categorías, Familias, SubFamilias funcionando correctamente

### 2026-03-13 - Optimización de Carga del Dashboard
- **Dashboard NO carga datos automáticamente al iniciar sesión**
- El usuario debe seleccionar manualmente un servidor para cargar los datos
- Esto elimina el bloqueo al iniciar sesión que causaba timeouts
- Nueva vista inicial con selector de servidor y mensaje informativo

### 2026-03-13 - Corrección de Ventas por Almacén (v2)
- **Backend - Lógica de Ventas Corregida**:
  - **MPRO**: Solo almacenes con nombre que contenga "GENERAL", "CONSUMO" o "VENTA" muestran ventas
  - Almacenes como BODEGA, PRODUCCIÓN, etc. NO muestran ventas (ventas = 0)
  - Se obtiene el código de almacén junto con la sucursal para filtrar correctamente
- **Backend - Nuevos Endpoints de Detalle**:
  - `POST /api/reports/movement-details`: Detalle de movimientos
  - `POST /api/reports/sales-details`: Detalle de ventas
- **Frontend - Detalle con Doble Clic**:
  - Columnas Movimientos y Ventas son clickeables cuando valor ≠ 0
  - Doble clic abre un modal simple con el detalle completo
  - Modal simple con HTML/CSS para evitar errores de `removeChild`

### Sesiones Anteriores
- Corrección de conexión DDNS con pytds
- Asistente de configuración de consultas SQL
- Dashboard con gráficos interactivos
- Implementación de filtros configurables por servidor
- Catálogo de consultas centralizado
- Sistema de permisos granular
- Excel con formato profesional

## Pendiente / Backlog

### P1 - Alta Prioridad
- [ ] Corregir exportación a Excel/PDF (el archivo no se descarga)

### P2 - Media Prioridad
- [ ] Agregar paginación al reporte de inventario
- [ ] Integrar consultas configuradas con el reporte de análisis de inventario

### P3 - Baja Prioridad / Futuro
- [ ] Exportación PDF mejorada con el mismo formato que Excel
- [ ] Envío de reportes por correo electrónico
- [ ] Limpieza de endpoints de debug
- [ ] Modularización del backend (server.py es muy grande)

## Credenciales de Prueba

### Aplicación
- **Admin**: `admin@inventario.com` / `admin123` (acceso completo)
- **Test User**: `test@inventario.com` / `test123` (solo sucursales 0021, 0022 de ManagmentPro)

### Servidores SQL Configurados
- **ManagmentPro**: `54.39.104.176:1433`, DB: `CENTRAL2020`, User: `HRLectura`
- **Cienfuegos**: `servercienfuegos.ddns.net,6669\nationalsoft`, DB: `softrestaurant95pro`
- **LA ESTELAR**: `serverestelar.ddns.net,6669`, DB: `softrestaurant12`, User: `STLectura`

## Notas Técnicas

### Sistema de Permisos
- Administradores tienen acceso completo a todos los servidores/sucursales
- Usuarios normales solo ven servidores/sucursales en sus listas permitidas
- Si `allowed_sucursales[server_id]` está vacío, tiene acceso a todas las sucursales

### SoftRestaurant - Tablas Importantes
- `insumos` - Catálogo de insumos (idinsumo, descripcion, unidad)
- `insumosdetalle` - Detalle con costos (idinsumo, costo)
- `movsinv` - Movimientos de insumos (fecha, idinsumo, cantidad, costo, idalmacen)
- `invfisico` - Inventarios físicos (folio, fecha)
- `invfisicomovtos` - Detalle de inventarios físicos
- `explosioninsumosdetalle` - Recetas (para calcular ventas de insumos)
- `almacen` - Almacenes (tipo: 1=Consumo con ventas, 2=Presentaciones sin ventas)

### Formato Excel
- Usa openpyxl con estilos profesionales
- Detecta automáticamente columnas de porcentaje, moneda y números
- Ordenamiento automático por jerarquía de categorías
- Auto-filter permite filtrar datos sin macros

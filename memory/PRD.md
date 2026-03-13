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
- `GET /api/servers/{id}/report-filters` - Obtiene categorías, familias, subfamilias para filtros
- `POST /api/reports/inventory-analysis` - Análisis de inventario (acepta filtros: categorias, familias, subfamilias)
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

### 2025-03-13 - Correcciones Finales
- **Backend - Corregido error SQL en detalle de movimientos**: Removida columna `Mv_Observaciones` que no existe en MPRO
- **Backend - Corregido error SQL en Dashboard SoftRestaurant**: Removido filtro por columna `esinventariable` que no existe
- **Frontend - Restaurados filtros multiselección**: Categorías, Familias, SubFamilias funcionando correctamente

### 2025-03-13 - Optimización de Carga del Dashboard
- **Dashboard NO carga datos automáticamente al iniciar sesión**
- El usuario debe seleccionar manualmente un servidor para cargar los datos
- Esto elimina el bloqueo al iniciar sesión que causaba timeouts
- Nueva vista inicial con selector de servidor y mensaje informativo

### 2025-03-13 - Corrección de Ventas por Almacén (v2)
- **Backend - Lógica de Ventas Corregida**:
  - **MPRO**: Solo almacenes con nombre que contenga "GENERAL", "CONSUMO" o "VENTA" muestran ventas
  - Almacenes como BODEGA, PRODUCCIÓN, etc. NO muestran ventas (ventas = 0)
  - Se obtiene el código de almacén junto con la sucursal para filtrar correctamente
- **Backend - Nuevos Endpoints de Detalle**:
  - `POST /api/reports/movement-details`: Detalle de movimientos (folio, fecha, cantidad, tipo, descripción, almacén, observaciones)
  - `POST /api/reports/sales-details`: Detalle de ventas (folio, fecha, cantidad, tipo venta, producto vendido, precio unitario)
- **Frontend - Detalle con Doble Clic**:
  - Columnas Movimientos y Ventas son clickeables (color azul) cuando valor ≠ 0
  - Doble clic abre un modal simple (sin Radix Dialog) con el detalle completo
  - Tabla con información de folio, fecha, cantidad, tipo de movimiento/venta
  - Modal simple con HTML/CSS para evitar errores de `removeChild`

### 2025-03-13 - Mejoras en Reporte de Análisis de Inventarios
- **Backend**: Nuevo endpoint `GET /api/servers/{id}/report-filters` para obtener categorías, familias y subfamilias
- **Backend**: El endpoint `POST /api/reports/inventory-analysis` ahora acepta filtros adicionales (categorias, familias, subfamilias)
- **Backend**: Nuevas columnas en el resultado del análisis: `Valor_Real` y `Teorico`
  - `Valor_Real = (Inv_Inicial + Movimientos - Inv_Final) * Costo`
  - `Teorico = Ventas * Costo`
- **Frontend**: Renombrado "Análisis Completo de Inventario" → "Análisis de Inventarios"
- **Frontend**: Filtros multiselección de Categoría, Familia, SubFamilia (solo para MPRO)
  - Componentes Popover con Checkbox para selección múltiple
  - Tags de colores para mostrar filtros seleccionados
  - Botón "Limpiar selección" en cada dropdown
- **Testing**: 78% backend tests pasados (7/9), 100% frontend verificado

### 2025-03-12 - Permisos de Sucursales y Excel con Formato
- **Backend**: Nuevo campo `allowed_sucursales` en modelo User
- **Backend**: Función `filter_sucursales_by_permissions()` filtra sucursales según usuario
- **Backend**: Endpoint `/servers/{id}/sucursales` ahora filtra automáticamente
- **Frontend**: Página de Usuarios con selección de sucursales por servidor
- **Excel mejorado**:
  - Encabezado con título, sucursal, almacén, folios, período y fecha
  - Números con formato `#,##0.00` (2 decimales)
  - Moneda con formato `$#,##0.00`
  - Porcentajes con formato `0.00%`
  - Datos ordenados por Categoría → Familia → SubFamilia
  - Auto-filtro habilitado para filtrar en Excel
  - Panel congelado para mantener encabezados visibles
- **Testing**: 100% tests pasados (backend y frontend)

### 2025-03-12 - Sistema de Permisos de Usuario (P0)
- **Backend**: Campos `company_group`, `allowed_servers`, `allowed_warehouses`
- **Backend**: Filtrado automático de servidores en `GET /api/servers`
- **Backend**: Endpoint `PUT /api/users/{id}/permissions`
- **Frontend**: Diálogo de permisos con checkboxes para servidores/almacenes

### Sesiones Anteriores
- Corrección de conexión DDNS con pytds
- Asistente de configuración de consultas SQL
- Dashboard con gráficos interactivos
- Implementación de filtros configurables por servidor
- Catálogo de consultas centralizado

## Pendiente / Backlog

### P2 - Media Prioridad
- [ ] Agregar paginación al reporte de inventario
- [ ] Integrar consultas configuradas con el reporte de análisis de inventario

### P3 - Baja Prioridad / Futuro
- [ ] Exportación PDF mejorada con el mismo formato que Excel
- [ ] Envío de reportes por correo electrónico
- [ ] Limpieza de endpoints de debug

## Credenciales de Prueba

### Aplicación
- **Admin**: `admin@inventario.com` / `admin123` (acceso completo - ve 7 sucursales)
- **Test User**: `test@inventario.com` / `test123` (solo sucursales 0021, 0022 de ManagmentPro)

### Servidores SQL
- **ManagmentPro**: `54.39.104.176:1433`, DB: `CENTRAL2020`, User: `HRLectura`
- **Cienfuegos**: `servercienfuegos.ddns.net,6669\nationalsoft`, DB: `softrestaurant95pro`
- **LA ESTELAR**: `serverestelar.ddns.net,6669`, DB: `softrestaurant12`

## Notas Técnicas

### Sistema de Permisos
- Administradores tienen acceso completo a todos los servidores/sucursales
- Usuarios normales solo ven servidores/sucursales en sus listas permitidas
- Si `allowed_sucursales[server_id]` está vacío, tiene acceso a todas las sucursales
- Si tiene sucursales específicas, solo ve esas sucursales en reportes

### Formato Excel
- Usa openpyxl con estilos profesionales
- Detecta automáticamente columnas de porcentaje, moneda y números
- Ordenamiento automático por jerarquía de categorías
- Auto-filter permite filtrar datos sin macros

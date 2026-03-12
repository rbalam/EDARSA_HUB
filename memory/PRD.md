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
4. **Exportación**: Excel y PDF
5. **Catálogo de Consultas**: Consultas SQL centralizadas y reutilizables
6. **Configuración Flexible de Consultas SQL**: Asistente para configurar consultas personalizadas por servidor
7. **Sistema de Permisos**: Asignación granular de acceso a servidores y almacenes por usuario

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

### Endpoints Principales
- `POST /api/auth/login` - Autenticación
- `GET/POST /api/servers` - CRUD de servidores (filtrado por permisos)
- `POST /api/reports/inventory-analysis` - Análisis de inventario
- `GET /api/servers/{id}/queries` - Estado de consultas configuradas
- `POST /api/servers/{id}/queries/validate` - Validar consulta SQL
- `PUT /api/servers/{id}/queries/{type}` - Guardar consulta validada
- `PUT /api/users/{id}/permissions` - Actualizar permisos de usuario
- `GET /api/company-groups` - Obtener grupos de empresas

### Modelo de Permisos
```
User {
  company_group: string          // Grupo de empresa (ej: "Grupo Norte")
  allowed_servers: string[]      // IDs de servidores permitidos
  allowed_warehouses: {          // Almacenes específicos por servidor
    [server_id]: string[]
  }
}
```

## Lo Implementado

### 2025-03-12 - Sistema de Permisos de Usuario (P0)
- **Backend**: Nuevo modelo `UserPermissions` con campos `company_group`, `allowed_servers`, `allowed_warehouses`
- **Backend**: Funciones de verificación `user_has_server_access()` y `user_has_warehouse_access()`
- **Backend**: Filtrado automático de servidores en `GET /api/servers` según permisos
- **Backend**: Nuevo endpoint `PUT /api/users/{id}/permissions` para actualizar permisos
- **Backend**: Endpoint `GET /api/company-groups` para listar grupos de empresas
- **Frontend**: Página de Usuarios rediseñada con botón "Permisos" para cada usuario
- **Frontend**: Diálogo de permisos con selección de grupo, servidores y almacenes
- **Frontend**: Checkboxes para asignar acceso a servidores específicos
- **Testing**: 13/13 tests de backend pasados, sistema verificado funcionando

### 2025-03-12 - Correcciones Menores
- **Frontend (Reportes.js)**: Manejo defensivo de arrays null con `Array.isArray()`
- **Frontend (Usuarios.js)**: Corregido bug de SelectItem con valor vacío (usar "none" en lugar de "")

### 2025-03-12 - Dashboard de Inventarios con Gráficos Interactivos
- **Rediseño completo del Dashboard** con gráficos de análisis de inventarios
- **KPIs en tiempo real**: Costo Diferencias, Faltantes, Sobrantes, Items Revisados, Precision
- **Gráficos interactivos con Recharts y Zoom**
- **Soporte para SoftRestaurant y MPRO**

### Sesiones Anteriores
- Corrección de conexión DDNS con pytds
- Asistente de configuración de consultas SQL
- Implementación de filtros configurables por servidor
- Catálogo de consultas centralizado

## Pendiente / Backlog

### P1 - Alta Prioridad
- [ ] Verificar y corregir exportación Excel/PDF (reporta éxito pero no descarga)

### P2 - Media Prioridad
- [ ] Agregar paginación al reporte de inventario
- [ ] Integrar consultas configuradas con el reporte de análisis de inventario

### P3 - Baja Prioridad / Futuro
- [ ] Envío de reportes por correo electrónico
- [ ] Configuración por grupo de productos
- [ ] Filtrar dashboard por permisos de usuario (almacenes específicos)

## Credenciales de Prueba

### Aplicación
- **Admin**: `admin@inventario.com` / `admin123` (acceso completo)
- **Test User**: `test@inventario.com` / `test123` (solo acceso a Cienfuegos)

### Servidores SQL
- **ManagmentPro**: `54.39.104.176:1433`, DB: `CENTRAL2020`, User: `HRLectura`
- **Cienfuegos**: `servercienfuegos.ddns.net,6669\nationalsoft`, DB: `softrestaurant95pro`
- **LA ESTELAR**: `serverestelar.ddns.net,6669`, DB: `softrestaurant12`

## Notas Técnicas

### Sistema de Permisos
- Administradores tienen acceso completo a todos los servidores
- Usuarios normales solo ven servidores en su lista `allowed_servers`
- Si `allowed_warehouses[server_id]` está vacío, tiene acceso a todos los almacenes del servidor
- Si tiene almacenes específicos, solo ve esos almacenes

### Conexiones SQL Server
- `pytds` es más confiable para conexiones con DDNS y puertos no estándar
- `pymssql` funciona bien para conexiones estándar pero falla con formatos complejos
- Siempre usar el parser de host para manejar diferentes formatos de conexión

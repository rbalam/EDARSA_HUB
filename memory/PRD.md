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

### Sistemas Soportados
- ManagmentPro (MPRO)
- SoftRestaurant

## Arquitectura Técnica

### Stack
- **Frontend**: React, TailwindCSS, Shadcn UI
- **Backend**: FastAPI, Python
- **Base de Datos**: MongoDB (configuración), SQL Server (datos de inventario)
- **Bibliotecas SQL**: pytds (principal), pymssql (fallback)

### Endpoints Principales
- `POST /api/auth/login` - Autenticación
- `GET/POST /api/servers` - CRUD de servidores
- `POST /api/reports/inventory-analysis` - Análisis de inventario
- `GET /api/catalogo/consultas` - Catálogo de consultas
- `POST /api/debug/test-connection` - Prueba de conexiones

## Lo Implementado

### 2025-03-11 - Corrección de Conexión DDNS SoftRestaurant
- **Problema**: Las conexiones con formato DDNS especial (`hostname,puerto\instancia`) fallaban con pymssql
- **Solución**: Se integró la biblioteca `pytds` como conector principal con fallback a pymssql
- **Función**: `parse_sql_server_host()` ahora maneja múltiples formatos de cadena de conexión:
  - `hostname`
  - `hostname,port`
  - `hostname\instance`
  - `hostname,port\instance`
  - `hostname\instance,port`
- **Resultado**: Conexión exitosa a `servercienfuegos.ddns.net,6669\nationalsoft`

### Sesiones Anteriores
- Corrección del cálculo de análisis de inventario (estrategia de consultas separadas + Pandas)
- Implementación de filtros configurables por servidor
- Creación del catálogo de consultas centralizado
- Mejora de mensajes de feedback en exportación

## Pendiente / Backlog

### P1 - Alta Prioridad
- [ ] Verificar y corregir exportación Excel/PDF (no descarga archivos)
- [ ] Poblar catálogo de consultas con queries para MPRO y SoftRestaurant

### P2 - Media Prioridad
- [ ] Agregar paginación al reporte de inventario
- [ ] Eliminar endpoint de debug `/api/debug/test-queries`

### P3 - Baja Prioridad / Futuro
- [ ] Envío de reportes por correo electrónico
- [ ] Gráficos para visualización de datos
- [ ] Configuración por grupo de productos

## Credenciales de Prueba

### Aplicación
- Email: `admin@inventario.com`
- Password: `admin123`

### SoftRestaurant (Cienfuegos)
- Servidor: `servercienfuegos.ddns.net,6669\nationalsoft`
- Usuario: `CFLectura`
- Password: `National09`
- Base de datos: `softrestaurant95pro`

## Notas Técnicas

### Conexiones SQL Server
- `pytds` es más confiable para conexiones con DDNS y puertos no estándar
- `pymssql` funciona bien para conexiones estándar pero falla con formatos complejos
- Siempre usar el parser de host para manejar diferentes formatos de conexión

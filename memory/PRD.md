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

### Sistemas Soportados
- ManagmentPro (MPRO)
- SoftRestaurant
- Otros sistemas (configurables mediante consultas personalizadas)

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
- `GET /api/servers/{id}/queries` - Estado de consultas configuradas
- `POST /api/servers/{id}/queries/validate` - Validar consulta SQL
- `PUT /api/servers/{id}/queries/{type}` - Guardar consulta validada

## Lo Implementado

### 2025-03-12 - Dashboard de Inventarios con Gráficos Interactivos
- **Rediseño completo del Dashboard** con gráficos de análisis de inventarios
- **KPIs en tiempo real**: Costo Diferencias, Faltantes, Sobrantes, Items Revisados, Precision
- **Gráficos interactivos con Recharts y Zoom**:
  - Top 10 Faltantes por Costo
  - Top 10 Faltantes por Cantidad
  - Comparativo Inicio vs Fin de Mes por Almacén
  - Diferencias por Grupo/Categoría (pastel)
  - Resumen Acumulado por Almacén (barras apiladas)
- **Tabla detallada** por almacén con estado (OK/Atención/Crítico)
- **Backend**: Endpoint `/api/dashboard/inventory-summary` con análisis usando Pandas

### 2025-03-11 - Asistente de Configuración de Consultas SQL
- **Nuevo componente**: `QueryConfigWizard.js` - Asistente paso a paso para configurar consultas
- **Características**:
  - 3 pasos: Inventarios, Ventas, Movimientos/Entradas
  - Validación en tiempo real de consultas SQL
  - Verificación de columnas requeridas (`codigo`, `cantidad`)
  - Mapeo flexible de alias de columnas (ej: `idinsumo` → `codigo`)
  - Vista previa de datos de muestra
  - Indicadores visuales de estado (verde=válido, rojo=error)
  - Guardado de avance parcial (puede cerrar y continuar después)
- **Backend**: 
  - Nuevos endpoints para validar, guardar y consultar estado de queries
  - Sistema de alias para reconocer diferentes nombres de columnas
  - Modelo `ServerQueryConfig` para persistir consultas en MongoDB

### 2025-03-11 - Corrección de Conexión DDNS SoftRestaurant
- **Problema**: Las conexiones con formato DDNS especial (`hostname,puerto\instancia`) fallaban con pymssql
- **Solución**: Se integró la biblioteca `pytds` como conector principal con fallback a pymssql
- **Función**: `parse_sql_server_host()` ahora maneja múltiples formatos de cadena de conexión

### Sesiones Anteriores
- Corrección del cálculo de análisis de inventario (estrategia de consultas separadas + Pandas)
- Implementación de filtros configurables por servidor
- Creación del catálogo de consultas centralizado
- Mejora de mensajes de feedback en exportación

## Pendiente / Backlog

### P1 - Alta Prioridad
- [ ] Implementar dashboard para MPRO (actualmente solo funciona con SoftRestaurant)
- [ ] Verificar y corregir exportación Excel/PDF (no descarga archivos)

### P2 - Media Prioridad
- [ ] Agregar paginación al reporte de inventario
- [ ] Integrar consultas configuradas con el reporte de análisis de inventario

### P3 - Baja Prioridad / Futuro
- [ ] Envío de reportes por correo electrónico
- [ ] Configuración por grupo de productos
- [ ] Filtrar dashboard por permisos de usuario (sucursales específicas)

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

### Configuración de Consultas SQL
Cada servidor puede tener 3 consultas personalizadas:
1. **Inventario**: Para obtener inventario inicial/final. Columnas requeridas: `codigo`, `cantidad`
2. **Ventas**: Para obtener ventas del período. Columnas requeridas: `codigo`, `cantidad`
3. **Movimientos**: Para obtener entradas/traspasos/ajustes. Columnas requeridas: `codigo`, `cantidad`

El sistema reconoce alias comunes:
- `codigo`: clave, code, idinsumo, idproducto, sku, pr_cve_producto
- `cantidad`: qty, existencia, stock, unidades

### Conexiones SQL Server
- `pytds` es más confiable para conexiones con DDNS y puertos no estándar
- `pymssql` funciona bien para conexiones estándar pero falla con formatos complejos
- Siempre usar el parser de host para manejar diferentes formatos de conexión

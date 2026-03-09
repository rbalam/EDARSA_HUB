# Sistema de Inventarios - Documentación

## Información General

Este es un sistema completo de análisis de inventarios multi-sucursal que permite:
- Conectar múltiples servidores SQL Server
- Ejecutar consultas personalizadas por tipo de sistema (MPRO, SoftRestaurant, etc.)
- Generar reportes de inventario con cálculos automáticos
- Exportar a Excel y PDF
- Enviar reportes automáticos por correo
- Configurar alertas de diferencias de inventario
- Gestión de usuarios con 3 roles: Administrador, Supervisor, Usuario

## Credenciales de Acceso

**Usuario Administrador por defecto:**
- Email: admin@inventario.com
- Contraseña: admin123

## Arquitectura

### Backend (FastAPI + Python)
- **Puerto:** 8001 (interno)
- **URL Externa:** https://stock-tracker-990.preview.emergentagent.com/api
- **Base de Datos Local:** MongoDB (usuarios, configuraciones)
- **Conexiones Externas:** SQL Server (inventarios)

### Frontend (React)
- **Puerto:** 3000 (interno)
- **URL:** https://stock-tracker-990.preview.emergentagent.com

## Consultas SQL Predeterminadas

El sistema viene con consultas SQL precargadas para **ManagementPro (MPRO)**:

### 1. Ventas
Obtiene el consumo de productos por ventas realizadas.

**Parámetros:**
- `@sucursal`: Nombre de la sucursal
- `@fecha_ini`: Fecha de inicio (formato: YYYY-MM-DD)
- `@fecha_fin`: Fecha de fin (formato: YYYY-MM-DD)

### 2. Movimientos
Obtiene todos los movimientos de inventario (entradas, salidas, transferencias).

**Parámetros:**
- `@sucursal`: Nombre de la sucursal
- `@almacen`: Nombre del almacén
- `@fecha_ini`: Fecha de inicio
- `@fecha_fin`: Fecha de fin

### 3. Productos
Lista de productos con información de categorías, familias y costos.

**Parámetros:** Ninguno (consulta estática)

### 4. Inventarios Físicos
Obtiene los inventarios físicos capturados.

**Parámetros:**
- `@sucursal`: Nombre de la sucursal
- `@fecha_ini`: Fecha de inicio
- `@fecha_fin`: Fecha de fin

## Cómo Agregar un Nuevo Servidor

### Desde la Interfaz Web:

1. Inicia sesión con usuario Administrador
2. Ve a la sección **Servidores**
3. Haz clic en **Agregar Servidor**
4. Completa la información:
   - **Nombre:** Identificador del servidor (ej: "Servidor Querétaro")
   - **Tipo de Sistema:** MPRO, SoftRestaurant, u Otro
   - **Host/IP:** Dirección del servidor (ej: 54.39.104.176)
   - **Puerto:** Puerto SQL Server (generalmente 1433)
   - **Base de Datos:** Nombre de la BD (ej: CENTRAL2020)
   - **Usuario:** Usuario de SQL Server
   - **Contraseña:** Contraseña de SQL Server
5. El sistema probará la conexión antes de guardar

## Cómo Agregar Consultas SQL para Otros Sistemas

### Opción 1: Desde MongoDB (Recomendado para Administradores)

Puedes agregar consultas directamente en la base de datos MongoDB:

```javascript
// Conectar a MongoDB
use test_database

// Insertar nueva consulta
db.queries.insertOne({
  "id": "nuevo-uuid-aqui",
  "name": "SoftRestaurant - Ventas",
  "system_type": "SoftRestaurant",
  "query_type": "ventas",
  "sql_query": "SELECT * FROM Ventas WHERE ...",
  "description": "Consulta de ventas para SoftRestaurant",
  "created_at": new Date().toISOString()
})
```

### Opción 2: Usando la API

```bash
curl -X POST "https://stock-tracker-990.preview.emergentagent.com/api/queries" \\
  -H "Authorization: Bearer TU_TOKEN_AQUI" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "SoftRestaurant - Ventas",
    "system_type": "SoftRestaurant",
    "query_type": "ventas",
    "sql_query": "SELECT ...",
    "description": "Consulta personalizada"
  }'
```

### Parámetros en Consultas SQL

En las consultas SQL, usa el formato `@nombre_parametro` para los parámetros que el usuario puede configurar:

```sql
SELECT * FROM Productos 
WHERE Sucursal = '@sucursal' 
AND Fecha BETWEEN '@fecha_ini' AND '@fecha_fin'
```

El sistema reemplazará automáticamente estos parámetros con los valores proporcionados por el usuario.

## Tipos de Consultas Soportadas

El sistema reconoce 4 tipos de consultas:

1. **ventas** - Consumo por ventas
2. **movimientos** - Movimientos de inventario
3. **productos** - Catálogo de productos
4. **inventarios** - Inventarios físicos

## Fórmula de Cálculo de Inventario

El sistema calcula las diferencias de inventario usando:

```
Inventario Inicial + Movimientos - Ventas = Inventario Teórico
Inventario Teórico - Inventario Final = Diferencias
```

## Configuración de Alertas

Las alertas permiten notificar por correo cuando las diferencias de inventario superen un umbral:

1. Ve a **Alertas**
2. Crea una nueva alerta
3. Define:
   - Umbral de diferencia (%)
   - Productos específicos (opcional)
   - Categoría/Familia (opcional)
   - Correos para notificar

## Configuración de SendGrid (Correos)

Para habilitar el envío de reportes por correo:

1. Edita `/app/backend/.env`
2. Agrega tus credenciales de SendGrid:
```
SENDGRID_API_KEY=tu-api-key-aqui
SENDER_EMAIL=noreply@tuempresa.com
```
3. Reinicia el backend: `sudo supervisorctl restart backend`

## Estructura de Base de Datos MongoDB

### Colecciones:

- **users** - Usuarios del sistema
- **servers** - Servidores SQL configurados
- **queries** - Plantillas de consultas SQL
- **alerts** - Alertas configuradas

## Exportación de Reportes

### Excel
- Formato: .xlsx
- Incluye todos los registros
- Mantiene tipos de datos

### PDF
- Formato: Landscape
- Tabla con todos los datos
- Ideal para impresión

## Roles y Permisos

### Administrador
- Acceso total al sistema
- Gestión de servidores
- Gestión de usuarios
- Gestión de consultas SQL
- Configuración de alertas
- Generación de reportes

### Supervisor
- Visualización de dashboards
- Generación de reportes
- Configuración de alertas
- Sin acceso a gestión de servidores/usuarios

### Usuario
- Visualización de dashboards
- Generación de reportes básicos
- Sin acceso a configuraciones

## Soporte Técnico

Para agregar nuevas funcionalidades o sistemas:

1. Analiza la estructura de la base de datos del nuevo sistema
2. Crea las consultas SQL correspondientes
3. Agrégalas al sistema usando MongoDB o la API
4. Prueba las consultas desde la sección de Reportes

## Próximos Pasos Sugeridos

1. **Agregar consultas para SoftRestaurant**
2. **Configurar SendGrid para envío de correos**
3. **Crear usuarios adicionales con roles específicos**
4. **Configurar alertas para productos críticos**
5. **Conectar servidores SQL reales**

## Notas Importantes

- Las contraseñas de SQL Server se almacenan en texto plano en MongoDB (considerar cifrado para producción)
- El sistema soporta múltiples tipos de sistemas SQL Server
- Las consultas SQL deben ser compatibles con SQL Server (T-SQL)
- Los parámetros en las consultas deben seguir el formato `@nombre_parametro`

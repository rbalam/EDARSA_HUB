# EDARSA HUB - ESPEJO DE BASE DE DATOS

> **REGLA DE NEGOCIO**: Todo el conocimiento y cerebro del sistema está 100% centralizado en EDARSA HUB.  
> **Fuente de Verdad**: `/app/backend/core/cerebro.py`  
> **Última Actualización**: Abril 2026

---

## 1. Resumen del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        EDARSA HUB                                │
│                   (CEREBRO CENTRAL)                              │
├─────────────────────────────────────────────────────────────────┤
│  MongoDB Local (18 colecciones)                                  │
│  ├── Autenticación (users, roles)                               │
│  ├── Configuración (servers, server_status)                     │
│  ├── Caché (kpis_cache, inventario_*)                           │
│  ├── Nómina (nomina_ciclos, nomina_movimientos, ...)            │
│  ├── Workflows (tareas_sistema, solicitudes_catalogos)          │
│  └── Auditoría (scripts_pendientes, script_logs, informes_*)    │
├─────────────────────────────────────────────────────────────────┤
│  SQL Server Externos (8 servidores)                              │
│  ├── MPRO Cloud (<REDACTED_EDARSAHUB_SQL_HOST>)                                 │
│  ├── APIs Locales (QRO, Origen) - Tiempo real                   │
│  └── SoftRestaurant (CIENFUEGOS, ESTELAR, MERIDA)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Colecciones MongoDB - Estructura Completa

### 2.1 AUTENTICACIÓN

#### `users` (10 documentos)
```javascript
{
  id: "uuid",              // Identificador único
  email: "string",         // Email único (índice)
  name: "string",          // Nombre completo
  password: "string",      // Hash bcrypt
  role: "string",          // "Administrador" | "Supervisor" | "Usuario"
  sucursales: ["string"],  // IDs de sucursales asignadas
  allowed_servers: ["uuid"], // Servidores permitidos
  active: true,            // Activo/Inactivo
  created_at: "ISO8601"    // Fecha de creación
}
```

#### `roles` (3 documentos)
```javascript
{
  id: "uuid",
  nombre: "string",        // "Administrador" | "Supervisor" | "Usuario"
  descripcion: "string",
  permisos: ["string"],    // IDs de módulos permitidos
  es_sistema: true,        // No editable si es true
  created_at: "ISO8601"
}
```

---

### 2.2 SERVIDORES

#### `servers` (10 documentos)
```javascript
{
  id: "uuid",
  name: "string",          // "ManagmentPro", "CIENFUEGOS"
  host: "string",          // "<REDACTED_EDARSAHUB_SQL_HOST>" o "servercienfuegos.ddns.net,6669\\nationalsoft"
  port: 1433,              // Puerto SQL
  database: "string",      // Nombre de BD
  username: "string",
  password: "string",      // ⚠️ Almacenado en claro
  system_type: "string",   // "MPRO" | "SoftRestaurant" | "Otro"
  sucursales: [{           // Array de sucursales del servidor
    id: "string",
    nombre: "string"
  }],
  active: true,
  visible_en_operaciones: true,  // Visible en Tablero Ejecutivo
  created_at: "ISO8601",
  // Configuraciones de queries
  queries_configured: true,
  query_inventario: { sql: "...", validated: true, ... },
  query_ventas: { sql: "...", validated: true, ... },
  query_movimientos: { sql: "...", validated: true, ... },
  // Catálogos
  categorias: ["ABARROTES", "CARNES", ...],
  departamentos: ["COCINA", "BAR", ...],
  tipos_movimiento: ["ENTRADA", "SALIDA", ...]
}
```

#### `server_status` (8 documentos)
```javascript
{
  server_id: "uuid",
  is_online: true,
  last_check: "ISO8601",
  response_time_ms: 150
}
```

---

### 2.3 KPIs Y CACHÉ

#### `kpis_cache` (46 documentos)
```javascript
{
  server_id: "uuid",
  periodo_key: "2026-04",  // Año-Mes
  kpis: {
    ventas: 1500000.00,
    ventas_ant: 1400000.00,
    ventas_año: 1300000.00,
    var_vs_mes_ant: 7.1,
    var_vs_año_ant: 15.4,
    proyeccion: 5000000.00,
    pax: 4500,
    pax_ant: 4200,
    pax_año: 4000,
    cheques: 1200,
    cheques_ant: 1100,
    cheques_año: 1000,
    ticket_prom: 333.33,
    cheque_prom: 1250.00,
    es_ventas_dia: false,
    unidad: "130° QUERETARO",
    server_id: "uuid",
    system_type: "MPRO",
    status: "online",
    updated_at: "ISO8601"
  },
  status: "online",
  updated_at: "ISO8601"
}
```

---

### 2.4 NÓMINA

#### `nomina_ciclos` (2 documentos)
```javascript
{
  id: "uuid",
  sucursal_id: "uuid",
  sucursal_nombre: "string",
  fecha_corte: "2026-04-15",
  tipo_nomina: "quincenal",  // "quincenal" | "semanal" | "mensual"
  notas: "string",
  etapa_actual: "headcount", // "headcount" | "maquilador" | "tesoreria" | "autorizacion" | "pagado"
  deadline_actual: "ISO8601",
  total_colaboradores: 50,
  total_movimientos: 120,
  fecha_creacion: "ISO8601",
  creado_por_id: "uuid",
  creado_por_email: "string",
  historial: [{
    etapa: "string",
    accion: "string",
    usuario_id: "uuid",
    usuario_email: "string",
    fecha: "ISO8601",
    notas: "string"
  }],
  fecha_ultima_actualizacion: "ISO8601"
}
```

#### `nomina_movimientos` (3 documentos)
```javascript
{
  id: "uuid",
  ciclo_id: "uuid",
  colaborador_id: "string",
  colaborador_nombre: "string",
  tipo_incidencia: "BONO",
  categoria: "percepcion",  // "percepcion" | "deduccion" | "informativa"
  monto: 1500.00,
  unidades: 1,
  notas: "Bono por productividad",
  fecha_registro: "ISO8601",
  registrado_por_id: "uuid",
  registrado_por: "admin@inventario.com"
}
```

#### `nomina_configuracion` (1 documento)
```javascript
{
  tipo: "nomina",
  dia_corte: 15,
  dia_pago: 20,
  dias_inhabiles: ["2026-12-25", "2026-01-01"],
  horario_headcount: "09:00",
  horario_maquilador: "12:00",
  horario_tesoreria: "15:00",
  horario_autorizacion: "17:00",
  actualizado_por: "admin@inventario.com",
  fecha_actualizacion: "ISO8601"
}
```

#### `nomina_kpis_puestos` (1 documento)
```javascript
{
  id: "uuid",
  puesto_id: "string",
  puesto_nombre: "Gerente",
  indicadores: [{
    nombre: "Ventas",
    descripcion: "Meta de ventas mensual",
    meta: 500000,
    peso: 40
  }],
  actualizado_por: "admin@inventario.com",
  fecha_actualizacion: "ISO8601"
}
```

---

### 2.5 INVENTARIOS

#### `inventario_diferencias_detalle` (11 documentos)
```javascript
{
  server_id: "uuid",
  sucursal_id: "string",
  almacen_id: "string",
  folio: "INV-2026-001",
  fecha_inventario: "2026-04-10",
  fecha_cache: "ISO8601",
  comentario: "string",
  productos: [{
    codigo: "PROD001",
    nombre: "Producto X",
    existencia_teorica: 100,
    existencia_fisica: 95,
    diferencia: -5,
    costo_unitario: 50.00,
    importe_diferencia: -250.00
  }]
}
```

#### `inventario_diferencias_cache` (1 documento)
```javascript
{
  server_id: "uuid",
  sucursal_id: "string",
  sucursal_nombre: "string",
  almacen_id: "string",
  almacen_nombre: "string",
  folio_mas_reciente: "INV-2026-001",
  fecha_cache: "ISO8601",
  comentario: "string",
  cortes: [{
    folio: "string",
    fecha: "string",
    total_productos: 100
  }],
  productos: [...]
}
```

#### `informes_auditoria` (3 documentos)
```javascript
{
  id: "uuid",
  fecha_creacion: "ISO8601",
  fecha_actualizacion: "ISO8601",
  estatus: "pendiente",  // "pendiente" | "en_proceso" | "completado"
  sucursal_id: "string",
  sucursal_nombre: "string",
  almacen_id: "string",
  almacen_nombre: "string",
  servidor_id: "uuid",
  servidor_nombre: "string",
  inventario_inicial_id: "string",
  inventario_inicial_fecha: "string",
  inventario_final_id: "string",
  inventario_final_fecha: "string",
  total_productos: 100,
  productos_con_diferencia: 15,
  valor_total_diferencias: -5000.00,
  porcentaje_precision: 85.0,
  comentarios: "string",
  conclusiones: "string",
  recomendaciones: "string",
  incluir_comparativo_4_cortes: true,
  datos_comparativo: {...},
  productos_diferencias: {...},
  auditor: "string",
  cargo_auditor: "string",
  usuario_id: "uuid",
  evidencias: [{
    tipo: "imagen",
    url: "https://...",
    descripcion: "string",
    fecha: "ISO8601"
  }]
}
```

---

### 2.6 PORTAL PROVEEDORES

#### `portal_suppliers` (3 documentos)
```javascript
{
  id: "uuid",
  rfc: "XAXX010101000",
  razon_social: "Proveedor SA de CV",
  nombre_contacto: "Juan Pérez",
  email: "contacto@proveedor.com",
  telefono: "5512345678",
  password: "$2b$...",  // Hash bcrypt
  banco: "BBVA",
  clabe: "012345678901234567",
  cuenta: "1234567890",
  status: "aprobado",  // "pendiente" | "aprobado" | "rechazado" | "suspendido"
  sucursales_asignadas: ["uuid1", "uuid2"],
  created_at: "ISO8601",
  approved_at: "ISO8601",
  approved_by: "admin@inventario.com",
  approval_notes: "Documentación completa"
}
```

---

### 2.7 CATÁLOGOS Y SOLICITUDES

#### `solicitudes_catalogos` (10 documentos)
```javascript
{
  id: "uuid",
  catalogo_id: "puestos",
  catalogo_nombre: "Puestos",
  modulo: "rh",
  datos: {
    descripcion: "Nuevo puesto de trabajo",
    departamento: "Cocina",
    sueldo_base: 15000
  },
  notas: "string",
  estatus: "pendiente",  // "pendiente" | "aprobado" | "rechazado"
  solicitante_id: "uuid",
  solicitante_email: "user@inventario.com",
  solicitante_nombre: "string",
  fecha_solicitud: "ISO8601",
  aprobador_id: "uuid",
  aprobador_email: "admin@inventario.com",
  fecha_aprobacion: "ISO8601",
  motivo_rechazo: null
}
```

#### `permisos_catalogos` (1 documento)
```javascript
{
  user_id: "uuid",
  catalogos_permitidos: ["puestos", "departamentos"],
  puede_solicitar: true,
  asignado_por: "admin@inventario.com",
  fecha_asignacion: "ISO8601"
}
```

#### `config_catalogos` (1 documento)
```javascript
{
  tipo: "catalogos",
  niveles: {
    puestos: 2,        // Niveles de aprobación
    departamentos: 1
  }
}
```

---

### 2.8 TAREAS DEL SISTEMA

#### `tareas_sistema` (20 documentos)
```javascript
{
  id: "uuid",
  tipo: "aprobacion_catalogo",  // "aprobacion_catalogo" | "revision" | "captura" | "auditoria"
  titulo: "Aprobar nuevo puesto",
  descripcion: "string",
  solicitud_id: "uuid",
  estatus: "pendiente",  // "pendiente" | "en_proceso" | "completado"
  prioridad: "media",    // "baja" | "media" | "alta" | "urgente"
  asignado_a_roles: ["Administrador", "Supervisor"],
  creado_por: "uuid",
  fecha_creacion: "ISO8601",
  fecha_limite: "ISO8601",
  completado_por: "uuid",
  fecha_completado: "ISO8601"
}
```

---

### 2.9 SCRIPTS SQL

#### `scripts_pendientes` (58 documentos)
```javascript
{
  server_id: "uuid",
  server_name: "ManagmentPro",
  titulo: "Actualizar precios Q2",
  script: "UPDATE productos SET precio = precio * 1.05...",
  num_statements: 3,
  creado_por: "admin@inventario.com",
  fecha_creacion: "ISO8601",
  estado: "pendiente",  // "pendiente" | "en_revision" | "aprobado" | "rechazado" | "ejecutado"
  fecha_modificacion: "ISO8601",
  modificado_por: "string",
  ejecutado_por: "string",
  fecha_ejecucion: "ISO8601",
  resultado: {
    exitosos: 2,
    fallidos: 1
  }
}
```

#### `script_logs` (19 documentos)
```javascript
{
  server_id: "uuid",
  server_name: "string",
  titulo: "string",
  usuario: "admin@inventario.com",
  fecha: "ISO8601",
  total_statements: 3,
  exitosos: 2,
  fallidos: 1,
  resultados: [{
    statement: "UPDATE productos...",
    success: true,
    rows_affected: 150,
    error: null
  }]
}
```

---

### 2.10 CONSULTAS CUSTOM

#### `consultas_custom` (3 documentos)
```javascript
{
  id: "uuid",
  original_id: "uuid",  // Si es copia
  nombre: "Ventas por hora",
  descripcion: "Desglose de ventas por hora del día",
  sistema: "MPRO",
  categoria: "Ventas",
  parametros: ["fecha_inicio", "fecha_fin", "sucursal"],
  sql: "SELECT DATEPART(hour, co_fecha) as hora...",
  created_by: "admin@inventario.com",
  created_at: "ISO8601",
  active: true
}
```

#### `queries` (4 documentos)
```javascript
{
  id: "uuid",
  name: "Ventas del día",
  system_type: "SoftRestaurant",
  query_type: "ventas",
  sql_query: "SELECT ... FROM cheques...",
  description: "Ventas del día actual",
  created_at: "ISO8601"
}
```

---

## 3. Índices Creados

| Colección | Índice | Campos | Tipo |
|-----------|--------|--------|------|
| users | idx_users_email | email | Único |
| servers | idx_servers_active_type | active, system_type | Compuesto |
| server_status | idx_server_status | server_id | Simple |
| kpis_cache | idx_kpis_lookup | server_id, periodo_key | Compuesto |
| scripts_pendientes | idx_scripts_server_estado | server_id, estado | Compuesto |
| tareas_sistema | idx_tareas_estatus | estatus | Simple |
| solicitudes_catalogos | idx_solicitudes_estatus | estatus, solicitante_id | Compuesto |
| roles | idx_roles_nombre | nombre | Simple |

---

## 4. Servidores SQL Externos

| Sistema | Nombre | Host | Puerto | Base de Datos |
|---------|--------|------|--------|---------------|
| MPRO | ManagmentPro | <REDACTED_EDARSAHUB_SQL_HOST> | 1433 | ManagementPro_Edarsa |
| MPRO | MPRO TABLAJERIA | <REDACTED_EDARSAHUB_SQL_HOST> | 1433 | ManagementPro_Tablajeria |
| MPRO | HR2020 ESCRITURA | <REDACTED_EDARSAHUB_SQL_HOST> | 1433 | HR2020 |
| SoftRest | CIENFUEGOS | servercienfuegos.ddns.net | 6669 | cienfuegos |
| SoftRest | CIENFUEGOS TABLAJERIA | servercienfuegos.ddns.net | 6669 | tablajeria |
| SoftRest | LA ESTELAR | serverestelar.ddns.net | 6969 | estelar |
| SoftRest | 130° MERIDA | 130mid.ddns.net | 1433 | merida |
| Otro | EDARSA HUB | <REDACTED_EDARSAHUB_SQL_HOST> | 1433 | EdarsaHub |

---

## 5. APIs Locales MPRO

| API | URL | Sucursal Destino | Hora Réplica |
|-----|-----|------------------|--------------|
| 130° QRO LOCAL | http://<REDACTED_EDARSAHUB_SQL_HOST>:8001/query | QUERETARO | 4:00 AM |
| ORIGEN LOCAL | http://<REDACTED_EDARSAHUB_SQL_HOST>:8000/query | ORIGEN | 4:00 AM |

---

## 6. Código de Referencia

### Ubicación del Cerebro
```python
from core.cerebro import (
    # Enums
    SystemType, RoleName, EstatusGeneral,
    # Modelos
    UserInDB, Server, KPIsCache, NominaCiclo,
    # Constantes
    MODULOS_DISPONIBLES, MONGODB_COLLECTIONS, MONGODB_INDEXES,
    # Validaciones
    validar_rfc, validar_clabe
)
```

### Crear Índices Programáticamente
```python
from core.cerebro import MONGODB_INDEXES

async def ensure_indexes(db):
    for collection, indexes in MONGODB_INDEXES.items():
        for index in indexes:
            await db[collection].create_index(
                list(index['keys'].items()),
                **index['options']
            )
```

---

## 7. Reglas de Negocio Críticas

1. **Zona Horaria**: Todas las operaciones usan `America/Mexico_City` (UTC-6)
2. **Hora de Réplica**: Los datos de APIs locales se replican a las 4:00 AM
3. **Cooldown Servidores**: 5 minutos de espera después de error de conexión
4. **Caché KPIs**: TTL de 15 minutos para datos del Tablero Ejecutivo
5. **JWT**: Expira en 24 horas, algoritmo HS256
6. **Passwords**: Hash bcrypt con salt automático

---

> **IMPORTANTE**: Este documento y `/app/backend/core/cerebro.py` son la ÚNICA FUENTE DE VERDAD.  
> Cualquier cambio en la estructura de datos DEBE reflejarse aquí.

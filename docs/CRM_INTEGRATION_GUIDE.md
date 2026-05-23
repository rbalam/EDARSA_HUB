# EDARSA HUB - CRM Integration Guide

## Arquitectura de Integración

```
┌─────────────────┐     ┌───────────────────┐     ┌─────────────────────┐
│   CRM Externo   │────▶│  Tablas Staging   │────▶│  Tablas Producción  │
│  (VTiger, etc.) │     │  (Buffer/Limpieza)│     │  (CRM_Leads, etc.)  │
└─────────────────┘     └───────────────────┘     └─────────────────────┘
        │                        │                         │
        │ PULL                   │ PROCESS                 │
        ▼                        ▼                         ▼
   VTigerConnector         StagingProcessor          Datos Limpios
   (pull_leads, etc.)     (deduplicación)           (listos para uso)
```

## Componentes Principales

### 1. Conectores (`/app/backend/modules/crm/integration/`)

| Archivo | Descripción |
|---------|-------------|
| `base_connector.py` | Clase abstracta base para todos los conectores |
| `vtiger_connector.py` | Implementación específica para VTiger CRM |
| `staging_service.py` | CRUD para tablas de staging |
| `sync_engine.py` | Motor de sincronización (orquestador) |
| `staging_processor.py` | Procesa staging → producción con deduplicación |

### 2. Tablas de Staging (SQL Server)

| Tabla | Propósito |
|-------|-----------|
| `CRM_Staging_Leads` | Buffer para leads importados |
| `CRM_Staging_Oportunidades` | Buffer para oportunidades |
| `CRM_Staging_Cuentas` | Buffer para cuentas/clientes |
| `CRM_Integracion_Conectores` | Configuración de conectores |
| `CRM_Integracion_SyncLog` | Historial de sincronizaciones |

### 3. Estados de Sincronización

| Estado | Descripción |
|--------|-------------|
| `PENDIENTE` | Registro recién importado, esperando procesamiento |
| `EN_PROCESO` | Actualmente siendo procesado |
| `SINCRONIZADO` | Exitosamente movido a producción |
| `ERROR` | Error durante el procesamiento |
| `CONFLICTO` | Duplicado detectado, requiere resolución manual |

---

## API REST de Integración

Base URL: `/api/crm/integration`

### Conectores

```bash
# Listar conectores
GET /conectores?empresa_id={uuid}&activo=true

# Obtener conector
GET /conectores/{conector_id}

# Crear conector
POST /conectores
{
  "empresa_id": "uuid",
  "codigo": "VTIGER",
  "nombre": "VTiger CRM",
  "tipo_conector": "VTIGER",
  "configuracion": {
    "base_url": "https://vtiger.example.com",
    "username": "admin",
    "access_key": "secret_key"
  }
}

# Actualizar conector
PUT /conectores/{conector_id}
{
  "nombre": "Nuevo nombre",
  "configuracion": { ... }
}

# Eliminar (desactivar)
DELETE /conectores/{conector_id}
```

### Test de Conexión

```bash
# Probar conexión sin guardar
POST /test-connection
{
  "tipo": "VTIGER",
  "base_url": "https://vtiger.example.com",
  "username": "admin",
  "access_key": "secret_key"
}

# Probar conector guardado
POST /conectores/{conector_id}/test
```

### Sincronización

```bash
# Extraer datos del CRM externo → Staging
POST /conectores/{conector_id}/sync
{
  "entidades": ["leads", "oportunidades", "cuentas"],
  "desde_fecha": "2026-01-01T00:00:00"  // opcional
}

# Procesar staging → Producción
POST /conectores/{conector_id}/process-staging
{
  "entidades": ["leads", "cuentas"],
  "accion_duplicados": "MARCAR_CONFLICTO",  // CREAR_NUEVO, ACTUALIZAR_EXISTENTE, OMITIR
  "limit": 100
}
```

### Staging

```bash
# Estadísticas de staging
GET /conectores/{conector_id}/staging/stats

# Listar registros en staging
GET /conectores/{conector_id}/staging/leads?estado=PENDIENTE&limit=50
GET /conectores/{conector_id}/staging/oportunidades
GET /conectores/{conector_id}/staging/cuentas
```

### Conflictos

```bash
# Listar conflictos
GET /conectores/{conector_id}/conflictos?entidad=leads

# Resolver conflicto individual
POST /conectores/{conector_id}/conflictos/{staging_id}/resolver?entidad=leads
{
  "accion": "CREAR_NUEVO"  // ACTUALIZAR_EXISTENTE, OMITIR
}

# Resolver todos los conflictos
POST /conectores/{conector_id}/conflictos/resolver-todos?entidad=leads
{
  "accion": "OMITIR"
}
```

### Historial

```bash
# Ver historial de sincronizaciones
GET /conectores/{conector_id}/sync-log?limit=20
```

---

## Flujo de Trabajo Típico

### 1. Configurar Conector

```bash
# Crear conector VTiger
curl -X POST http://localhost:8001/api/crm/integration/conectores \
  -H "Content-Type: application/json" \
  -d '{
    "empresa_id": "00000000-0000-0000-0000-000000000001",
    "codigo": "VTIGER",
    "nombre": "VTiger Principal",
    "tipo_conector": "VTIGER",
    "configuracion": {
      "base_url": "https://saligula.hostw3b.com",
      "username": "admin",
      "access_key": "v7Wex2c3Mf9jVlJB"
    }
  }'
```

### 2. Probar Conexión

```bash
curl -X POST http://localhost:8001/api/crm/integration/conectores/1/test
# Respuesta: {"success": true, "mensaje": "Conexión exitosa"}
```

### 3. Sincronizar desde CRM Externo

```bash
# Extraer leads y cuentas de VTiger → Staging
curl -X POST http://localhost:8001/api/crm/integration/conectores/1/sync \
  -H "Content-Type: application/json" \
  -d '{"entidades": ["leads", "cuentas"]}'

# Respuesta: {"success": true, "procesados": 4, "creados": 4, ...}
```

### 4. Verificar Staging

```bash
curl http://localhost:8001/api/crm/integration/conectores/1/staging/stats
# Respuesta: {"stats": {"leads": {"PENDIENTE": 2}, "cuentas": {"PENDIENTE": 2}}}
```

### 5. Procesar a Producción

```bash
curl -X POST http://localhost:8001/api/crm/integration/conectores/1/process-staging \
  -H "Content-Type: application/json" \
  -d '{
    "entidades": ["leads", "cuentas"],
    "accion_duplicados": "MARCAR_CONFLICTO"
  }'

# Respuesta: {"success": true, "creados": 3, "conflictos": 1, ...}
```

### 6. Resolver Conflictos (si hay)

```bash
# Ver conflictos
curl http://localhost:8001/api/crm/integration/conectores/1/conflictos?entidad=leads

# Resolver individualmente
curl -X POST "http://localhost:8001/api/crm/integration/conectores/1/conflictos/5/resolver?entidad=leads" \
  -H "Content-Type: application/json" \
  -d '{"accion": "ACTUALIZAR_EXISTENTE"}'
```

---

## Lógica de Deduplicación

### Leads
1. **Email exacto** (95% confianza)
2. **Teléfono exacto** (80% confianza)
3. **Nombre de empresa** (60% confianza)

### Cuentas
1. **RFC exacto** (98% confianza)
2. **Razón social exacta** (85% confianza)

### Acciones ante Duplicados

| Acción | Comportamiento |
|--------|----------------|
| `CREAR_NUEVO` | Crea registro aunque exista duplicado |
| `ACTUALIZAR_EXISTENTE` | Actualiza el registro existente con datos nuevos |
| `MARCAR_CONFLICTO` | Marca para revisión manual |
| `OMITIR` | Descarta el registro de staging |

---

## Agregar Nuevos Conectores

Para agregar soporte a otro CRM (ej: Salesforce):

1. Crear `salesforce_connector.py` heredando de `BaseCRMConnector`
2. Implementar métodos abstractos:
   - `test_connection()`
   - `connect()`
   - `pull_leads()`, `push_lead()`, `update_lead()`
   - `pull_opportunities()`, `push_opportunity()`, `update_opportunity()`
   - `pull_accounts()`, `push_account()`
3. Registrar en `sync_engine.py`:
   ```python
   if tipo == 'SALESFORCE':
       return SalesforceConnector(conector_id, config)
   ```
4. Actualizar `__init__.py` con el export

---

## Notas de Implementación

- **Zona Horaria**: Todas las fechas usan `America/Mexico_City`
- **UUIDs**: Los IDs locales (`LeadID`, `OportunidadID`) son `uniqueidentifier`
- **Batch Processing**: El límite por defecto es 100 registros por ejecución
- **Reintentos**: Cada registro tiene contador `Intentos` para control de errores
- **Logging**: Todos los eventos se registran en `CRM_Integracion_SyncLog`
